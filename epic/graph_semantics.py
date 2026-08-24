from .graph_syntax_utils import *

import collections

class FancyQueue:
    # nodes have a priority order and a "masked" state
    is_masked_callback : Callable[[OperationIdent], bool]
    insertion_pos : Union[Literal["here"], Literal["end"]]
    order : List[OperationIdent]
    masked : MutableSet[OperationIdent]
    biggest_mask : int = -1

    def __init__(self,
        is_masked_callback : Callable[[OperationIdent], bool],
        insertion_pos : Union[Literal["here"], Literal["end"]],
    ):
        self.is_masked_callback = is_masked_callback
        self.insertion_pos = insertion_pos
        self.order = [-1]
        self.masked = set()

    def replace(self, old : OperationIdent, news : IList[OperationIdent]):
        assert old not in self.masked

        i = self.order.index(old)
        if self.insertion_pos == "here":
            self.order = self.order[:i] + list(news) + self.order[(i+1):]
        else:
            self.order = self.order[:i] + self.order[(i+1):] + list(news)
        
        for n in news:
            if self.is_masked_callback(n):
                self.masked.add(n)
    
    def next_unmasked(self) -> Optional[OperationIdent]:
        i = 0
        out = None
        for ident in self.order:
            i += 1
            if ident not in self.masked:
                out = ident
                break
        if i > self.biggest_mask:
            self.biggest_mask = i
        return out

    def refresh_mask(self, ident : OperationIdent):
        if ident in self.masked:
            if not self.is_masked_callback(ident):
                self.masked.remove(ident)

class GraphQueue:
    # nodes have a priority order and a "masked" state
    is_masked_callback : Callable[[OperationIdent], bool]
    queue : typing.Deque[OperationIdent]
    masked : MutableSet[OperationIdent]
    biggest_mask : int = -1

    def __init__(self,
        is_masked_callback : Callable[[OperationIdent], bool],
    ):
        self.is_masked_callback = is_masked_callback
        self.queue = collections.deque((-1,))
        self.masked = set()

    def replace(self, old : OperationIdent, news : IList[OperationIdent]):
        old2 = self.queue.popleft()
        assert old == old2, (old, old2)

        for n in news:
            if self.is_masked_callback(n):
                self.masked.add(n)
            else:
                self.queue.append(n)
    
    def next_unmasked(self) -> Optional[OperationIdent]:
        if self.queue:
            return self.queue[0]
        else:
            return None

    def refresh_mask(self, ident : OperationIdent):
        if ident in self.masked:
            if not self.is_masked_callback(ident):
                self.masked.remove(ident)
                self.queue.append(ident)

TreePolicy = Union[Literal["bfs"], Literal["dfs"]]
@dataclass
class GraphSemanticsState:
    g : TermGraph
    fq : Union[FancyQueue, GraphQueue]
    running_tasks : MutableSet[Task]
    tree_policy : TreePolicy
    blocking_async : bool

StepOutput = Tuple[IList[OperationIdent], FrozenSet[OperationIdent]]

REDUCTION_STUCK_EVENT = asyncio.Event()

async def reduce_term_async(e : Function, tree_policy : TreePolicy, blocking_async : bool) -> TermGraph:
    REDUCTION_STUCK_EVENT.clear()
    g, init_ops = graph_from_initial_term(e)
    # trace_printing.print_func(e)
    # e_print = graph_to_term(g)
    # trace_printing.print_func(e_print)
    # sp_graph(g)
    if tree_policy == "dfs":
        fq = FancyQueue(lambda ident: not graph_steppable_op(g, ident), "here")
    else:
        fq = GraphQueue(lambda ident: not graph_steppable_op(g, ident))
    fq.replace(-1, init_ops)
    
    s = GraphSemanticsState(g, fq, set(), tree_policy, blocking_async)

    while True:
        print(f">> semantics iteration ({len(s.running_tasks)} tasks)")
        # print(*((ident, ident in fq.masked) for ident in fq.order))
        # print(fq.queue)
        # print(fq.masked)
        ident = fq.next_unmasked()
        if ident is not None:
            # print(ident, g.ops[ident])
            # trace_printing.print_func(graph_to_term(g))
            new_ops, toucheds = await graph_step(s, ident)
            fq.replace(ident, new_ops)
            for touched in toucheds:
                fq.refresh_mask(touched)

            await asyncio.sleep(0)
        else:
            REDUCTION_STUCK_EVENT.set()
            REDUCTION_STUCK_EVENT.clear()
            if len(s.running_tasks) != 0:
                print(f">> sleeping...")
                await asyncio.wait(s.running_tasks, return_when = asyncio.FIRST_COMPLETED)
            else:
                break
    
    assert not s.running_tasks
    # print("BIGGEST MASK", fq.biggest_mask)
    return g

