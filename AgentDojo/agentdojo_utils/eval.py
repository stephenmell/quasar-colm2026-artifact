import time
import ast
from agentdojo.base_tasks import BaseUserTask
from agentdojo.task_suite import TaskSuite

from AgentDojo.tools import (
    constants,
)

NORETURN = object()
# from https://stackoverflow.com/questions/33908794/get-value-of-last-expression-in-exec-call
def exec_with_return(code: str, globals:dict, locals:dict):
    a = ast.parse(code)
    last_expression = None
    if a.body:
        if isinstance(a_last := a.body[-1], ast.Expr):
            last_expression = ast.unparse(a.body.pop())
        # elif isinstance(a_last, ast.Assign):
        #     last_expression = ast.unparse(a_last.targets[0])
        # elif isinstance(a_last, (ast.AnnAssign, ast.AugAssign)):
        #     last_expression = ast.unparse(a_last.target)
    exec(ast.unparse(a), globals, locals)
    if last_expression:
        return eval(last_expression, globals, locals)
    else:
        return NORETURN

def eval_oneshot(suite : TaskSuite, user_task : BaseUserTask, prog : str):
    # suite = suite_for_task(user_task)
    env = suite.load_and_inject_default_environment({})
    task_environment = user_task.init_environment(env)
    pre_environment = task_environment.model_copy(deep=True)

    exec_globals = constants.SUITE_GLOBALS[suite.name](env, SET=False, ASYNC=False)
    exec_locals = {}
    t_start = time.perf_counter()
    try:
        result = exec_with_return(prog, exec_globals, exec_locals)
        err = None
    except Exception as err_:
        result = None
        err = err_
    t_end = time.perf_counter()
    post_environment = task_environment.model_copy(deep=True)

    utility = user_task.utility(
        model_output=str(result),
        pre_environment=pre_environment,
        post_environment=post_environment,
    )

    return utility, result, err, prog, t_end - t_start