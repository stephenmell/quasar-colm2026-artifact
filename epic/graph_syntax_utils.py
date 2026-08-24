from .graph_syntax import *

VarMapping = Dict[Var, VarIdent]

def add_statement_to_graph(g : TermGraph, vm : VarMapping, stmt : Statement) -> OperationIdent:
    match stmt:
        case "def", f, func:
            fvs : MutableSet[Var] = set()
            freevars_function(func, fvs)

            ident, f_new = g.add_def(f.name, func, {v : vm[v] for v in fvs})
            vm[f] = f_new

        case "call", name, outps, f, inps:
            ident, outps_new = g.add_call(name, tuple(outp.name for outp in outps), vm[f], tuple(vm[inp] for inp in inps))
            vm.update(zip(outps, outps_new))

        case "pack", outp, inps:
            ident, outp_new = g.add_pack(outp.name, tuple(vm[inp] for inp in inps))
            vm[outp] = outp_new

        case "unpack", outps, inp:
            ident, outps_new = g.add_unpack(tuple(outp.name for outp in outps), vm[inp])
            vm.update(zip(outps, outps_new))

        case "prim", outp, pyobj:
            ident, outp_new = g.add_prim(outp.name, pyobj)
            vm[outp] = outp_new

        case "task", name, outps, pyfuture:
            ident, outps_new = g.add_task(name, tuple(outp.name for outp in outps), pyfuture)
            vm.update(zip(outps, outps_new))

        case "loop", _outp, _init, _step:
            raise NotImplemented
        case x: assert False, x
    return ident

def graph_from_initial_term(func : Function) -> Tuple[TermGraph, IList[OperationIdent]]:
    g = TermGraph()
    vm : VarMapping = {}

    _, params = g.add_parameters(tuple(v.name for v in func[0]))
    vm.update(zip(func[0], params))

    real_statements : List[OperationIdent] = []

    for stmt in func[1][0]:
        ident = add_statement_to_graph(g, vm, stmt)
        real_statements.append(ident)

    _ = g.add_return(tuple(vm[o] for o in func[1][1]))

    return g, tuple(real_statements)

def graph_to_term(g : TermGraph) -> Function:
    params : Optional[IList[Var]] = None
    statements : List[Statement] = []
    rets : Optional[IList[Var]] = None

    def ident_as_var(v : VarIdent) -> Var:
        return Var(v, g.get_var_name(v))
    def idents_as_vars(vs : IList[VarIdent]) -> IList[Var]:
        return tuple(ident_as_var(v) for v in vs)
    def closure_as_subst(closure : Dict[Var, VarIdent]) -> Dict[Var, Var]:
        return {k: ident_as_var(v) for k, v in closure.items()}

    for ident, op in g.ops.items(): # pyright: ignore [reportPrivateUsage]
        match op:
            case "parameters",:
                assert params is None
                params = idents_as_vars(g.get_op_as_parameters(ident))
            case "return",:
                assert rets is None
                rets = idents_as_vars(g.get_op_as_return(ident))
            case "def", func:
                func2, f, closure = g.get_op_as_def(ident)
                assert func2 == func
                new_func = substitute_function(func, closure_as_subst(closure))
                statements.append(("def", ident_as_var(f), new_func))
            case "call", call_name:
                call_name2, outps, f, inps = g.get_op_as_call(ident)
                assert call_name == call_name2
                statements.append(("call", call_name, idents_as_vars(outps), ident_as_var(f), idents_as_vars(inps)))
            case "pack",:
                outp, inps = g.get_op_as_pack(ident)
                statements.append(("pack", ident_as_var(outp), idents_as_vars(inps)))
            case "unpack",:
                outps, inp = g.get_op_as_unpack(ident)
                statements.append(("unpack", idents_as_vars(outps), ident_as_var(inp)))
            case "prim", pyobj:
                outp, pyobj2 = g.get_op_as_prim(ident)
                assert pyobj is pyobj2
                statements.append(("prim", ident_as_var(outp), pyobj))
            case "task", call_name, pyfuture:
                call_name2, outps, pyfuture2 = g.get_op_as_task(ident)
                assert call_name == call_name2
                assert pyfuture is pyfuture2
                statements.append(("task", call_name, idents_as_vars(outps), pyfuture))

    assert params is not None
    assert rets is not None
    return params, (tuple(statements), rets)

def sp_graph(g : TermGraph):
    print("OPS")
    for ident, op in g.ops.items():
        print("  O |", ident, op)
        print("    B |", g.bind_pos_to_var[ident])
        print("    U |", g.use_pos_to_var[ident])
        
    print("VARS")
    for v, name in g.vars.items():
        print("  V |", v, name)
        print("    B |", g.bind_var_to_pos[v])
        print("    U |", g.use_var_to_pos[v])