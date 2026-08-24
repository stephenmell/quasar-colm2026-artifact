import ast
import inspect
import pprint
import asyncio

from . import syntax
from . import semantics
from . import printing

# DEFAULT_SEMANTICS = semantics.reduce_cbv_weak_sync
DEFAULT_SEMANTICS = semantics.reduce_graph_opportunistic

class Collapser:
    def __add__(self, other):
        return other

    def __iadd__(self, other):
        return other

class DefBuilder:
    def __init__(self, var, args, return_vars):
        self.statements = []
        self.return_var = None

    def add_statement(statement):
        if type(statement) is DefBuilder:
            pass
        elif statement[0] == "call":
            _, debug, out, func, args = statement
            if is_bound(func):
                self.statements.append(statement)
            else:
                self.statements.append(new_placeholder(var))
        else:
            self.statements.append(statement)

    def add_call(var):
        pass

    def resolve_placeholder(placeholder, value):
        for i in range(len(self.statements)):
            if type(statement) is DefBuilder:
                statement.resolve_placeholder(placeholder, value)
            if self.statements[i] == placeholder:
                self.statements[i] = value

    def finalize():
        final_statements = []
        for statement in self.statements:
            if type(statement) is DefBuilder:
                final_statements.append(statement.finalize())
            elif type(statement) is Placeholder:
                raise RuntimeError("Not all placeholders were substituted!")
            else:
                final_statements.append(final_statements)
        return ("def", var, (tuple(args), (tuple(final_statements), tuple(return_vars))))

class EpicFunction:
    globals_namespaces = []
    namespace_var_lookup = []

    def __init__(self, py_function): # Merge bound var into namespace top level vars, free vars tracked per function
        self.semantics = DEFAULT_SEMANTICS

        self.py_function = py_function

        globals_namespace = self.py_function.__globals__
        try:
            index = EpicFunction.globals_namespaces.index(globals_namespace)
            namespace_vars = EpicFunction.namespace_var_lookup[index]
        except ValueError:
            namespace_vars = {}
            EpicFunction.globals_namespaces.append(globals_namespace)
            EpicFunction.namespace_var_lookup.append(namespace_vars)

        func_ast, func_filename, func_lineno = ast_from_function(py_function)
        rewriter = RewriteEpic(func_ast, func_filename, func_lineno, namespace_vars)
        self.epic_ast = rewriter.epic_ast
        self.top_level_vars = rewriter.top_level_vars
        #pprint.pp(self.epic_ast)

    def __call__(self, *arg_values):
        #print(function.__globals__)
        #print(function.__closure__)
        #print(inspect.getclosurevars(self.py_function))
        pprint.pp(self.epic_ast)

        bound_statements = []

        handled_vars = set()

        for var, statements in builtins_statements.items():
            bound_statements.append(statements)
            handled_vars.add(var)

        bind_top_level_vars(bound_statements, handled_vars, self)

        (args, (unbound_statements, return_vars)) = self.epic_ast[2]

        args_num = len(args)
        values_num = len(arg_values)

        if args_num < values_num:
            raise TypeError(self.epic_ast[1].name + "() takes " + str(args_num) + " positional argument" + ("" if args_num == 1 else "s") + " but " + str(values_num) + " " + ("was" if values_num == 1 else "were") + " given")

        if args_num > values_num:
            num_delta = args_num - values_num
            arg_names = []
            for arg in args[-num_delta:]:
                arg_names.append("'" + arg.name + "'")
            raise TypeError(self.epic_ast[1].name + "() missing " + str(num_delta) + " required positional argument" + ("" if num_delta == 1 else "s") + ": " + (" and ".join(arg_names)))

        for i, arg in enumerate(args):
            #handle_constant
            bound_statements.append(("prim", arg, wrap(arg_values[i])))

        bound_statements.extend(list(unbound_statements))
        expression = (args, (tuple(bound_statements), return_vars))

        #pprint.pp(expression)

        printing.print_twocolumn_trace(expression, self.semantics)
        print("========================================================\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        printing.print_final(expression, self.semantics)

class PythonFunction:
    def __init__(self, py_function):
        self.py_function = py_function

        globals_namespace = self.py_function.__globals__
        try:
            index = EpicFunction.globals_namespaces.index(globals_namespace)
            namespace_vars = EpicFunction.namespace_var_lookup[index]
        except ValueError:
            namespace_vars = {}
            EpicFunction.globals_namespaces.append(globals_namespace)
            EpicFunction.namespace_var_lookup.append(namespace_vars)

        var = syntax.var(py_function.__name__)

        namespace_vars[py_function.__name__] = ("bound", var)

    def __call__(self, *args, **kwargs):
        return self.py_function(*args, **kwargs)

class WrappedCallable:
    def __init__(self, obj, wrapper):
        self._obj = obj
        self._wrapper = wrapper
        self.__name__ = wrapper.__name__

    def __call__(self, *args, **kwargs):
        return wrap(self._wrapper(*args, **kwargs))

    def __getattr__(self, attr):
        return wrap(getattr(self._obj, attr))

def wrap(function, TO_CHURCH=False):
    if isinstance(function, EpicFunction) or isinstance(function, WrappedCallable):
        return function
    wrapped = function
    if callable(function):
        #if signature is None:
            #signature = inspect.signature(function)
            #stmts.append(("call", function, (var_next,), function, (var_cur, x_var,)))
        #if inspect.isgeneratorfunction(function):
        #    async def wrapped(*args, **kwargs):
        #        itr = function(*args, **kwargs)
        #        items = []
        #        is_done = [False]
        #        event_more = asyncio.Event()
        #
        #        async def consumer():
        #            async for c in itr:
        #                items.append(c)
        #                event_more.set()
        #            is_done[0] = True
        #            event_more.set()
        #        asyncio.create_task(consumer())
        #
        #        async def l():
        #            i = 0
        #            while True:
        #                if i < len(items):
        #                    yield items[i]
        #                    i += 1
        #                else:
        #                    if is_done[0]:
        #                        break
        #                    else:
        #                        event_more.clear()
        #                        await event_more.wait()
        #
        #        async def init():
        #            itr = l()
        #            async def get_next():
        #                var_s0 = syntax.var("s0")
        #                var_append = syntax.var("append")
        #                var_cur = var_s0
        #                stmts = []
        #                try:
        #                    v = await anext(itr)
        #
        #                    var_next = syntax.var(f"sv")
        #                    x_var = syntax.var("component_0")
        #                    stmts.append(("prim", prim_var, v))
        #                    stmts.append(("call", f"list_{v}", (var_next,), var_append, (var_cur, x_var,)))
        #                    var_cur = var_next
        #
        #                    var_next = syntax.var(f"sk")
        #                    var_k = syntax.var(f"k")
        #                    var_l2 = syntax.var(f"l2")
        #                    stmts.append(("prim", var_k, get_next))
        #                    stmts.append(("call", f"list_k", (var_l2,), var_k, ()))
        #                    stmts.append(("call", f"concat_k", (var_next,), var_l2, (var_cur, var_append,)))
        #                    var_cur = var_next
        #                except StopAsyncIteration:
        #                    pass
        #                var_list = syntax.var("list")
        #                return (
        #                    ("def", var_list, ((var_s0, var_append), (tuple(stmts), (var_cur,)))),
        #                ), (var_list,)
        #            return await get_next()
        #
        #        var_k = syntax.var("k")
        #        var_s0 = syntax.var("s0")
        #        var_sf = syntax.var("sf")
        #        var_append = syntax.var("append")
        #        var_list = syntax.var("list")
        #        return (
        #            ("def", var_list, ((var_s0, var_append,), ((
        #                ("prim", var_k, init),
        #                ("call", "list_k", (var_list,), var_k, ()),
        #                ("call", "list", (var_sf,), var_list, (var_s0, var_append)),
        #            ), (var_sf,)))),
        #        ), (var_list,)
        #else:
        if inspect.iscoroutinefunction(function) and (not inspect.isgeneratorfunction(function) or inspect.isasyncgenfunction(function)):
            if TO_CHURCH:
                async def wrapped(*args, **kwargs):
                    return list_to_church(await function(*args, **kwargs))
            else:
                async def wrapped(*args, **kwargs):
                    prim_var = syntax.var("#implicit#")
                    return (("prim", prim_var, await function(*args, **kwargs)),), (prim_var,)
        else:
            if TO_CHURCH:
                def wrapped(*args, **kwargs):
                    return list_to_church(function(*args, **kwargs))
            else:
                def wrapped(*args, **kwargs):
                    prim_var = syntax.var("#implicit#")
                    return (("prim", prim_var, function(*args, **kwargs)),), (prim_var,)

        wrapped.__name__ = function.__name__
        if function != wrapped:
            wrapped = WrappedCallable(function, wrapped)
    else:
        pass

    return wrapped

def translateToEpic(func_ast, func_filename, func_lineno):
    rewriter = RewriteEpic(func_ast, func_filename, func_lineno)
    return (rewriter.epic_ast, rewriter.top_level_vars)

def translationFinalize(epic, arg_values, mappings):
    epic_ast, top_level_vars = epic

    # pprint.pp(epic_ast)

    bound_statements = []

    for var, statements in builtins_statements.items():
        bound_statements.append(statements)

    for name in top_level_vars:
        (category, var) = top_level_vars[name]
        if not name in mappings:
            if name == "len":
                bound_statements.extend(make_len(var))
            else:
                raise NameError(name)
        else:
            bound_statements.append(("prim", var, mappings[name]))

    (args, (unbound_statements, return_vars)) = epic_ast[2]

    args_num = len(args)
    values_num = len(arg_values)

    if args_num < values_num:
        raise TypeError(epic_ast[1].name + "() takes " + str(args_num) + " positional argument" + ("" if args_num == 1 else "s") + " but " + str(values_num) + " " + ("was" if values_num == 1 else "were") + " given")

    if args_num > values_num:
        num_delta = args_num - values_num
        arg_names = []
        for arg in args[-num_delta:]:
            arg_names.append("'" + arg.name + "'")
        raise TypeError(epic_ast[1].name + "() missing " + str(num_delta) + " required positional argument" + ("" if num_delta == 1 else "s") + ": " + (" and ".join(arg_names)))

    for i, arg in enumerate(args):
        bound_statements.append(("prim", arg, arg_values[i]))

    bound_statements.extend(list(unbound_statements))
    expression = (args, (tuple(bound_statements), return_vars))
    return expression

    #pprint.pp(expression)

def interpretEpic(expression, semantics = DEFAULT_SEMANTICS):
    return tuple(semantics(expression))

def traceEpic(expression, semantics = DEFAULT_SEMANTICS):
    printing.print_twocolumn_trace(expression, semantics)
    print("========================================================\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    printing.print_final(expression, semantics)

bool_var = syntax.var("bool")
true_arg = syntax.var("true")
false_arg = syntax.var("false")
def bool_to_church(b : bool):
    if b:
        true_var = syntax.var("true")
        return (("def", true_var, ((true_arg, false_arg), ((), (true_arg,)))),), (true_var,)
    else:
        false_var = syntax.var("false")
        return (("def", false_var, ((true_arg, false_arg), ((), (false_arg,)))),), (false_var,)

list_var = syntax.var("list")
def list_to_church(l : iter, iter_var=None):
    try:
        if iter_var is None:
            iter_var = syntax.var("#list#")
        init_arg = syntax.var("s0")
        append_arg = syntax.var("append")
        state_var = init_arg
        statements = []
        for i, x in enumerate(l):
            next_state_var = syntax.var(f"s{i + 1}")
            if type(x) is syntax.Var:
                prim_var = x
            else:
                prim_var = syntax.var(f"p{i}")
                statements.append(("prim", prim_var, x))
            statements.append(("call", f"i{i}", (next_state_var,), append_arg, (state_var, prim_var,)))
            state_var = next_state_var
        return (("def", iter_var, ((init_arg, append_arg), (tuple(statements), (state_var,)))),), (iter_var,)
    except TypeError:
        return (), (l,)

def list_element(elem):
    return [elem]

def collapse_list():
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left == right),), (prim_var,)

