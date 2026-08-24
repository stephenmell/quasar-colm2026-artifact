import ast
import textwrap

def wrap_expression(code: str, func_name: str = "execute_command") -> str:
    if not code:
        return f"def {func_name}():\n    pass\n"
    try:
        tree = ast.parse(code)
        last_expression = None
        if tree.body:
            last_node = tree.body[-1]
            if isinstance(last_node, ast.Expr):
                tree.body.pop()
                try:
                    last_expression = ast.unparse(last_node.value)
                except Exception as e:
                    last_expression = None
        try:
            remaining_expression = ast.unparse(tree).strip()
        except Exception as e:
            raise RuntimeError(f"Failed to regenerate code from AST: {e}") from e
        
        lines = [f"def {func_name}():\n"]
        if remaining_expression:
            lines.append(textwrap.indent(remaining_expression, "    "))
        elif not last_expression:
            lines.append("    pass")
        if last_expression:
            if remaining_expression:
                lines.append("")
            lines.append(f"    return {last_expression}")
        return "\n".join(lines) + "\n"
    
    except SyntaxError as e:
        raise RuntimeError(f"Failed to parse code: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to wrap expression: {e}") from e

if __name__ == "__main__":
    # Test case 1: Statement with expression
    s = """print("a")
5"""
    print("Test 1 - Statement with expression:")
    print(wrap_expression(s))
    print()

    # Test case 2: Empty code
    print("Test 2 - Empty code:")
    print(wrap_expression(""))
    print()

    # Test case 3: Single expression only
    print("Test 3 - Single expression:")
    print(wrap_expression("42 + 8"))
    print()

    # Test case 4: Multiple statements without expression
    print("Test 4 - Multiple statements:")
    print(wrap_expression("x = 10\ny = 20\nprint(x + y)"))
    print()

    # Test case 5: Custom function name
    print("Test 5 - Custom function name:")
    print(wrap_expression("'hello'.upper()", "my_func"))