#!/usr/bin/env python

import ast
import inspect
import pprint
import asyncio
from eval import rewrap

class PatchPython(ast.NodeTransformer):
    def __init__(self, func_ast, func_filename, func_lineno):
        self.filename = func_filename
        self.lineno = func_lineno

        self.passthrough_name_scopes = []
        self.python_scope_boundaries = []

        self.loop_nesting = 0
        self.if_nesting = 0
        self.returning = False
        self.returned = False

        self.ast = self.visit(func_ast)

    def source(self):
        return ast.unparse(self.ast)

    def register_passthrough(self, name):
        passthrough = self.passthrough_name_scopes[-1]
        if name not in passthrough:
            passthrough.add(name)

    def get_function_passthrough(self):
        names = set()
        for passthrough in reversed(self.passthrough_name_scopes):
            names.update(passthrough)
            if passthrough is self.python_scope_boundaries[-1]:
                break
        return names

    def propagate_passthrough(self, local, parent):
        for name in local:
            if not name in parent:
                parent.add(name)

    def visit_lhs(self, node, passthrough=True):
        node_type = type(node)

        if node_type is ast.Tuple:
            for elt in node.elts:
                self.visit_lhs(elt, passthrough=passthrough)
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
        else:
            print(node_type)
            raise NotImplementedError

    def handle_binop(self, op, left, right, lineno):
        comp_type = type(op)

        if comp_type is ast.Add:
            comp_var = add_var
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

        self.scope_statements[-1].append(("call", f"{self.filename}:{self.lineno + lineno}", tuple([out_var]), comp_var, tuple([self.solidify_var(left), self.solidify_var(right)])))
        return out_var

    def visit_Module(self, node):
        passthrough = set()
        self.python_scope_boundaries.append(passthrough)
        self.passthrough_name_scopes.append(passthrough)

        module = self.generic_visit(node)

        passthrough = self.python_scope_boundaries.pop()
        passthrough = self.passthrough_name_scopes.pop()

        return module

    def visit_FunctionDef(self, node):
        loop_nesting = self.loop_nesting
        self.loop_nesting = 0

        if_nesting = self.if_nesting
        self.if_nesting = 0

        returned = self.returned
        self.returned = False

        args = set()
        for arg_node in node.args.args:
            self.register_passthrough(arg_node.arg)
            args.add(arg_node.arg)

        passthrough = set()
        self.python_scope_boundaries.append(passthrough)
        self.passthrough_name_scopes.append(passthrough)

        function = self.generic_visit(node)

        self.if_nesting = if_nesting
        self.returned = returned

        self.loop_nesting = loop_nesting

        passthrough = self.passthrough_name_scopes.pop()
        passthrough = self.python_scope_boundaries.pop()

        function.body = [ast.Assign(targets=[ast.Name(name, ctx=ast.Store())], value=ast.Constant(None), lineno=node.lineno) for name in sorted(list(passthrough.difference(args)))] + function.body

        return function

    def visit_Assign(self, node):
        assign = self.generic_visit(node)
        for target in reversed(node.targets):
            self.visit_lhs(target)
        return assign

    def visit_AnnAssign(self, node):
        #node.annotation
        #node.simple
        assign = self.generic_visit(node)
        if not node.simple:
            self.visit_lhs(node.target)
        return assign

    def visit_AugAssign(self, node):
        #assign = self.handle_binop(node.op, node.target.id, self.visit(node.value), node.lineno)
        assign = self.generic_visit(node)
        self.visit_lhs(node.target)
        return assign

    def visit_NamedExpr(self, node):
        assign = self.generic_visit(node)
        self.visit_lhs(node.target)
        return assign

    def visit_Return(self, node):
        if self.loop_nesting > 0:
            raise NotImplementedError
        return_node = self.generic_visit(node)
        if self.if_nesting  > 0:
            self.returning = True
            self.returned = self.returned or True
            return ast.Return(value=ast.Tuple(elts=[return_node.value], ctx=ast.Load()))
        else:
            return return_node

    def visit_Name(self, node):
        return node

    def visit_If(self, node):
        statements = []

        test_node = self.visit(node.test)

        if_nesting = self.if_nesting
        self.if_nesting += 1

        returning = self.returning
        self.returning = False

        self.passthrough_name_scopes.append(set())
        body_var = "_if"
        body_statements = [self.visit(child) for child in node.body]
        body_passthrough = self.passthrough_name_scopes.pop()
        body_return = self.returning

        self.returning = False

        if len(node.orelse) > 0:
            self.passthrough_name_scopes.append(set())
            else_var = "_else"
            else_statements = [self.visit(child) for child in node.orelse]
            else_passthrough = self.passthrough_name_scopes.pop()
            else_return = self.returning
        else:
            else_var = None
            else_passthrough = set()
            else_return = False

        self.returning = returning
        self.if_nesting = if_nesting

        if body_return != else_return:
            raise NotImplementedError

        function_passthrough = self.get_function_passthrough()

        passthrough = body_passthrough.union(function_passthrough, body_passthrough, else_passthrough)
        #passthrough = body_passthrough.intersection(else_passthrough).union(function_passthrough.intersection(body_passthrough), function_passthrough.intersection(else_passthrough))
        passthrough = sorted(list(passthrough))

        parent_passthrough = self.passthrough_name_scopes[-1]

        self.propagate_passthrough(body_passthrough, parent_passthrough)
        self.propagate_passthrough(else_passthrough, parent_passthrough)

        return_var = "_return"

        # if name in function_passthrough else ast.Constant(None)
        passthough_pack = ast.Tuple(elts=[ast.Name(name, ctx=ast.Store()) for name in passthrough], ctx=ast.Store())
        passthough_args = ast.arguments(posonlyargs=[], args=[ast.arg(arg=name) for name in passthrough], kwonlyargs=[], kw_defaults=[], defaults=[])

        if self.returned:
            passthough_unpack = ast.Tuple(elts=[ast.Name(return_var, ctx=ast.Store())], ctx=ast.Store())
            return_node = ast.Return(value=ast.Tuple(elts=[ast.Name(return_var, ctx=ast.Load())], ctx=ast.Load()))
        else:
            passthough_unpack = ast.Tuple(elts=[ast.Name(name, ctx=ast.Store()) for name in passthrough], ctx=ast.Store())
            return_node = ast.Return(value=ast.Tuple(elts=[ast.Name(name, ctx=ast.Load()) for name in passthrough], ctx=ast.Load()))

        if not body_return:
            body_statements.append(return_node)

        statements.append(ast.FunctionDef(name=body_var, args=passthough_args, body=body_statements, decorator_list=[], lineno=node.lineno))

        if else_var is not None:
            if not else_return:
                else_statements.append(return_node)
            statements.append(ast.FunctionDef(name=else_var, args=passthough_args, body=else_statements, decorator_list=[], lineno=node.lineno))

        if_var = "if_stmt"

        statements.append(ast.Assign(targets=[passthough_unpack], value=ast.Call(
            func=ast.Name(id=if_var, ctx=ast.Load()),
            args=[
                ast.Name(id=body_var, ctx=ast.Load()),
                ast.Name(id=else_var, ctx=ast.Load()) if else_var is not None else ast.Constant(None),
                test_node,
                passthough_pack
            ],
            keywords=[]
        ), lineno=node.lineno))

        if self.returned and self.if_nesting == 0:
            statements.append(ast.Return(value=ast.Name(return_var, ctx=ast.Load())))

        return statements

    def visit_IfExp(self, node):
        return self.generic_visit(node)

    def visit_For(self, node):
        statements = []

        iter_node = self.visit(node.iter)

        loop_nesting = self.loop_nesting
        self.loop_nesting += 1

        self.passthrough_name_scopes.append(set())

        loop_var = "_for"
        loop_statements = [self.visit(child) for child in node.body]

        self.loop_nesting = loop_nesting

        loop_passthrough = self.passthrough_name_scopes.pop()

        function_passthrough = self.get_function_passthrough()

        passthrough = loop_passthrough.union(function_passthrough)
        #passthrough = loop_passthrough.intersection(function_passthrough)
        passthrough = sorted(list(passthrough))

        parent_passthrough = self.passthrough_name_scopes[-1]

        self.propagate_passthrough(loop_passthrough, parent_passthrough)

        passthough_pack = ast.Tuple(elts=[ast.Name(name, ctx=ast.Load()) for name in passthrough], ctx=ast.Load())
        passthough_unpack = ast.Tuple(elts=[ast.Name(name, ctx=ast.Store()) for name in passthrough], ctx=ast.Store())

        if type(node.target) is not ast.Name:
            raise NotImplementedError
        passthough_args = ast.arguments(posonlyargs=[], args=[ast.arg(arg=node.target.id)] + [ast.arg(arg=name) for name in passthrough], kwonlyargs=[], kw_defaults=[], defaults=[])

        return_node = ast.Return(value=ast.Tuple(elts=[ast.Name(name, ctx=ast.Load()) for name in passthrough], ctx=ast.Load()), ctx=ast.Load())
        loop_statements.append(return_node)

        statements.append(ast.FunctionDef(name=loop_var, args=passthough_args, body=loop_statements, decorator_list=[], lineno=node.lineno))

        for_var = "for_stmt"

        statements.append(ast.Assign(targets=[passthough_unpack], value=ast.Call(
            func=ast.Name(id=for_var, ctx=ast.Load()),
            args=[
                ast.Name(id=loop_var, ctx=ast.Load()),
                iter_node,
                passthough_pack
            ],
            keywords=[]
        ), lineno=node.lineno))

        for sub_node in node.orelse:
            raise NotImplementedError

        return statements

    def visit_While(self, node):
        raise NotImplementedError

    def visit_Compare(self, node):
        return self.generic_visit(node)
        left = self.visit(node.left)
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

        return node

    def visit_BoolOp(self, node):
        comp_type = type(node.op)

        if comp_type is ast.And:
            comp_var = "and_expr"
        elif comp_type is ast.Or:
            comp_var = "or_expr"
        else:
            raise NotImplementedError

        left = None
        right = None

        for value in reversed(node.values):
            right = left
            left = self.generic_visit(value)
            if right is None:
                continue

            left = ast.Call(
                func=ast.Name(id=comp_var, ctx=ast.Load()),
                args=[
                    left,
                    right
                ],
                keywords=[]
            )

        return left

    def visit_BinOp(self, node):
        return self.generic_visit(node)
        return self.handle_binop(node.op, self.visit(node.left), self.visit(node.right), node.lineno)

    def visit_UnaryOp(self, node):
        comp_type = type(node.op)

        if comp_type is ast.Not:
            comp_var = "not_expr"
        else:
            return self.generic_visit(node)

        return ast.Call(
            func=ast.Name(id=comp_var, ctx=ast.Load()),
            args=[
                self.generic_visit(node.operand)
            ],
            keywords=[]
        )

        if comp_type is ast.UAdd:
            comp_var = uadd_var
        elif comp_type is ast.USub:
            comp_var = usub_var
        elif comp_type is ast.Not:
            comp_var = not_var
        elif comp_type is ast.Invert:
            comp_var = invert_var

    def visit_Lambda(self, node):
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        raise NotImplementedError

    def visit_Nonlocal(self, node):
        raise NotImplementedError

    def visit_Global(self, node):
        raise NotImplementedError

    def visit_Await(self, node):
        raise NotImplementedError

    def visit_ClassDef(self, node):
        raise NotImplementedError
    def visit_Delete(self, node):
        raise NotImplementedError
    def visit_AsyncFor(self, node):
        raise NotImplementedError
    def visit_With(self, node):
        raise NotImplementedError
    def visit_AsyncWith(self, node):
        raise NotImplementedError
    def visit_Raise(self, node):
        raise NotImplementedError
    def visit_Try(self, node):
        raise NotImplementedError
    def visit_Assert(self, node):
        raise NotImplementedError
    def visit_Import(self, node):
        raise NotImplementedError
    def visit_ImportFrom(self, node):
        raise NotImplementedError
    def visit_Break(self, node):
        raise NotImplementedError
    def visit_Continue(self, node):
        raise NotImplementedError
    # def visit_Dict(self, node):
    #     raise NotImplementedError
    # def visit_Set(self, node):
    #     raise NotImplementedError
    def visit_ListComp(self, node):
        raise NotImplementedError
    def visit_SetComp(self, node):
        raise NotImplementedError
    def visit_DictComp(self, node):
        raise NotImplementedError
    def visit_GeneratorExp(self, node):
        raise NotImplementedError
    def visit_Yield(self, node):
        raise NotImplementedError
    def visit_YieldFrom(self, node):
        raise NotImplementedError
    def visit_Starred(self, node):
        raise NotImplementedError
    def visit_Slice(self, node):
        raise NotImplementedError