prim_add_var = syntax.var("+")
def prim_add(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left + right),), (prim_var,)

def collapse_list():
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left == right),), (prim_var,)

eq_var = syntax.var("==")
def eq(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left == right),), (prim_var,)

noteq_var = syntax.var("!=")
def noteq(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left != right),), (prim_var,)

lt_var = syntax.var("<")
def lt(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left < right),), (prim_var,)

lte_var = syntax.var("<=")
def lte(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left <= right),), (prim_var,)

gt_var = syntax.var(">")
def gt(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left > right),), (prim_var,)

gte_var = syntax.var(">=")
def gte(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left >= right),), (prim_var,)

is_var = syntax.var("is")
def is_(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left is right),), (prim_var,)

isnot_var = syntax.var("is not")
def isnot(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left is not right),), (prim_var,)

in_var = syntax.var("in")
def in_(left, right: list):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left in right),), (prim_var,)

notin_var = syntax.var("not in")
def notin(left, right: list):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left not in right),), (prim_var,)

and_var = syntax.var("and")
def and_(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left and right),), (prim_var,)

or_var = syntax.var("or")
def or_(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left or right),), (prim_var,)

uadd_var = syntax.var("+")
def uadd(operand):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, +operand),), (prim_var,)

usub_var = syntax.var("-")
def usub(operand):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, -operand),), (prim_var,)

not_var = syntax.var("not")
def not_(operand):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, not operand),), (prim_var,)

invert_var = syntax.var("~")
def invert(operand):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, ~operand),), (prim_var,)

add_var = syntax.var("+")
left_arg = syntax.var("left")
right_arg = syntax.var("right")
def add():
    statements = []
    init_arg = syntax.var("init")
    append_arg = syntax.var("append")
    s0_var = syntax.var("s0")
    statements.append(("call", f"lhs", (s0_var,), left_arg, (init_arg, append_arg,)))
    s1_var = syntax.var("s1")
    statements.append(("call", f"rhs", (s1_var,), right_arg, (s0_var, append_arg,)))
    ret_var = syntax.var("ret")
    return ("def", add_var, ((left_arg, right_arg), ((("def", ret_var, ((init_arg, append_arg), (tuple(statements), (s1_var,)))),), (ret_var,))))
add = add()

sub_var = syntax.var("-")
def sub(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left - right),), (prim_var,)

mult_var = syntax.var("*")
def mult(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left * right),), (prim_var,)

div_var = syntax.var("/")
def div(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left / right),), (prim_var,)

floordiv_var = syntax.var("//")
def floordiv(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left // right),), (prim_var,)

mod_var = syntax.var("%")
def mod(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left % right),), (prim_var,)

pow_var = syntax.var("**")
def pow_(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left ** right),), (prim_var,)

