import os
import sys
import traceback
import typeguard
from agentdojo.task_suite import TaskSuite
from agentdojo.task_suite.load_suites import get_suite

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
from utils import (
    read_file,
    wrap_expression
)
from AgentDojo.agentdojo_utils import (
    eval,
)
from AgentDojo.tools import (
    constants
)
from AgentDojo import (
    custom_translator
)
from opal_checker import (
    immut_common,
    immut_checker
)
from epic import (
    epics_syntax,
    epics_vipergpt
)

CUSTOM_SUFFIX = """
Generate Python code that answers the user's query. Do not print the result. Simply place the final expression on the last line. Here are some examples of user queries and correct programs:
"""

def get_gt_progs(kind, suite_name):
    gt_progs = {}
    gt_prompts = {}
    suite = get_suite("v1.2.1", suite_name)
    for tid, user_task in suite.user_tasks.items():
        tid_full = f"{suite.name}_{tid}"
        gt_path = os.path.join(
            "AgentDojo",
            "prompts",
            f"{kind}_examples",
            f"{tid_full}.py",
        )
        if os.path.exists(gt_path):
            gt_prog = read_file(gt_path)
            gt_progs[tid] = gt_prog
            gt_prompts[tid] = user_task.PROMPT
    return gt_progs, gt_prompts

def test_gt_progs(suite, exec_globals, gt_progs):
    utilities = []
    for tid, gt_prog in gt_progs.items():
        try:
            prog_wrapped = wrap_expression(gt_prog)
            # mutation_checker = immut_checker.AgentDojoMutationChecker(
            #     program=prog_wrapped,
            #     filename="dummy.py",
            #     exec_globals=exec_globals
            # )
            # mutation_checker.exec()
            _epics_expr, _var_names = epics_syntax.from_python_str(prog_wrapped, "dummy.py", translator = custom_translator)
            typeguard.check_type(_epics_expr, epics_syntax.Program)
            typeguard.check_type(_var_names, epics_syntax.VarNames)
            mappings = {
                k: custom_translator.wrap(v)
                for k, v in exec_globals.items()
            }
            epics_vipergpt.finalize(_epics_expr, [], mappings, _var_names, translator = custom_translator)
        except immut_common.IllegalMutationException as e:
            traceback.print_exception(e)
            assert False, f"Illegal syntax in gold program for task {tid} of suite {suite.name}."
        except Exception as e:
            traceback.print_exception(e)
            assert False, f"Compilation error in gold program for task {tid} of suite {suite.name}."
        user_task = suite.user_tasks[tid]
        utility, result, err, prog, dur = eval.eval_oneshot(suite, user_task, gt_prog)
        assert utility, f"[{suite.name}] Gold program for task {tid} did not achieve positive utility."
        utilities.append(utility)
    assert len(utilities) == len(gt_progs.values()), f"[{suite.name}] Some gold programs could not be evaluated."
    return True

def create_system_prompt(kind: str, task_suite : TaskSuite):
    suite_name = task_suite.name
    prompt_path = os.path.join(
        "AgentDojo",
        "prompts",
        f"{kind}",
        f"{suite_name}_prompt.txt",
    )
    prompt = read_file(prompt_path)
    prompt = prompt + CUSTOM_SUFFIX
    gt_progs, gt_prompts = get_gt_progs(kind, suite_name)
    for tid, gt_prog in gt_progs.items():
        prompt += f"\nQuery: {gt_prompts[tid]}\n```python\n{gt_prog}\n```"
    return prompt

if __name__ == "__main__":
    # for kind in ["epic_compiled", "python"]:
    for kind in ["epic_compiled"]:
        # for suite_name in ["workspace", "travel", "slack", "banking"]:
        for suite_name in ["workspace"]:
            gt_progs, _ = get_gt_progs(kind, suite_name)
            suite = get_suite("v1.2.1", suite_name)
            env = suite.load_and_inject_default_environment({})
            exec_globals = constants.SUITE_GLOBALS[suite_name](env, SET=False, ASYNC=False)
            test_gt_progs(suite, exec_globals, gt_progs)
    print(f"✅ All gold programs passed the test.")