def reduce_term(e : Function, tree_policy : TreePolicy, blocking_async : bool) -> TermGraph:
    return asyncio.get_event_loop().run_until_complete(reduce_term_async(e, tree_policy, blocking_async))

def reduce_graph_sequential(f : Function) -> Iterable[Function]:
    g = reduce_term(f, "dfs", True)
    yield graph_to_term(g)

def reduce_graph_opportunistic(f : Function) -> Iterable[Function]:
    g = reduce_term(f, "bfs", False)
    yield graph_to_term(g)

def reduce_graph_opportunistic_dfs(f : Function) -> Iterable[Function]:
    g = reduce_term(f, "dfs", False)
    yield graph_to_term(g)

def graph_steppable_op(g : TermGraph, ident : OperationIdent) -> bool:
    match g.ops[ident]:
        case "parameters",: pass
        case "return",: pass
        case "def", _func:
            _func, f, _closure = g.get_op_as_def(ident)
            if len(g.use_var_to_pos[f]) == 0:
                return True
        case "call", _call_name:
            if g.get_call_def(ident) is not None:
                return True
            elif g.get_call_prims(ident) is not None:
                return True
        case "pack",:
            outp, _inps = g.get_op_as_pack(ident)
            if len(g.use_var_to_pos[outp]) == 0:
                return True
        case "unpack",:
            if g.get_unpack_pack(ident) is not None:
                return True
        case "prim", _pyobj:
            outp, _pyobj = g.get_op_as_prim(ident)
            if len(g.use_var_to_pos[outp]) == 0:
                return True
        case "task", _call_name, pyfuture:
            if pyfuture.done():
                return True
    return False

async def graph_step(s : GraphSemanticsState, ident : OperationIdent) -> StepOutput:
    match s.g.ops[ident]:
        case "parameters",:
            assert False
        case "return",:
            assert False
        case "def", _func:
            return graph_step_gc(s, ident)
        case "call", _call_name:
            return await graph_step_call(s, ident)
        case "pack",:
            return graph_step_gc(s, ident)
        case "unpack",:
            return graph_step_unpack(s, ident)
        case "prim", _pyobj:
            return graph_step_gc(s, ident)
        case "task", _call_name, _pyfuture:
            return graph_step_task(s, ident)

async def graph_step_call(s : GraphSemanticsState, call_ident : OperationIdent) -> StepOutput:
    call_name, outps, call_f, inps = s.g.get_op_as_call(call_ident)

    def_ident = s.g.get_call_def(call_ident)
    if def_ident is not None:
        return graph_step_call_normal(s, call_ident, call_f, inps, def_ident)
    
    prim_idents = s.g.get_call_prims(call_ident)
    if prim_idents is not None:
        return await graph_step_call_prim(s, call_name, outps, call_ident, call_f, inps, prim_idents[0], prim_idents[1])
    assert False

def graph_step_call_normal(s : GraphSemanticsState, call_ident : OperationIdent, call_f : VarIdent, inps : IList[VarIdent], def_ident : OperationIdent) -> StepOutput:
    func, f2, closure = s.g.get_op_as_def(def_ident)
    assert call_f == f2 #, (ppv(call_f), ppv(f2))

    vm : VarMapping = closure
    vm.update(zip(func[0], inps)) # add arguments to mapping
    
    return graph_step_body(s, call_ident, vm, func[1])