lshift_var = syntax.var("<<")
def lshift(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left << right),), (prim_var,)

rshift_var = syntax.var(">>")
def rshift(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left >> right),), (prim_var,)

bitor_var = syntax.var("|")
def bitor(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left | right),), (prim_var,)

bitxor_var = syntax.var("^")
def bitxor(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left ^ right),), (prim_var,)

bitand_var = syntax.var("&")
def bitand(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left & right),), (prim_var,)

matmult_var = syntax.var("@")
def matmult(left, right):
    prim_var = syntax.var("#implicit#")
    return (("prim", prim_var, left @ right),), (prim_var,)

format_var = syntax.var("format")
str_var = syntax.var("str")
repr_var = syntax.var("repr")
ascii_var = syntax.var("ascii")

def getattr_(obj, attr):
    return wrap(getattr(obj, attr))
getattr_var = syntax.var("getattr")

def make_len(len_var):
    statements = []

    incr_var = syntax.var("#incr#")
    count_arg = syntax.var("cur")
    elem_arg = syntax.var("elem")
    body_statements = []
    prim_var = syntax.var("#implicit#")
    body_statements.append(("prim", prim_var, 1))
    return_var = syntax.var("#implicit#")
    body_statements.append(("call", f"len", tuple([return_var]), prim_add_var, tuple([count_arg, prim_var])))
    statements.append(("def", incr_var, (tuple([count_arg, elem_arg]), (tuple(body_statements), (return_var,)))))

    church_arg = syntax.var("iter")
    body_statements = []
    init_var = syntax.var("#implicit#")
    body_statements.append(("prim", init_var, 0))
    return_var = syntax.var("#implicit#")
    body_statements.append(("call", f"len", tuple([return_var]), church_arg, tuple([init_var, incr_var])))
    statements.append(("def", len_var, (tuple([church_arg]), (tuple(body_statements), (return_var,)))))

    return statements

def identity(value):
    return value

def ast_from_function(function):
    func_filename = function.__code__.co_filename
    func_lineno = function.__code__.co_firstlineno - 1
    func_ast = ast.parse(inspect.getsource(function), filename=function.__code__.co_filename, mode='exec', type_comments=True)
    return func_ast, func_filename, func_lineno

