from .env import *
from .syntax import *

VarIdent = int
OperationIdent = int
OpIdSet = FrozenSet[OperationIdent]

OutPosition = Union[
    Tuple[Literal["parameter"], int],
    Tuple[Literal["def"]],
    Tuple[Literal["call"], int],
    Tuple[Literal["pack"]],
    Tuple[Literal["unpack"], int],
    Tuple[Literal["prim"]],
    Tuple[Literal["task"], int],
]

InPosition = Union[
    Tuple[Literal["return"], int],
    Tuple[Literal["def"], Var],
    Tuple[Literal["call"], Optional[int]],
    Tuple[Literal["pack"], int],
    Tuple[Literal["unpack"]],
]

Operation : TypeAlias = Union[
    Tuple[Literal["parameters"]],
    Tuple[Literal["return"]],
    Tuple[Literal["def"], Function],
    Tuple[Literal["call"], str],
    Tuple[Literal["pack"]],
    Tuple[Literal["unpack"]],
    Tuple[Literal["prim"], Object],
    Tuple[Literal["task"], str, Task],
]

@dataclass
class TermGraph:
    # strong invariants (respected by all functions):
    # - bind_var_to_pos and bind_pos_to_var agree
    # - use_var_to_pos and use_pos_to_var agree

    # invariants (respected by all non private functions):
    # - every var has a binding site
    # - every operation has all inputs and outputs

    # intuitions:
    # - there should be exactly one parameter operation
    # - there should be exactly one return operation

    vars : Dict[VarIdent, str]
    var_next_id : int

    ops : Dict[OperationIdent, Operation]
    op_next_id : int

    bind_var_to_pos : Dict[VarIdent, Tuple[OperationIdent, OutPosition]]
    bind_pos_to_var : Dict[OperationIdent, Dict[OutPosition, VarIdent]]
    
    use_var_to_pos : Dict[VarIdent, MutableSet[Tuple[OperationIdent, InPosition]]]
    use_pos_to_var : Dict[OperationIdent, Dict[InPosition, VarIdent]]

    def __init__(self):
        self.vars = {}
        self.var_next_id = 0
        self.ops = {}
        self.op_next_id = 0
        self.bind_var_to_pos = {}
        self.bind_pos_to_var = {}
        self.use_var_to_pos = {}
        self.use_pos_to_var = {}

    def _new_var_ident(self, name : str) -> VarIdent:
        ret = self.var_next_id
        self.var_next_id += 1
        self.vars[ret] = name
        self.use_var_to_pos[ret] = set()
        return ret

    def _new_op_ident(self, op : Operation) -> OperationIdent:
        ret = self.op_next_id
        self.op_next_id += 1
        self.ops[ret] = op
        self.bind_pos_to_var[ret] = {}
        self.use_pos_to_var[ret] = {}
        return ret
    
    def _add_bind(self, v : VarIdent, op_ident : OperationIdent, opos : OutPosition):
        assert v not in self.bind_var_to_pos, (v, self.bind_var_to_pos)
        self.bind_var_to_pos[v] = op_ident, opos

        assert opos not in self.bind_pos_to_var[op_ident], (opos, self.bind_pos_to_var[op_ident])
        self.bind_pos_to_var[op_ident][opos] = v

    def _add_use(self, v : VarIdent, op_ident : OperationIdent, ipos : InPosition):
        assert (op_ident, ipos) not in self.use_var_to_pos[v]
        self.use_var_to_pos[v].add((op_ident, ipos))

        assert ipos not in self.use_pos_to_var[op_ident], (ipos, self.use_pos_to_var[op_ident])
        self.use_pos_to_var[op_ident][ipos] = v

    def add_parameters(self, names : IList[str]) -> Tuple[OperationIdent, IList[VarIdent]]:
        out_vars = tuple(self._new_var_ident(name) for name in names)

        op_ident = self._new_op_ident(("parameters",))

        for i, v in enumerate(out_vars):
            self._add_bind(v, op_ident, ("parameter", i))

        return op_ident, out_vars
    
    def add_return(self, rets : IList[VarIdent]) -> OperationIdent:
        op_ident = self._new_op_ident(("return",))

        for i, v in enumerate(rets):
            self._add_use(v, op_ident, ("return", i))

        return op_ident

    def add_def(self, name : str, func : Function, closure : Dict[Var, VarIdent]) -> Tuple[OperationIdent, VarIdent]:
        f_var = self._new_var_ident(name)
        op_ident = self._new_op_ident(("def", func))

        self._add_bind(f_var, op_ident, ("def",))

        for inner, outer in closure.items():
            self._add_use(outer, op_ident, ("def", inner))

        return op_ident, f_var

    def add_call(self, call_name : str, out_names : IList[str], f : VarIdent, args : IList[VarIdent]) -> Tuple[OperationIdent, IList[VarIdent]]:
        out_vars = tuple(self._new_var_ident(name) for name in out_names)

        op_ident = self._new_op_ident(("call", call_name))
        
        for i, v in enumerate(out_vars):
            self._add_bind(v, op_ident, ("call", i))

        self._add_use(f, op_ident, ("call", None))
        for i, v in enumerate(args):
            self._add_use(v, op_ident, ("call", i))

        return op_ident, out_vars
    
    def add_pack(self, out_name : str, comps : IList[VarIdent]) -> Tuple[OperationIdent, VarIdent]:
        out_var = self._new_var_ident(out_name)

        op_ident = self._new_op_ident(("pack",))
        
        self._add_bind(out_var, op_ident, ("pack",))

        for i, v in enumerate(comps):
            self._add_use(v, op_ident, ("pack", i))

        return op_ident, out_var

    def add_unpack(self, out_names : IList[str], inp : VarIdent) -> Tuple[OperationIdent, IList[VarIdent]]:
        out_vars = tuple(self._new_var_ident(name) for name in out_names)

        op_ident = self._new_op_ident(("unpack",))
        
        for i, v in enumerate(out_vars):
            self._add_bind(v, op_ident, ("unpack", i))

        self._add_use(inp, op_ident, ("unpack",))

        return op_ident, out_vars
    
    def add_prim(self, out_name : str, obj : Object) -> Tuple[OperationIdent, VarIdent]:
        out_var = self._new_var_ident(out_name)

        op_ident = self._new_op_ident(("prim", obj))
        self._add_bind(out_var, op_ident, ("prim",))

        return op_ident, out_var
    
    def add_task(self, call_name : str, out_names : IList[str], task : Task) -> Tuple[OperationIdent, IList[VarIdent]]:
        out_vars = tuple(self._new_var_ident(name) for name in out_names)

        op_ident = self._new_op_ident(("task", call_name, task))
        
        for i, v in enumerate(out_vars):
            self._add_bind(v, op_ident, ("task", i))

        return op_ident, out_vars

    def get_var_name(self, v : VarIdent) -> str:
        return self.vars[v]

    def get_op_as_parameters(self, ident : OperationIdent) -> IList[VarIdent]:
        match self.ops[ident]:
            case "parameters",: pass
            case x: assert False, x
        
        out_params : Dict[int, VarIdent] = {}
        for opos, v in self.bind_pos_to_var[ident].items():
            match opos:
                case "parameter", i:
                    out_params[i] = v
                case x:
                    assert False, x
        
        return int_dict_as_contiguous(out_params)

    def get_op_as_return(self, ident : OperationIdent) -> IList[VarIdent]:
        match self.ops[ident]:
            case "return",: pass
            case x: assert False, x
        
        in_params : Dict[int, VarIdent] = {}
        for opos, v in self.use_pos_to_var[ident].items():
            match opos:
                case "return", i:
                    in_params[i] = v
                case x:
                    assert False, x
        
        return int_dict_as_contiguous(in_params)
    

    def get_op_as_call(self, ident : OperationIdent) -> Tuple[str, IList[VarIdent], VarIdent, IList[VarIdent]]:
        match self.ops[ident]:
            case "call", call_name: pass
            case x: assert False, x
        
        f : Optional[VarIdent] = None
        args : Dict[int, VarIdent] = {}
        for ipos, v in self.use_pos_to_var[ident].items():
            match ipos:
                case "call", None:
                    assert f is None
                    f = v
                case "call", i:
                    args[i] = v
                case x:
                    assert False, x

        outs : Dict[int, VarIdent] = {}
        for opos, v in self.bind_pos_to_var[ident].items():
            match opos:
                case "call", i:
                    outs[i] = v
                case x:
                    assert False, x
        
        assert f is not None
        return call_name, int_dict_as_contiguous(outs), f, int_dict_as_contiguous(args)
    
    def get_op_as_def(self, ident : OperationIdent) -> Tuple[Function, VarIdent, Dict[Var, VarIdent]]:
        match self.ops[ident]:
            case "def", func: pass
            case x: assert False, x
        
        bnds = self.bind_pos_to_var[ident]
        assert len(bnds) == 1
        f = bnds["def",]

        closure : Dict[Var, VarIdent] = {}
        for opos, v in self.use_pos_to_var[ident].items():
            match opos:
                case "def", v_old:
                    assert v_old not in closure
                    closure[v_old] = v
                case x:
                    assert False, x
        
        return func, f, closure
    

    def get_op_as_pack(self, ident : OperationIdent) -> Tuple[VarIdent, IList[VarIdent]]:
        match self.ops[ident]:
            case "pack",: pass
            case x: assert False, x
        
        inps : Dict[int, VarIdent] = {}
        for ipos, v in self.use_pos_to_var[ident].items():
            match ipos:
                case "pack", i:
                    inps[i] = v
                case x:
                    assert False, x

        bnds = self.bind_pos_to_var[ident]
        assert len(bnds) == 1
        outp = bnds["pack",]
        
        return outp, int_dict_as_contiguous(inps)
    
    def get_op_as_unpack(self, ident : OperationIdent) -> Tuple[IList[VarIdent], VarIdent]:
        match self.ops[ident]:
            case "unpack",: pass
            case x: assert False, x
        
        uses = self.use_pos_to_var[ident]
        assert len(uses) == 1
        inp = uses["unpack",]

        outs : Dict[int, VarIdent] = {}
        for opos, v in self.bind_pos_to_var[ident].items():
            match opos:
                case "unpack", i:
                    outs[i] = v
                case x:
                    assert False, x
        
        return int_dict_as_contiguous(outs), inp
    
    def get_op_as_prim(self, ident : OperationIdent) -> Tuple[VarIdent, Object]:
        match self.ops[ident]:
            case "prim", obj: pass
            case x: assert False, x

        bnds = self.bind_pos_to_var[ident]
        assert len(bnds) == 1, bnds
        outp = bnds["prim",]
        
        return outp, obj

    def get_op_as_task(self, ident : OperationIdent) -> Tuple[str, IList[VarIdent], Task]:
        match self.ops[ident]:
            case "task", call_name, task: pass
            case x: assert False, x

        outs : Dict[int, VarIdent] = {}
        for opos, v in self.bind_pos_to_var[ident].items():
            match opos:
                case "task", i:
                    outs[i] = v
                case x:
                    assert False, x
        
        return call_name, int_dict_as_contiguous(outs), task

    def get_call_def(self, ident : OperationIdent) -> Optional[OperationIdent]:
        assert self.ops[ident][0] == "call"
        f = self.use_pos_to_var[ident]["call", None]
        def_pos = self.bind_var_to_pos[f]
        match def_pos:
            case def_ident, ("def",):
                return def_ident
            case _:
                return None

    def get_call_prims(self, ident : OperationIdent) -> Optional[Tuple[OperationIdent, IList[OperationIdent]]]:
        assert self.ops[ident][0] == "call"

        f_ident : Optional[OperationIdent] = None
        arg_idents : Dict[int, OperationIdent] = {}
        for ipos, v in self.use_pos_to_var[ident].items():
            match self.bind_var_to_pos[v]:
                case arg_ident, ("prim",):
                    pass
                case _:
                    return None
                
            match ipos:
                case "call", None:
                    assert f_ident is None
                    f_ident = arg_ident
                case "call", i:
                    arg_idents[i] = arg_ident
                case x:
                    assert False, x
        assert f_ident is not None
        return f_ident, int_dict_as_contiguous(arg_idents)
            
    def get_unpack_pack(self, ident : OperationIdent) -> Optional[OperationIdent]:
        assert self.ops[ident][0] == "unpack"
        pack = self.use_pos_to_var[ident]["unpack",]
        pack_pos = self.bind_var_to_pos[pack]
        match pack_pos:
            case pack_ident, ("pack",):
                return pack_ident
            case _:
                return None
    
    def replace_op_with_vars(self, ident : OperationIdent, subst : Callable[[OutPosition], Optional[VarIdent]]) -> OpIdSet:
        del self.ops[ident]
        touched_ops : MutableSet[OperationIdent] = set()

        for opos, v in self.bind_pos_to_var.pop(ident).items():
            ident2, opos2 = self.bind_var_to_pos.pop(v)
            assert ident == ident2, (ident, ident2)
            assert opos == opos2, (opos, opos2)
            
            v_new = subst(opos)

            for ident_recip, ipos in self.use_var_to_pos.pop(v):
                touched_ops.add(ident_recip)
                v2 = self.use_pos_to_var[ident_recip].pop(ipos)
                assert v == v2, (v, v2)

                assert v_new is not None
                self._add_use(v_new, ident_recip, ipos)
            
            del self.vars[v]

        for ipos, v in self.use_pos_to_var.pop(ident).items():
            self.use_var_to_pos[v].remove((ident, ipos))

            # COULD BE MORE SELECTIVE HERE ABOUT ONLY TOUCHING DEF, PACK?
            ident_recip, _opos = self.bind_var_to_pos[v]
            touched_ops.add(ident_recip)

        return frozenset(touched_ops)