async def graph_step_call_prim(s : GraphSemanticsState, call_name : str, outps : IList[VarIdent], call_ident : OperationIdent, call_f : VarIdent, inps : IList[VarIdent], f_ident : OperationIdent, arg_idents : IList[OperationIdent]) -> StepOutput:
    f2, f_obj = s.g.get_op_as_prim(f_ident)
    assert call_f == f2 #, (ppv(call_f), ppv(f2))

    inp_objs : List[Object] = []
    for i, arg_ident in enumerate(arg_idents):
        inp2, inp_obj = s.g.get_op_as_prim(arg_ident)
        assert inps[i] == inp2
        inp_objs.append(inp_obj)

    prim_res : Union[Body, Coroutine[Body, typing.Any, typing.Any]] = cast(f_obj)(*inp_objs)
    if asyncio.iscoroutine(prim_res) and not s.blocking_async:
        task = asyncio.create_task(prim_res)

        new_outps = tuple(var(s.g.get_var_name(outp)) for outp in outps)
        body : Body = ((
            ("task", call_name, new_outps, task),
        ), new_outps)

        vm : VarMapping = {}
        new_idents, touched = graph_step_body(s, call_ident, vm, body)
        task_ident, = new_idents

        s.running_tasks.add(task)
        def done(task2 : Task):
            assert task2 is task
            assert task.done()
            s.running_tasks.remove(task)
            s.fq.refresh_mask(task_ident)
        task.add_done_callback(done)

        return new_idents, touched
    else:
        vm : VarMapping = {}
        if asyncio.iscoroutine(prim_res):
            assert s.blocking_async
            body = await prim_res
        else:
            body = prim_res
        return graph_step_body(s, call_ident, vm, body)


def graph_step_unpack(s : GraphSemanticsState, unpack_ident : OperationIdent) -> StepOutput:
    # def ppv(v : VarIdent):
    #     return f"{g.get_var_name(v)}#{v}"

    _outps, tupl = s.g.get_op_as_unpack(unpack_ident)

    pack_ident = s.g.get_unpack_pack(unpack_ident)
    assert pack_ident is not None

    tupl2, inps = s.g.get_op_as_pack(pack_ident)
    assert tupl == tupl2 #, (ppv(tupl), ppv(tupl2))
    
    def subst(opos : OutPosition) -> Optional[VarIdent]:
        match opos:
            case "unpack", i:
                return inps[i]
            case x:
                assert False, x
    touched_idents = s.g.replace_op_with_vars(unpack_ident, subst)

    return (), touched_idents

def graph_step_gc(s : GraphSemanticsState, ident : OperationIdent) -> StepOutput:
    def subst(_opos : OutPosition) -> Optional[VarIdent]:
        return None
    touched = s.g.replace_op_with_vars(ident, subst)
    return (), touched


def graph_step_task(s : GraphSemanticsState, call_ident : OperationIdent) -> StepOutput:
    _call_name, _outps, pyfuture = s.g.get_op_as_task(call_ident)

    body = pyfuture.result()

    vm : VarMapping = {}

    return graph_step_body(s, call_ident, vm, body)

def graph_step_body(s : GraphSemanticsState, call_ident : OperationIdent, vm : VarMapping, body : Body) -> StepOutput:
    new_idents : List[OperationIdent] = []
    for stmt in body[0]:
        new_ident = add_statement_to_graph(s.g, vm, stmt)
        new_idents.append(new_ident)
    
    def subst(opos : OutPosition) -> VarIdent:
        match opos:
            case "call", i:
                return vm[body[1][i]]
            case "task", i:
                return vm[body[1][i]]
            case x:
                assert False, x
    touched_idents = s.g.replace_op_with_vars(call_ident, subst)

    return tuple(new_idents), touched_idents