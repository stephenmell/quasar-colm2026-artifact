import ast
import textwrap
def wrap_expression(code: str):
    try:
        a = ast.parse(code)
        last_expression = None
        if a.body:
            if isinstance(a_last := a.body[-1], ast.Expr):
                last_expression = ast.unparse(a.body.pop())
        
        ret = "def execute_command():\n"
        ret += textwrap.indent(ast.unparse(a), "    ")
        if last_expression:
            ret += "\n    return " + last_expression
        return ret
    except Exception as e:
        raise RuntimeError(f"Failed to wrap expression: {e}") from e

if __name__ == "__main__":
    s = """print("a")
5"""
    print(wrap_expression(s))