import os
import sys
import traceback
import pathlib
import time
import argparse

#
from utils import (
    get_filepaths_from_dirs,
    read_file,
    write_file
)

KINDS_DIR = os.path.join(os.path.dirname(__file__), f"../datasets/gqa")

parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--dir',
    help='Target dir',
    required = True
)
parser.add_argument(
    '-s', '--suffix',
    help='Source program suffix ("py" vs "prog")',
    required = True
)
parser.add_argument(
    '-r', '--rewrap',
    action="store_true",
)
args = parser.parse_args()

# Directory for vipergpt programs
DIRNAME = args.dir
SUFFIX = args.suffix
REWRAP = args.rewrap

# Load vipergpt programs
filepaths = get_filepaths_from_dirs([f"{DIRNAME}/progs_py"], extension=f".{SUFFIX}")

TRANS_DIRNAME = f"{DIRNAME}/progs_set"
os.makedirs(TRANS_DIRNAME, exist_ok=True)

results = []
for i, fn_path in enumerate(filepaths, 1):
    filename = os.path.basename(fn_path)

    #if filename not in ["08619158.prog"]:
    #    continue

    print(f"[{i}/{len(filepaths)}] Processing: {filename}")

    filename_no_ext = os.path.splitext(filename)[0]

    trans_filepath = os.path.join(TRANS_DIRNAME, f"{filename_no_ext}.prog")
    err_filepath = os.path.join(TRANS_DIRNAME, f"{filename_no_ext}.err")

    py_code = read_file(fn_path)
    if REWRAP:
        py_code = rewrap.wrap_expression(py_code)

    try:
        print(f"    Translating {filename} to Set Python ...")
        write_file(trans_filepath, PatchPython(ast.parse(py_code, mode='exec', type_comments=True), filename, 0).source())

        try:
            os.remove(err_filepath)
        except FileNotFoundError:
            pass
    except Exception as e:
        print(f"        Failed to translate {filename} to Set Python: {e}")
        write_file(err_filepath, "\n".join(traceback.format_exception(e)))
        traceback.print_exc()
        try:
            os.remove(trans_filepath)
        except FileNotFoundError:
            pass