class RewriteEpic:
    def __init__(self, func_ast, func_filename, func_lineno, namespace_vars=None):
        self.filename = func_filename
        self.lineno = func_lineno

        if namespace_vars == None:
            namespace_vars = {}

        self.var_frames = [namespace_vars]
        self.top_level_vars = {}

        self.passthrough_var_frames = [{}]
        self.function_frames = []
        self.block_frames = []

        self.is_top_level = True

        self.scope_statements = []
        self.return_vars = []
        self.loop_nesting = 0

        self.var_merge_history = {}

        self.epic_ast = self.visit(func_ast)

    def _ni(self, node, what: str) -> None:
        """Raise a richly-informative NotImplementedError."""
        import ast as _ast
        if isinstance(node, _ast.AST):
            line = getattr(node, "lineno", None)
            col = getattr(node, "col_offset", None)
            if line is not None:
                loc = f"at line {line}"
                if col is not None:
                    loc += f", col {col}"
            else:
                loc = ""
            try:
                ast_text = _ast.dump(node, include_attributes=False)
            except Exception:
                ast_text = repr(node)
            extra = f"\nAST: {node.__class__.__name__} -> {ast_text}"
        else:
            loc = f"at lineno {self.lineno}"
            extra = f"\nObject: {type(node).__name__} -> {getattr(node, 'name', repr(node))}"
            
        raise NotImplementedError(f"{what} not supported {loc}{extra}")

    def new_var(self, name: str):
        return syntax.var(name)

    def lazy_var(self, name: str):
        return syntax.Var(None, name)

    def resolve_lazy_var_to_name(self, lazy: syntax.Var, name: str):
        if name is None:
            name = lazy.name
        if lazy.id is None:
            var = syntax.var(name)
            lazy.__dict__['id'] = var.id
        lazy.__dict__['name'] = name
        return lazy

    def merge_var_into(self, var: syntax.Var, into: syntax.Var):
        if var.id == into.id:
            return var
        history = self.var_merge_history.setdefault(into.id, [])
        if var.id is not None:
            prev = self.var_merge_history.get(var.id)
            if prev is not None:
                for merged in prev:
                    merged.__dict__['id'] = into.id
                    merged.__dict__['name'] = into.name
                    history.append(merged)
                del self.var_merge_history[var.id]
        var.__dict__['id'] = into.id
        var.__dict__['name'] = into.name
        history.append(var)
        return var

    def make_implicit_var(self):
        return self.lazy_var("#implicit#")

    def solidify_var(self, var: syntax.Var):
        if var.id is None:
            return self.resolve_lazy_var_to_name(var, None)
        else:
            return var

    def var_is_solid(self, var: syntax.Var):
        return var.id is not None

    def track_var(self, category, var, var_frame=None):
        if var_frame is None:
            var_frame = self.var_frames[-1]
        self.resolve_lazy_var_to_name(var, var.name)
        var_frame[var.name] = (category, var)
        return var

    def get_var(self, name: str, filter_categories: list, var_frame=None):
        if var_frame is None:
            var_frame = self.var_frames[-1]
        if name in var_frame:
            (category, var) = var_frame[name]
            if filter_categories is None or category in filter_categories:
                return var
        else:
            return None

    def get_block_var(self, name: str, filter_categories: list):
        for var_frame in reversed(self.var_frames):
            if name in var_frame:
                (category, var) = var_frame[name]
                if filter_categories is None or category in filter_categories:
                    return var
            if var_frame == self.block_frames[-1]:
                break
        return None

    def get_function_var_names(self, filter_categories: list):
        names = set()
        for var_frame in reversed(self.var_frames):
            for name in var_frame:
                (category, var) = var_frame[name]
                if filter_categories is None or category in filter_categories:
                    names.add(name)
            if var_frame == self.function_frames[-1]:
                break
        return names

    def get_or_create_var(self, name: str):
        local_vars = self.var_frames[-1]
        if name in local_vars:
            (category, var) = local_vars[name]
            return var
        return self.track_var("free", self.new_var(name))

    def register_passthrough(self, name):
        passthrough = self.passthrough_var_frames[-1]
        if name not in passthrough:
            existing = self.get_block_var(name, ["free"])
            if existing is not None:
                passthrough[name] = existing
            else:
                passthrough[name] = self.lazy_var(name)

    def visit_lhs(self, node, var_frame, statements, out_var=None, passthrough=True):
        node_type = type(node)

        if node_type is ast.Tuple:
            if out_var is None:
                out_var = self.make_implicit_var()
            unpack_vars = []
            for elt in node.elts:
                var = self.make_implicit_var()
                unpack_vars.append(self.visit_lhs(elt, var_frame, statements, out_var=var, passthrough=passthrough))
                self.solidify_var(var)
            statements.append(("unpack", tuple(unpack_vars), self.solidify_var(out_var)))
            return out_var
        elif node_type is ast.Name:
            ctx_type = type(node.ctx)

            if ctx_type is ast.Load:
                raise NotImplementedError
            elif ctx_type is ast.Store:
                pass
            elif ctx_type is ast.Del:
                raise NotImplementedError
            else:
                raise NotImplementedError

            if passthrough:
                self.register_passthrough(node.id)
            var = self.get_var(node.id, ["scoped"], var_frame=var_frame) or self.new_var(node.id)
            if out_var is None:
                self.track_var("scoped", var, var_frame=var_frame)
            else:
                if self.var_is_solid(out_var):
                    packed_var = self.solidify_var(self.make_implicit_var())
                    statements.append(("pack", packed_var, tuple([out_var])))
                    statements.append(("unpack", tuple([var]), packed_var))
                else:
                    self.merge_var_into(out_var, var)
                self.track_var("bound", var, var_frame=var_frame)
            return var
        elif node_type is ast.Subscript:
            print(node_type)
            # raise NotImplementedError
            self._ni(node, "Subscript targets on the LHS are not supported")
        else:
            print(node_type)
            raise NotImplementedError

    def add_return(self, value, func=identity, from_expression=False):
        if not from_expression and self.loop_nesting > 0:
            raise NotImplementedError
        return_var = self.return_vars[-1]
        if return_var is None:
            return_var = func(value)
            self.return_vars[-1] = return_var
        else:
            raise NotImplementedError
        return return_var

    def build_block(self, var, child, arg_names=[], var_frame=None, from_expression=False):
        if var_frame == None:
            var_frame = {}
        self.var_frames.append(var_frame)

        self.scope_statements.append([])
        self.return_vars.append(None)

        args = []
        for arg_name in arg_names:
            args.append(self.track_var("bound", self.new_var(arg_name)))

        if from_expression:
            node = child
            self.add_return(node, self.visit, from_expression)
        else:
            nodes = child
            for node in nodes:
                term = self.visit(node)
                if term is not None:
                    term_type = type(term)
                    if term_type is syntax.Var:
                        self.solidify_var(term)
                    elif term_type is list:
                        self.scope_statements[-1].extend(term)
                    else:
                        self.scope_statements[-1].append(term)

        local_vars = self.var_frames.pop()

        return_var = self.return_vars.pop()

        local_statements = self.scope_statements.pop()

        return local_statements, return_var, local_vars, args

    def propagate_free_vars(self, local_vars, parent_vars):
        for name in local_vars:
            (category, local_var) = local_vars[name]
            if category == "bound":
                pass
            elif category == "scoped":
                # raise NotImplementedError
                self._ni(self.new_var(name), "Propagating a scoped (local) variable as a free var is not supported")
            elif category == "free":
                if name in parent_vars:
                    self.merge_var_into(local_var, parent_vars[name][1])
                else:
                    parent_vars[name] = (category, local_var)

    def handle_binop(self, op, left, right, lineno):
        comp_type = type(op)

        if comp_type is ast.Add:
            comp_var = prim_add_var
            #comp_var = add_var
        elif comp_type is ast.Sub:
            comp_var = sub_var
        elif comp_type is ast.Mult:
            comp_var = mult_var
        elif comp_type is ast.Div:
            comp_var = div_var
        elif comp_type is ast.FloorDiv:
            comp_var = floordiv_var
        elif comp_type is ast.Mod:
            comp_var = mod_var
        elif comp_type is ast.Pow:
            comp_var = pow_var
        elif comp_type is ast.LShift:
            comp_var = lshift_var
        elif comp_type is ast.RShift:
            comp_var = rshift_var
        elif comp_type is ast.BitOr:
            comp_var = bitor_var
        elif comp_type is ast.BitXor:
            comp_var = bitxor_var
        elif comp_type is ast.BitAnd:
            comp_var = bitand_var
        elif comp_type is ast.MatMult:
            comp_var = matmult_var
        else:
            raise NotImplementedError

        out_var = self.make_implicit_var()
        self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + lineno}", tuple([out_var]), comp_var, tuple([self.solidify_var(left), self.solidify_var(right)])))
        return out_var

    def handle_constant(self, value):
        value_type = type(value)

        out_var = self.make_implicit_var()

        if value_type is str:
            #(statements, (church_var,)) = list_to_church(value, iter_var=out_var)
            #self.scope_statements[-1].extend(statements)
            self.scope_statements[-1].append(("prim", out_var, value))
        else:
            self.scope_statements[-1].append(("prim", out_var, value))
            #(statements, (church_var,)) = list_to_church([value], iter_var=out_var)
            #self.scope_statements[-1].extend(statements)

        return out_var

    def visit(self, node):
        node_type = type(node)

        if node_type is ast.FunctionDef:
            is_top_level = self.is_top_level
            if is_top_level:
                var = self.get_or_create_var(node.name)
                self.solidify_var(var)
                self.is_top_level = False
            else:
                var = self.track_var("bound", self.new_var(node.name))

            loop_nesting = self.loop_nesting
            self.loop_nesting = 0

            self.passthrough_var_frames.append({})

            arg_names = []
            for arg_node in node.args.args:
                arg_names.append(arg_node.arg)

            local_vars = {}
            self.function_frames.append(local_vars)
            self.block_frames.append(local_vars)
            statements, return_var, local_vars, args = self.build_block(var, node.body, arg_names=arg_names, var_frame=local_vars)
            local_vars = self.function_frames.pop()
            local_vars = self.block_frames.pop()

            parent_vars = self.var_frames[-1]
            self.propagate_free_vars(local_vars, parent_vars)

            self.loop_nesting = loop_nesting

            if return_var is None:
                return_var = self.make_implicit_var()
                statements.append(("prim", return_var, None))
            self.solidify_var(return_var)

            passthrough = self.passthrough_var_frames.pop()

            if is_top_level:
                for name in local_vars:
                    (category, local_var) = local_vars[name]
                    if category == "free":
                        if name in self.top_level_vars:
                            self.merge_var_into(local_var, self.top_level_vars[name][1])
                        elif self.var_is_solid(local_var):
                            self.top_level_vars[name] = (category, local_var)

            return ("def", var, (tuple(args), (tuple(statements), tuple([return_var]))))

        elif node_type is ast.Assign:
            var_frame = self.var_frames[-1]
            statements = self.scope_statements[-1]
            out_var = self.visit(node.value)
            for target in reversed(node.targets):
                out_var = self.visit_lhs(target, var_frame, statements, out_var=out_var)

        elif node_type is ast.AnnAssign:
            #node.annotation
            #node.simple
            var_frame = self.var_frames[-1]
            statements = self.scope_statements[-1]
            self.visit_lhs(node.target, var_frame, statements)

        elif node_type is ast.AugAssign: # TODO: Error if not bound
            var_frame = self.var_frames[-1]
            statements = self.scope_statements[-1]
            out_var = self.handle_binop(node.op, self.get_or_create_var(node.target.id), self.visit(node.value), node.lineno)
            self.visit_lhs(node.target, var_frame, statements, out_var=out_var)

        elif node_type is ast.NamedExpr:
            var_frame = self.var_frames[-1]
            statements = self.scope_statements[-1]
            out_var = self.visit(value)
            return self.visit_lhs(node.target, var_frame, statements, out_var=out_var)

        elif node_type is ast.Call:
            func = None
            args = []
            if type(node.func) is ast.Attribute:
                attr = node.func
                var_name = ""
                while type(attr) is ast.Attribute:
                    var_name = "." + attr.attr + var_name
                    attr = attr.value
                func = self.get_or_create_var(var_name)
                args.append(self.solidify_var(self.visit(attr)))
            else:
                func = self.visit(node.func)
            for arg in node.args:
                args.append(self.solidify_var(self.visit(arg)))
            out_var = self.make_implicit_var()
            self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([out_var]), func, tuple(args)))
            return out_var

        elif node_type is ast.Constant: #TODO: Constant lifting
            return self.handle_constant(node.value)

        elif node_type is ast.Tuple:
            out_var = self.make_implicit_var()
            elts = []
            for elt in node.elts:
                elts.append(self.solidify_var(self.visit(elt)))
            self.scope_statements[-1].append(("pack", out_var, tuple(elts)))
            return out_var

        elif node_type is ast.List:
            elts = []
            for elt in node.elts:
                elts.append(self.solidify_var(self.visit(elt)))
            (statements, (church_var,)) = list_to_church(elts, iter_var=self.make_implicit_var())
            self.scope_statements[-1].extend(statements)
            return church_var

        elif node_type is ast.Return:
            if node.value is None:
                 self.add_return(self.new_var("#implicit#"))
            else:
                return self.add_return(node.value, self.visit)

        elif node_type is ast.Nonlocal:
            raise NotImplementedError
            for name in node.names:
                pass

        elif node_type is ast.Name:
            ctx_type = type(node.ctx)

            if ctx_type is ast.Load:
                pass
            elif ctx_type is ast.Store:
                raise NotImplementedError
            elif ctx_type is ast.Del:
                raise NotImplementedError
            else:
                raise NotImplementedError

            return self.get_or_create_var(node.id)

        elif node_type is ast.Pass:
            pass

        elif node_type is ast.Expr:
            return self.visit(node.value)

        elif node_type is ast.Module:
            if len(node.body) != 1:
                raise NotImplementedError
            return self.visit(node.body[0])

        elif node_type is ast.If or node_type is ast.IfExp:
            from_expression = node_type is ast.IfExp

            statements = []

            test_var = self.solidify_var(self.visit(node.test))

            parent_vars = self.var_frames[-1]

            self.passthrough_var_frames.append({})
            body_var = self.new_var("#body#")
            body_statements, body_literal_return_var, body_local_vars, _ = self.build_block(body_var, node.body, var_frame={}, from_expression=from_expression)
            self.propagate_free_vars(body_local_vars, parent_vars)
            body_passthrough = self.passthrough_var_frames.pop()
            body_passthrough_names = set(body_passthrough.keys())

            for name in body_passthrough:
                local_var = body_passthrough[name]
                if name in parent_vars:
                    self.merge_var_into(local_var, parent_vars[name][1])
                else:
                    parent_vars[name] = ("free", local_var)

            self.passthrough_var_frames.append({})
            else_var = self.new_var("#else#")
            else_statements, else_literal_return_var, else_local_vars, _ = self.build_block(else_var, node.orelse, var_frame={}, from_expression=from_expression)
            self.propagate_free_vars(else_local_vars, parent_vars)
            else_passthrough = self.passthrough_var_frames.pop()
            else_passthrough_names = set(else_passthrough.keys())

            for name in else_passthrough:
                local_var = else_passthrough[name]
                if name in parent_vars:
                    self.merge_var_into(local_var, parent_vars[name][1])
                else:
                    parent_vars[name] = ("free", local_var)

            bound = self.get_function_var_names(["bound"])

            return_var_names = body_passthrough_names.intersection(else_passthrough_names).union(bound.intersection(body_passthrough_names), bound.intersection(else_passthrough_names))
            return_var_names = sorted(list(return_var_names))

            body_pack_vars = []
            else_pack_vars = []
            unpack_vars = []
            expression_return_var = None

            if body_literal_return_var is not None or else_literal_return_var is not None:
                if body_literal_return_var is None or else_literal_return_var is None:
                    raise NotImplementedError("Early returns are not supported")
                self.solidify_var(body_literal_return_var)
                body_pack_vars.append(body_literal_return_var)
                self.solidify_var(else_literal_return_var)
                else_pack_vars.append(else_literal_return_var)
                expression_return_var = self.new_var("#implicit#")
                if not from_expression:
                    self.add_return(expression_return_var)
                unpack_vars.append(expression_return_var)

            for name in return_var_names:
                body_pack_vars.append(self.solidify_var((body_local_vars.get(name) or [None, body_passthrough.get(name)])[1] or self.get_or_create_var(name)))
                else_pack_vars.append(self.solidify_var((else_local_vars.get(name) or [None, else_passthrough.get(name)])[1] or self.get_or_create_var(name)))
                self.register_passthrough(name)
                unpack_vars.append(self.track_var("bound", self.new_var(name)))

            if len(unpack_vars) != 1:
                return_packed = True
                return_var = self.new_var("#implicit#")
                body_return_var = self.new_var("#implicit#")
                body_statements.append(("pack", body_return_var, tuple(body_pack_vars)))
                else_return_var = self.new_var("#implicit#")
                else_statements.append(("pack", else_return_var, tuple(else_pack_vars)))
            else:
                return_packed = False
                return_var = unpack_vars[0]
                body_return_var = body_pack_vars[0]
                else_return_var = else_pack_vars[0]

            statements.append(("def", body_var, (tuple([]), (tuple(body_statements), tuple([body_return_var])))))
            statements.append(("def", else_var, (tuple([]), (tuple(else_statements), tuple([else_return_var])))))
            church_var = self.new_var("#implicit#")
            statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([church_var]), bool_var, tuple([test_var])))
            branch_var = self.new_var("#implicit#")
            statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([branch_var]), church_var, tuple([body_var, else_var])))
            statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([return_var]), branch_var, tuple([])))
            if return_packed:
                statements.append(("unpack", tuple(unpack_vars), return_var))

            self.scope_statements[-1].extend(statements)

            if from_expression:
                return expression_return_var

        elif node_type is ast.For:
            statements = []

            church_var = self.solidify_var(self.visit(node.iter))

            loop_nesting = self.loop_nesting
            self.loop_nesting += 1

            self.passthrough_var_frames.append({})

            loop_var = self.new_var("#for#")
            loop_local_vars = {}
            self.block_frames.append(loop_local_vars)
            loop_statements = []
            loop_values = self.make_implicit_var()
            self.visit_lhs(node.target, loop_local_vars, loop_statements, out_var=loop_values, passthrough=False)
            loop_statements_, loop_literal_return_var, loop_local_vars, _ = self.build_block(loop_var, node.body, var_frame=loop_local_vars)
            loop_local_vars = self.block_frames.pop()
            loop_statements.extend(loop_statements_)
            loop_statements_ = loop_statements

            self.loop_nesting = loop_nesting

            if loop_literal_return_var is not None:
                raise NotImplementedError

            loop_passthrough = self.passthrough_var_frames.pop()

            bound = self.get_function_var_names(["bound"])

            passthrough = set(loop_passthrough.keys()).intersection(bound)
            passthrough = sorted(list(passthrough))

            loop_unpack_vars = []
            loop_pack_vars = []
            pack_vars = []
            unpack_vars = []

            parent_vars = self.var_frames[-1]
            self.propagate_free_vars(loop_local_vars, parent_vars)

            for name in passthrough:
                loop_unpack_vars.append(self.solidify_var(loop_passthrough[name]))
                loop_pack_vars.append(self.solidify_var((loop_local_vars.get(name) or [None, loop_passthrough.get(name)])[1] or self.get_or_create_var(name)))
                pack_vars.append(self.get_or_create_var(name))
                self.register_passthrough(name)
                unpack_vars.append(self.track_var("bound", self.new_var(name)))

            if len(passthrough) != 1:
                passthrough_packed = True
                return_var = self.new_var("#passthrough#")
                loop_arg = self.new_var("#passthrough#")
                loop_statements.insert(0, ("unpack", tuple(loop_unpack_vars), loop_arg))
                loop_return_var = self.new_var("#passthrough#")
                loop_statements.append(("pack", loop_return_var, tuple(loop_pack_vars)))
                state_var = self.new_var("#passthrough#")
            else:
                passthrough_packed = False
                return_var = unpack_vars[0]
                loop_arg = loop_unpack_vars[0]
                loop_return_var = loop_pack_vars[0]
                state_var = pack_vars[0]

            statements.append(("def", loop_var, (tuple([loop_arg, loop_values]), (tuple(loop_statements), tuple([loop_return_var])))))
            if passthrough_packed:
                statements.append(("pack", state_var, tuple(pack_vars)))
            statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([return_var]), church_var, tuple([state_var, loop_var])))
            #church_var = self.new_var("#implicit#")
            #statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([church_var]), list_var, tuple([iter_var])))
            if passthrough_packed:
                statements.append(("unpack", tuple(unpack_vars), return_var))

            self.scope_statements[-1].extend(statements)

            for sub_node in node.orelse: #TODO: Won't work once we have break and continue
                self.visit(sub_node)

        elif node_type is ast.While:
            statements = []

            loop_var = self.new_var("#while#")

            loop_nesting = self.loop_nesting
            self.loop_nesting += 1

            self.passthrough_var_frames.append({})

            body_local_vars = {}
            self.block_frames.append(body_local_vars)
            self.var_frames.append(body_local_vars)
            self.scope_statements.append([])
            test_var = self.solidify_var(self.visit(node.test))
            body_local_vars = self.var_frames.pop()
            loop_statements = self.scope_statements.pop()

            body_var = self.new_var("#body#")

            body_statements, body_literal_return_var, body_local_vars, _ = self.build_block(body_var, node.body, var_frame=body_local_vars)
            body_local_vars = self.block_frames.pop()

            self.loop_nesting = loop_nesting

            if body_literal_return_var is not None:
                raise NotImplementedError

            body_passthrough = self.passthrough_var_frames.pop()

            done_var = self.new_var("#done#")

            bound = self.get_function_var_names(["bound"])

            passthrough = set(body_passthrough.keys()).intersection(bound)
            passthrough = sorted(list(passthrough))

            loop_unpack_vars = []
            body_pack_vars = []
            pack_vars = []
            unpack_vars = []

            parent_vars = self.var_frames[-1]
            self.propagate_free_vars(body_local_vars, parent_vars)

            for name in passthrough:
                loop_unpack_vars.append(self.solidify_var(body_passthrough[name]))
                body_pack_vars.append(self.solidify_var((body_local_vars.get(name) or [None, body_passthrough.get(name)])[1] or self.get_or_create_var(name)))
                pack_vars.append(self.get_or_create_var(name))
                self.register_passthrough(name)
                unpack_vars.append(self.track_var("bound", self.new_var(name)))

            if len(passthrough) != 1:
                passthrough_packed = True
                return_var = self.new_var("#passthrough#")
                loop_arg = self.new_var("#passthrough#")
                body_statements.insert(0, ("unpack", tuple(loop_unpack_vars), loop_arg))
                body_recurse_var = self.new_var("#passthrough#")
                body_statements.append(("pack", body_recurse_var, tuple(body_pack_vars)))
                state_var = self.new_var("#passthrough#")
            else:
                passthrough_packed = False
                return_var = unpack_vars[0]
                loop_arg = loop_unpack_vars[0]
                body_recurse_var = body_pack_vars[0]
                state_var = pack_vars[0]

            body_return_var = self.new_var("#passthrough#")
            body_statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([body_return_var]), loop_var, tuple([body_recurse_var])))
            loop_statements.append(("def", body_var, (tuple([]), (tuple(body_statements), tuple([body_return_var])))))
            loop_statements.append(("def", done_var, (tuple([]), (tuple([]), tuple([loop_arg])))))
            church_var = self.new_var("#implicit#")
            loop_statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([church_var]), bool_var, tuple([test_var])))
            branch_var = self.new_var("#implicit#")
            loop_statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([branch_var]), church_var, tuple([body_var, done_var])))
            loop_return_var = self.new_var("#passthrough#")
            loop_statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([loop_return_var]), branch_var, tuple([])))
            statements.append(("def", loop_var, (tuple([loop_arg]), (tuple(loop_statements), tuple([loop_return_var])))))
            if passthrough_packed:
                statements.append(("pack", state_var, tuple(pack_vars)))
            statements.append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([return_var]), loop_var, tuple([state_var])))
            if passthrough_packed:
                statements.append(("unpack", tuple(unpack_vars), return_var))

            self.scope_statements[-1].extend(statements)

            for sub_node in node.orelse: #TODO: Won't work once we have break and continue
                self.visit(sub_node)

        elif node_type is ast.Compare:
            left = self.solidify_var(self.visit(node.left))
            right = None
            out_var = None

            for op, comparator in zip(node.ops, node.comparators):
                comp_type = type(op)

                if comp_type is ast.Eq:
                    comp_var = eq_var
                elif comp_type is ast.NotEq:
                    comp_var = noteq_var
                elif comp_type is ast.Lt:
                    comp_var = lt_var
                elif comp_type is ast.LtE:
                    comp_var = lte_var
                elif comp_type is ast.Gt:
                    comp_var = gt_var
                elif comp_type is ast.GtE:
                    comp_var = gte_var
                elif comp_type is ast.Is:
                    comp_var = is_var
                elif comp_type is ast.IsNot:
                    comp_var = isnot_var
                elif comp_type is ast.In:
                    comp_var = in_var
                elif comp_type is ast.NotIn:
                    comp_var = notin_var
                else:
                    raise NotImplementedError

                right = self.solidify_var(self.visit(comparator))
                out_var = self.make_implicit_var()
                self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([out_var]), comp_var, tuple([left, right])))
                left = out_var

            return out_var

        elif node_type is ast.BoolOp:
            comp_type = type(node.op)

            if comp_type is ast.And:
                comp_var = and_var
            elif comp_type is ast.Or:
                comp_var = or_var
            else:
                raise NotImplementedError

            left = None
            right = None
            out_var  = None

            for value in node.values:
                right = left
                left = self.solidify_var(self.visit(value))
                if right is None:
                    continue
                self.solidify_var(right)

                out_var = self.make_implicit_var()
                self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([out_var]), comp_var, tuple([left, right])))
                left = out_var

            return out_var

        elif node_type is ast.BinOp:
            return self.handle_binop(node.op, self.visit(node.left), self.visit(node.right), node.lineno)

        elif node_type is ast.UnaryOp:
            comp_type = type(node.op)

            if comp_type is ast.UAdd:
                comp_var = uadd_var
            elif comp_type is ast.USub:
                comp_var = usub_var
            elif comp_type is ast.Not:
                comp_var = not_var
            elif comp_type is ast.Invert:
                comp_var = invert_var
            else:
                raise NotImplementedError

            out_var = self.make_implicit_var()
            self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([out_var]), comp_var, tuple([self.solidify_var(self.visit(node.operand))])))
            return out_var

        elif node_type is ast.Lambda:
            out_var = self.make_implicit_var()

            self.passthrough_var_frames.append({})

            arg_names = []
            for arg_node in node.args.args:
                arg_names.append(arg_node.arg)

            local_vars = {}
            self.function_frames.append(local_vars)
            self.block_frames.append(local_vars)
            statements, return_var, local_vars, args = self.build_block(None, node.body, arg_names=arg_names, from_expression=True)
            local_vars = self.function_frames.pop()
            local_vars = self.block_frames.pop()

            self.solidify_var(return_var)

            passthrough = self.passthrough_var_frames.pop()

            self.scope_statements[-1].append(("def", out_var, (tuple(args), (tuple(statements), tuple([return_var])))))

            return out_var

        elif node_type is ast.Attribute:
            ctx_type = type(node.ctx)

            if ctx_type is ast.Load:
                attr_var = self.new_var("#implicit#")
                self.scope_statements[-1].append(("prim", attr_var, node.attr))
                out_var = self.make_implicit_var()
                self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([out_var]), getattr_var, tuple([self.solidify_var(self.visit(node.value)), attr_var])))
                return out_var
            elif ctx_type is ast.Store:
                raise NotImplementedError
            elif ctx_type is ast.Del:
                raise NotImplementedError
            else:
                raise NotImplementedError

        elif node_type is ast.Subscript:
            ctx_type = type(node.ctx)

            if ctx_type is ast.Load:
                out_var = self.make_implicit_var()
                self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([out_var]), subscript_var, tuple([self.solidify_var(self.visit(node.value)), self.solidify_var(self.visit(node.slice))])))
                return out_var
            elif ctx_type is ast.Store:
                raise NotImplementedError
            elif ctx_type is ast.Del:
                raise NotImplementedError
            else:
                raise NotImplementedError

        elif node_type is ast.FormattedValue:
            value_var = self.visit(node.value)
            out_var = value_var

            if node.conversion != -1 or node.format_spec is None:
                if node.conversion == 115 or node.conversion == -1:
                    conversion_var = str_var
                elif node.conversion == 114:
                    conversion_var = repr_var
                elif node.conversion == 97:
                    conversion_var = ascii_var
                else:
                    raise NotImplementedError

                converted_var = self.make_implicit_var()
                self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([converted_var]), conversion_var, tuple([self.solidify_var(out_var)])))
                out_var = converted_var

            if node.format_spec is not None:
                formatted_var = self.make_implicit_var()
                self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([formatted_var]), format_var, tuple([self.solidify_var(out_var), self.solidify_var(self.visit(node.format_spec))])))
                out_var = formatted_var

            return out_var

        elif node_type is ast.JoinedStr:
            values = []
            for value in node.values:
                values.append(self.solidify_var(self.visit(value)))
            (statements, (church_var,)) = list_to_church(values, iter_var=self.make_implicit_var())
            self.scope_statements[-1].extend(statements)
            out_var = self.make_implicit_var()
            self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + node.lineno}", tuple([out_var]), self.solidify_var(church_var), tuple([self.solidify_var(self.handle_constant("")), prim_add_var])))
            return out_var

        elif node_type is ast.AsyncFunctionDef:
            raise NotImplementedError

        elif node_type is ast.Global:
            raise NotImplementedError

        elif node_type is ast.Await:
            print(ast.dump(node, indent=4))
            raise NotImplementedError

        elif node_type is ast.ClassDef:
            # raise NotImplementedError
            self._ni(node, "class definitions are not supported")
        elif node_type is ast.Delete:
            raise NotImplementedError
        elif node_type is ast.AsyncFor:
            raise NotImplementedError
        elif node_type is ast.With:
            raise NotImplementedError
        elif node_type is ast.AsyncWith:
            raise NotImplementedError
        elif node_type is ast.Raise:
            # raise NotImplementedError
            self._ni(node, "raise is not supported")
        elif node_type is ast.Try:
            raise NotImplementedError
        elif node_type is ast.Assert:
            raise NotImplementedError
        elif node_type is ast.Import:
            raise NotImplementedError
        elif node_type is ast.ImportFrom:
            raise NotImplementedError
        elif node_type is ast.Break:
            # raise NotImplementedError
            self._ni(node, "break is not supported")
        elif node_type is ast.Continue:
            # raise NotImplementedError
            self._ni(node, "continue is not supported")
        elif node_type is ast.Dict:
            # raise NotImplementedError
            self._ni(node, "dict literals are not supported")
        elif node_type is ast.Set:
            # raise NotImplementedError
            self._ni(node, "set literals are not supported")
        elif node_type is ast.ListComp:
            # raise NotImplementedError
            self._ni(node, "list comprehensions are not supported")
        elif node_type is ast.SetComp:
            raise NotImplementedError
        elif node_type is ast.DictComp:
            raise NotImplementedError
        elif node_type is ast.GeneratorExp:
            # raise NotImplementedError
            self._ni(node, "Generator expressions are not supported")
        elif node_type is ast.Yield:
            raise NotImplementedError
        elif node_type is ast.YieldFrom:
            raise NotImplementedError
        elif node_type is ast.Starred:
            # raise NotImplementedError
            self._ni(node, "Starred (unpacking) expressions are not supported")
        elif node_type is ast.Slice:
            raise NotImplementedError
        else:
            print(node_type)
            raise NotImplementedError

