import os
import sys
import re
import time
import traceback
import typeguard

from agentdojo.base_tasks import BaseUserTask
from agentdojo.task_suite import TaskSuite

#
from AgentDojo.agentdojo_utils import (
    create_prompt
)
from AgentDojo import (
    custom_translator
)
from utils import (
    get_openai_client,
    wrap_expression
)
from opal_checker import (
    immut_common,
    immut_checker
)
from epic import (
    epics_syntax,
    epics_vipergpt
)

def genprog_init_messages(kind: str, task_suite : TaskSuite, user_task : BaseUserTask):
    prompt = create_prompt.create_system_prompt(kind, task_suite)
    prompt += f"\nQuery: {user_task.PROMPT}"
    return [
        # {
        #     "role": "system",
        #     "content": create_prompt.create_system_prompt(task_suite),
        # },
        {
            "role": "user",
            "content": prompt,
        },
    ]
    
def genprog_python(messages, model_name):
    client = get_openai_client()
    response = client.chat.completions.create(
        model = model_name,
        messages=messages,
    )
    answer = response.choices[0].message.content
    assert answer is not None

    try:
        matches = re.findall(r"```python(.*)```", answer, re.DOTALL)
        assert len(matches) == 1
        return matches[0].strip(), answer
    except Exception:
        return answer, answer

def genprog_until_translate(
    kind: str,
    task_suite : TaskSuite, 
    exec_globals: dict,
    user_task : BaseUserTask, 
    model_name: str,
    regenerate: str = None,
    num_attempts: int = 1,
    trial: int = None,
) -> tuple[tuple[str, float], ...]:
    messages = genprog_init_messages(kind, task_suite, user_task)
    
    print("BEGIN GEN LOOP")
    # print(">> QUERY:", messages[1]["content"])
    print(">> QUERY:", user_task.PROMPT)
    outputs = [] # (prog, gen_time_s, error)
    t_start = time.perf_counter()
    for _ in range(num_attempts):
        prog, answer = genprog_python(messages, model_name)
        gen_time_s = time.perf_counter() - t_start
        # print(">> ASSISTANT:", answer)
        try:
            if regenerate is not None:
                prog_wrapped = wrap_expression(prog)
                _epics_expr, _var_names = epics_syntax.from_python_str(prog_wrapped, "dummy.py", translator = custom_translator)
                typeguard.check_type(_epics_expr, epics_syntax.Program)
                mappings = {
                    k: custom_translator.wrap(v)
                    for k, v in exec_globals.items()
                }
                epics_vipergpt.finalize(_epics_expr, [], mappings, _var_names, translator = custom_translator)
                # mutation_checker = immut_checker.AgentDojoMutationChecker(
                #     program=prog_wrapped,
                #     filename="dummy.py",
                #     exec_globals=exec_globals
                # )
                # mutation_checker.exec()
            outputs.append((prog, gen_time_s, None))
            break
        except immut_common.IllegalMutationException as e:
            traceback.print_exception(e)
            e_name, = e.args
            outputs.append((prog, gen_time_s, e_name))
            print(">> ILLEGAL MUTATION ERROR:", repr(e), str(e))
            messages.append({
                "role": "assistant",
                "content": answer,
            })
            messages.append({
                "role": "user",
                "content": f"The generated code could not be processed. Please regenerate correct Python code only. The error is: {str(e)}",
            })
        except RuntimeError as e:
            traceback.print_exception(e)
            outputs.append((prog, gen_time_s, "\n".join(traceback.format_exception(e))))
            print(">> WRAP ERROR:", repr(e), str(e))
            messages.append({
                "role": "assistant",
                "content": answer,
            })
            messages.append({
                "role": "user",
                "content": f"The generated code could not be processed. Please return valid Python code only. The error is: {str(e)}",
            })
        except Exception as e:
            traceback.print_exception(e)
            outputs.append((prog, gen_time_s, "\n".join(traceback.format_exception(e))))
            print(">> UNEXPECTED ERROR:", repr(e), str(e))
            messages.append({
                "role": "assistant",
                "content": answer,
            })
            messages.append({
                "role": "user",
                "content": f"An unexpected error occurred. Please regenerate correct Python code. Error: {str(e)}",
            })
    return tuple(outputs)