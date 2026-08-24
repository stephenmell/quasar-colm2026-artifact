from .env import *
from .syntax import *
from .color_printing import *

color_list : Tuple[str, ...] = (
    # "black",
    # "white",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    # "cyan",
    # "light_grey",
    # "dark_grey",
    # "light_red",
    # "light_green",
    # "light_yellow",
    # "light_blue",
    # "light_magenta",
    "light_cyan",
)

import hashlib
def _str_to_int(s : str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % (10 ** 8)

def make_string_unique(s : str, i : int) -> ColoredString:
    color_id = (_str_to_int(s) + i)%len(color_list)
    num = i//len(color_list)
    color_str = color_list[color_id]
    s_numbered = s if num == 0 else f"{s}:{num}"
    return ((color_str, s_numbered),)

# def make_unique_var_names(vars : Iterable[Var]) -> Dict[Var, str]:
#     bucketed : Dict[str, List[Var]] = {}
#     for var in vars:
#         if var.name not in bucketed:
#             bucketed[var.name] = []
#         bucketed[var.name].append(var)
#     
#     ret : Dict[Var, str] = {}
#     for name, bucket in bucketed.items():
#         for i, var in enumerate(bucket):
#             ret[var] = make_string_unique(name, i)
#     return ret
# 
# def pretty_names_for_terms(exprs : Iterable[Term]) -> Dict[Var, str]:
#     all_bound_vars : MutableSet[Var] = set()
#     all_contextual_vars : MutableSet[Var] = set()
#     for expr in exprs:
#         bound_vars : MutableSet[Var] = set()
#         contextual_vars : MutableSet[Var] = set()
#         collect_vars(expr, bound_vars, contextual_vars)
#         # assert contextual_vars.isdisjoint(all_bound_vars)
#         # assert bound_vars.isdisjoint(all_contextual_vars)
#         all_bound_vars.update(bound_vars)
#         all_contextual_vars.update(contextual_vars)
#     names = make_unique_var_names(all_bound_vars)
#     return names


VarUniquifier : TypeAlias = Callable[[Var], ColoredString]
def var_name_uniquifier() -> VarUniquifier:
    bucketed : Dict[str, List[Var]] = {}
    ret : Dict[Var, ColoredString] = {}

    def another(var : Var) -> ColoredString:
        if var not in ret:
            if var.name not in bucketed:
                bucketed[var.name] = []
            i = len(bucketed[var.name])
            bucketed[var.name].append(var)
            ret[var] = make_string_unique(var.name, i)
        return ret[var]

    return another

def ppil_var_list(vars : Tuple[Var, ...], u : VarUniquifier) -> ColoredString:
    # return cs_join(" ", (cs_cat(u(p), ",") for p in vars)) # with trailing commas
    return cs_join(", ", (u(p) for p in vars))

def ppil_function(func : Function, func_var : Optional[Var] = None, u : Optional[VarUniquifier] = None) -> IndentedLines:
    if u is None: u = var_name_uniquifier()

    func_name = u(func_var) if func_var is not None else ""
    param_str = ppil_var_list(func[0], u)

    return (
        ("str", cs_cat("def ", func_name, "(", param_str, ")")),
        ("block", ppil_body(func[1], u)),
    )

def ppil_body(body : Body, u : Optional[VarUniquifier] = None) -> IndentedLines:
    if u is None: u = var_name_uniquifier()

    stmt_lines = (line for stmt in body[0] for line in ppil_statement(stmt, u))
    return_str = ppil_var_list(body[1], u)

    return (
        *stmt_lines,
        ("str", return_str),
    )

def ppil_statement(statement : Statement, u : Optional[VarUniquifier] = None) -> IndentedLines:
    if u is None: u = var_name_uniquifier()

    match statement:
        case "def", f, func:
            ret = ppil_function(func, f, u)
        case "call", name, outps, f, inps:
            outps_str = ppil_var_list(outps, u)
            inps_str = ppil_var_list(inps, u)
            ret = (("str", cs_cat(
                outps_str, " = [", name, "] ", u(f), "(", inps_str, ")"
            )),)
        case "pack", outp, inps:
            inps_str = ppil_var_list(inps, u)
            ret = (("str", cs_cat(
                u(outp), " = ", inps_str,
            )),)
        case "unpack", outps, inp:
            outps_str = ppil_var_list(outps, u)
            ret = (("str", cs_cat(
                outps_str, " = ", u(inp),
            )),)
        case "prim", outp, pyobj:
            ret = (("str", cs_cat(
                u(outp), " = prim ", repr(pyobj),
            )),)
        case "task", name, outps, pyfuture:
            outps_str = ppil_var_list(outps, u)
            ret = (("str", cs_cat(
                outps_str, " = [", name, "] future ", hex(id(pyfuture))
            )),)
        case "loop", outp, init, step:
            ret = (("str", cs_cat(
                u(outp), " = loop ", u(init), " ", u(step),
            )),)
        case x: assert False, x
    return ret

def statement_vars_mut(stmt : Statement, out_vars : MutableSet[Var]):
    match stmt:
        case "def", f, _func:
            assert f not in out_vars, f
            out_vars.add(f)
        case "call", _name, outps, _f, _inps:
            for outp in outps:
                assert outp not in out_vars, outp
                out_vars.add(outp)
        case "pack", outp, _inps:
            assert outp not in out_vars, outp
            out_vars.add(outp)
        case "unpack", outps, _inp:
            for outp in outps:
                assert outp not in out_vars, outp
                out_vars.add(outp)
        case "prim", outp, _pyobj:
            assert outp not in out_vars, outp
            out_vars.add(outp)
        case "task", _name, outps, _pyfuture:
            for outp in outps:
                assert outp not in out_vars, outp
                out_vars.add(outp)
        case "loop", outp, _init, _step:
            assert outp not in out_vars, outp
            out_vars.add(outp)
        case x: assert False, x

def statement_vars(stmt : Statement) -> FrozenSet[Var]:
    ret : MutableSet[Var] = set()
    statement_vars_mut(stmt, ret)
    return frozenset(ret)

def statements_vars(stmts : Tuple[Statement, ...]) -> FrozenSet[Var]:
    ret : MutableSet[Var] = set()
    for stmt in stmts:
        statement_vars_mut(stmt, ret)
    return frozenset(ret)

def stepping_pair_to_aligned_statements(
    before_stmts : Tuple[Statement, ...],
    after_stmts : Tuple[Statement, ...],
) -> Tuple[Tuple[Optional[Statement], Optional[Statement]], ...]:
    all_before_vars : FrozenSet[Var] = statements_vars(before_stmts)
    all_after_vars : FrozenSet[Var] = statements_vars(after_stmts)

    before_stmt_idx = 0
    after_stmt_idx = 0
    ret : List[Tuple[Optional[Statement], Optional[Statement]]] = []
    while True:
        before_stmt = before_stmts[before_stmt_idx] if before_stmt_idx < len(before_stmts) else None
        after_stmt = after_stmts[after_stmt_idx] if after_stmt_idx < len(after_stmts) else None

        if before_stmt is None and after_stmt is None:
            break

        before_vars : FrozenSet[Var] = statement_vars(before_stmt) if before_stmt is not None else frozenset()
        after_vars : FrozenSet[Var]  = statement_vars(after_stmt) if after_stmt is not None else frozenset()

        if before_vars == after_vars:
            # we've found the same statement in both terms
            ret.append((before_stmt, after_stmt))
            before_stmt_idx += 1
            after_stmt_idx += 1
        elif not before_vars.issubset(all_after_vars):
            assert before_vars.intersection(all_after_vars) == frozenset(), ("only some bound variables are missing", before_vars, all_after_vars)
            # the before statement is missing from the after term, and thus was deleted
            ret.append((before_stmt, None))
            before_stmt_idx += 1
        elif not after_vars.issubset(all_before_vars):
            assert after_vars.intersection(all_before_vars) == frozenset(), ("only some bound variables are missing", after_vars, all_before_vars)
            # the after statement is missing from the before term, and thus was inserted
            ret.append((None, after_stmt))
            after_stmt_idx += 1
        elif len(before_vars) == 0:
            # the before statement is an empty unpack
            ret.append((before_stmt, None))
            before_stmt_idx += 1
        elif len(after_vars) == 0:
            # the after statement is an empty unpack
            ret.append((None, after_stmt))
            after_stmt_idx += 1
        else:
            print("before vars")
            for v in before_vars:
                print("\t", v)
            print("after vars")
            for v in after_vars:
                print("\t", v)
            print("before stmts")
            for s in before_stmts:
                print("\t", statement_vars(s))
            print("after stmts")
            for s in after_stmts:
                print("\t", statement_vars(s))
            assert False, (before_vars, after_vars, all_before_vars, all_after_vars)
    
    return tuple(ret)


def stepping_pair_to_indented_lines(
    before : Function,
    after : Function,
    func_var : Optional[Var] = None,
    u : Optional[VarUniquifier] = None,
) -> Tuple[IndentedLines, IndentedLines]:
    before_inputs, (before_statements, before_outputs) = before
    after_inputs, (after_statements, after_outputs) = after

    if u is None: u = var_name_uniquifier()
    body_before : List[IndentedLinesItem] = []
    body_after : List[IndentedLinesItem]  = []
    
    func_name = u(func_var) if func_var is not None else ""
    before_param_str = ppil_var_list(before_inputs, u)
    after_param_str = ppil_var_list(after_inputs, u)

    header_before = ("str", cs_cat("def ", func_name, "(", before_param_str, ")"))
    header_after = ("str", cs_cat("def ", func_name, "(", after_param_str, ")"))

    for before_stmt, after_stmt in stepping_pair_to_aligned_statements(before_statements, after_statements):
        before_lines : IndentedLines = ppil_statement(before_stmt, u) if before_stmt is not None else ()
        after_lines : IndentedLines = ppil_statement(after_stmt, u) if after_stmt is not None else ()
        before_lines_padded, after_lines_padded = il_pair_pad_end(before_lines, after_lines)
        body_before.extend(before_lines_padded)
        body_after.extend(after_lines_padded)

    before_return_str = ppil_var_list(before_outputs, u)
    after_return_str = ppil_var_list(after_outputs, u)

    body_before.append(("str", before_return_str))
    body_after.append(("str", after_return_str))

    return (
        header_before,
        ("block", tuple(body_before)),
    ), (
        header_after,
        ("block", tuple(body_after)),
    )