def bind_top_level_vars(bound_statements, handled_vars, epic_function):
    for name in epic_function.top_level_vars:
        (category, var) = epic_function.top_level_vars[name]
        if not name in epic_function.py_function.__globals__:
            raise NameError(name)

        if var in handled_vars:
            continue
        handled_vars.add(var)

        value = epic_function.py_function.__globals__[name]
        if isinstance(value, EpicFunction):
            bind_top_level_vars(bound_statements, handled_vars, value)
            bound_statements.append(value.epic_ast)
        elif isinstance(value, PythonFunction):
            bound_statements.append(value.epic_ast)
        else:
            bound_statements.append(("prim", var, wrap(value)))

def EPIC(annotated):
    if not inspect.isfunction(annotated):
        raise TypeError

    return EpicFunction(annotated)


@EPIC
def subscript(church, slice):
    def loop(state, elem):
        (index, result) = state
        next = index + 1
        return (next, elem) if index == slice else (next, result)
    _, result = church((0, None), loop)
    return result
subscript = subscript.epic_ast
subscript_var = subscript[1]
subscript_var.__dict__['name'] = "[]"

builtins_statements = {
    bool_var: ("prim", bool_var, bool_to_church),
    list_var: ("prim", list_var, list_to_church),
    eq_var: ("prim", eq_var, eq),
    noteq_var: ("prim", noteq_var, noteq),
    lt_var: ("prim", lt_var, lt),
    lte_var: ("prim", lte_var, lte),
    gt_var: ("prim", gt_var, gt),
    gte_var: ("prim", gte_var, gte),
    is_var: ("prim", is_var, is_),
    isnot_var: ("prim", isnot_var, isnot),
    in_var: ("prim", in_var, in_),
    notin_var: ("prim", notin_var, notin),
    and_var: ("prim", and_var, and_),
    or_var: ("prim", or_var, or_),
    uadd_var: ("prim", uadd_var, uadd),
    usub: ("prim", usub_var, usub),
    not_var: ("prim", not_var, not_),
    invert_var: ("prim", invert_var, invert),
    add_var: add,
    prim_add_var: ("prim", prim_add_var, prim_add),
    sub_var: ("prim", sub_var, sub),
    mult_var: ("prim", mult_var, mult),
    div_var: ("prim", div_var, div),
    floordiv_var: ("prim", floordiv_var, floordiv),
    mod_var: ("prim", mod_var, mod),
    pow_var: ("prim", pow_var, pow_),
    lshift_var: ("prim", lshift_var, lshift),
    rshift_var: ("prim", rshift_var, rshift),
    bitor_var: ("prim", bitor_var, bitor),
    bitxor_var: ("prim", bitxor_var, bitxor),
    bitand_var: ("prim", bitand_var, bitand),
    matmult_var: ("prim", matmult_var, matmult),
    format_var: ("prim", format_var, wrap(format)),
    str_var: ("prim", str_var, wrap(str)),
    repr_var: ("prim", repr_var, wrap(repr)),
    ascii_var: ("prim", ascii_var, wrap(ascii)),
    getattr_var: ("prim", getattr_var, wrap(getattr)),
    subscript_var: subscript,
}

if False:
    class TestClass:
        def __init__(self, val):
            self.val = val

        def test(self, other):
            return other + self.val

    #@EPIC
    def attr():
        a = TestClass(2)
        b = a.test(1)
        return b
    attr()


    #@EPIC
    def ex1(x, f):
        x = f(x)
        x = f(x)
        return x
    #ex1()


    #@EPIC
    def ex2(x, f):
        def g(x):
            x = f(f(x))
            return x
        x = g(x)
        return g(x)

    #@EPIC
    def exc1(x, f):
        return (f(x), f(x))



    #@EPIC
    def exc2():
        x, (y, z) = f()
        return x
    #exc2()

    #@EPIC
    def ex3(x, f):
        a = 0
        def g(x):
            nonlocal a
            x = f(x)
            x = f(x)
            a = a + 1
            return x
        return g



    ###@EPIC
    def demo_arith(init , incr):
        def three(init, incr):
            acc = incr(init)
            acc = incr(acc)
            acc = incr(acc)
            return acc
        # three = nli_nat_lit(3)

        # ret = nli_nat_add(three, three)
        ret = nli_nat_multiply(three, three)

        return ret(init, incr)



    ###@EPIC
    def nli_nat_multiply(a, b):
        def ret(init : W, incr):
            def a_incr(prev):
                return b(prev, incr)
            return a(init, a_incr)
        return ret


    ###demo_arith()

    ###@EPIC
    def r():
        x = 2
        x : int
        def a():
            return x
        x = 1
        return a()

    ###r()







    #@EPIC
    def arged(arg):
        return arg
    arged(1)

    #@EPIC
    def cond():
        b = True
        a = 0
        if b:
            a = 1
        else:
            #TODO: Don't unpack?
            pass
        return a
    cond()


    #@EPIC
    def cond_ret():
        b = True
        a = 0
        if b:
            return 1
        else:
            return a
    cond_ret()


    #@EPIC
    def cond_noop():
        b = True
        a = 0
        if b:
            pass
        else:
            pass
    cond_noop()

    #@EPIC
    def cond_combo():
        b = True
        a = 0
        if b:
            a = 2
            return 1
        else:
            return a
    cond_combo()

    #@EPIC
    def cond_inline():
        b = True
        a = 0
        c = 1 if b else a
        return c
    cond_inline()


    #@EPIC
    def cond_nest():
        b = True
        c = True
        a = 0
        if b:
            if c:
                a = 1
            else:
                a = 2
        else:
            pass
        return a
    cond_nest()

    #@EPIC
    #def cond_predeclare():
    #    return b
    #cond_predeclare()

    #@EPIC
    def loop_for():
        numbers = [1, 2, 3]
        a = 0
        for c in numbers:
            a = c
        return a
    loop_for()

    #@EPIC
    def loop_for_2x():
        numbers = [1, 2, 3]
        a = 0
        for c in numbers:
            for c in numbers:
                a += c
        return a
    loop_for_2x()

    #@EPIC
    def loop_for_if():
        numbers = [1, 2, 3]
        a = 0
        for c in numbers:
            if c < 3:
                a = c
            else:
                pass
        return a
    loop_for_if()

    #@EPIC
    def loop_for_ifm():
        numbers = [1, 3, 2, 1]
        a = 0
        for c in numbers:
            if c < 3:
                a += c
            else:
                pass
        return a
    loop_for_ifm()


    #@EPIC
    def loop_while():
        a = 0
        while a < 3:
            a += 1
        return a
    loop_while()


    #@EPIC
    def loop_overload():
        numbers = [1, 2, 3]
        a = 0
        for c in numbers:
            a += c
            while a % 2 == 1:
                a += 1
        return a
    loop_overload()


    #@EPIC
    def split_strt():
        l = ["a", "b", "c"]
        delim = "b"
        cur = ""
        self = ""
        for char in l:
            if char == delim:
                self += cur
                cur = ""
            else:
                cur += char
        self += cur
        return self
    split_strt()


    zee = 1

    #@EPIC
    def free():
        def x():
            u = zee
            def i():
                u = zee
                return zee
            return i()
        def y():
            u = zee
            def i():
                u = zee
                return zee
            return i()
        y()
        return x()

    free()

    #@EPIC
    def cond_walrus():
        a = 0
        c = 1 if (b := False) else a
        return c
    #cond_walrus()


    len = len

    #@EPIC
    def lambdara():
        a = lambda continent: len(continent) > 5
        return a("Hi")
    lambdara()

    #@EPIC
    def split():
        a = "Hey you!"
        b = a.split(" ")
        return b

    #@wrap
    async def do_simple_gpt(prompt : str):
        # print(">> GPT")
        stream = await OPENAI_ASYNC.chat.completions.create(
            model="gpt-3.5-turbo",
            # model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                # print(">>", repr(content))
                for c in content:
                    yield c
        # print("<< GPT")


    #@wrap
    def do_simple_gpt(prompt : str) -> list[chr]:
        return ["A", "B", "C"]

    #@EPIC
    def nli_list_cons(tl, hd):
        def ret(init, append):
            new_tl = tl(init, append)
            ret = append(new_tl, hd)
            return ret
        return ret

    #@EPIC
    def split_str(l, delim):
        def out(self, append):
            cur = []
            for char in l:
                if char == delim:
                    self = append(self, cur)
                    cur = []
                else:
                    cur = nli_list_cons(cur, char)
            self = append(self, cur)
            return self
        return out

    #@wrap
    async def f_print_char_py(dummy, x):
        assert dummy is None, dummy
        print(x, end = "")
        return None

    #@wrap
    async def foutput_print_char_py(dummy, x):
        assert dummy is None, dummy
        print(x, end = "")
        do_foutput(x)
        return None

    #@EPIC
    def foutput_printline(fd, l):
        fd = l(fd, f_print_char_py)
        fd = f_print_char_py(fd, "\n")
        return fd

    #@EPIC
    def to_str(l: list[chr]) -> str:
        return l("", add)

    #@EPIC
    def gpt():
        get_ds_raw = lambda continent: f"What are 10 cities that are popular tourist destinations in {continent}? Please give a list of the form \"CITY, COUNTRY (EXPLANATION)\", with no bullets, on separate lines, with no blank lines."
        get_ft = lambda dest: f"What are ten fun things I can do on vacation in {dest}?"


        def get_ds(continent):
            return split_str(list_to_church(do_simple_gpt(get_ds_raw(continent))), "\n")

        stdout = None

        dests = get_ds("Oceania")

        for dest in dests:
            # _ = foutput(stdout, dest)
            stdout = foutput_printline(stdout, dest)

            fun_thing = do_simple_gpt(get_ft(to_str(dest)))

            # _ = foutput(stdout, fun_thing)
            stdout = foutput_printline(stdout, fun_thing)

    #gpt()
