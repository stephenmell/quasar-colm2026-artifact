"""Generate GQA Python programs from questions, via LLM (component 5).

Derived from upstream GQA/pipeline_gen_gqa.py.  Nondeterministic: gpt-5 is
sampled without a pinned temperature, so regenerated programs will not match
the committed progs_py.  The committed generation used:

    uv run python generate_gqa.py --num_samples 1000 -k epic_compiled \
        --model_name gpt-5 -p --regenerate checker --num_attempts 4

Needs OPENAI_API_KEY.  Writes progs_py/ and the items file under
datasets/gqa_val/<model_name>/.
"""

import os
from tqdm import tqdm
import traceback
import argparse
import time
import typeguard

from GQA.gqa_utils import (
    load_gqa,
    create_items_path
)
from epic import (
    imgpatch,
    imgpatch_test,
    epics_syntax,
    epics_vipergpt
)
from eval import (
    run_utils
)
from utils import (
    get_openai_client,
    read_file,
    write_file,
    write_json,
    response_to_py_program,
)
from opal_checker import (
    immut_common,
    immut_checker
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="GQA program generation."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="gqa",
        help="Directory containing dataset kinds (default: gqa)"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="val",
        choices=["train", "val", "test"],
        help="Dataset split to use (default: val)"
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        required=True,
        help="Number of samples to process (default: 1000)"
    )
    parser.add_argument(
        "-k", "--kind",
        type=str,
        required=True,
        choices=["epic_compiled", "python", "epic_direct"],
        help="Kind of generation"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="Name of the model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        default=False,
        help="Whether to overwrite existing predictions (default: False; upstream's rm -rf of the whole kind dir is dropped)"
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=str,
        default=None,
        help="Base datasets directory to write into (default: the in-tree datasets/)"
    )
    parser.add_argument(
        "--regenerate",
        type=str,
        default=None,
        choices=["None", "checker"],
        help="Whether to regenerate programs using the checker (default: None)"
    )
    parser.add_argument(
        "--num_attempts",
        type=int,
        default=1,
        help="Number of regeneration attempts for each example (default: 1)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2025,
        help="Random seed for reproducibility (default: 2025)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-e", "--epic", 
        action="store_true",
        default=False,
        help="Save as EPIC"
    )
    group.add_argument(
        "-p", "--python",
        action="store_true",
        default=False,
        help="Save as Python"
    )
    args = parser.parse_args()
    if args.regenerate == "None" and args.num_attempts != 1:
        parser.error("--num_attempts must be 1 when --regenerate is 'None'")
    if args.num_attempts < 1:
        parser.error("--num_attempts must be at least 1")
    return args

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    args = parse_args()
    base_dir = args.output_dir or os.path.join(HERE, "datasets")
    dataset_dir = os.path.join(base_dir, f"{args.dataset}_{args.split}", args.model_name)
    kind_dir = os.path.join(dataset_dir, args.kind)

    client = get_openai_client()
    
    lang = "epic" if args.epic else "py"
    prog_out_dir = os.path.join(kind_dir, f"progs_{lang}")
    os.makedirs(prog_out_dir, exist_ok=True)
    
    if lang == "py" and args.kind == "epic_compiled":
        print("Generating EPIC-compilable Python subset ...")
    elif lang == "py" and args.kind == "python":
        print("Generating unrestricted Python ...")
    elif lang == "epic" and args.kind == "epic_direct":
        print("Generating EPIC ...")
    else:
        raise ValueError(f"Invalid combination of kind {args.kind} and language {lang}")

    try:
        prompt = read_file(os.path.join(HERE, "GQA", "prompts", f"{args.kind}.txt"))
    except FileNotFoundError:
        print(f"❗️ Prompt file for kind {args.kind} not found. Please ensure the file exists in gqa/prompts/{args.kind}.txt")
        return

    print("Loading GQA dataset...")
    image_mappings, dataset_instructions, indices = load_gqa(
        split=args.split, 
        n=args.num_samples, 
        seed=args.seed
    )
    items = {}
    items_path = os.path.join(dataset_dir, create_items_path(args.split, args.num_samples, args.seed))
    
    print(f"Starting program generation for {len(indices)} examples using {args.model_name} ({lang})...\n")
    CONTEXT = run_utils.make_context(imgpatch_test, recording=False, sync=True, track_rounds=False)
    for i, idx in enumerate(tqdm(indices, desc="Generating")):
        if i >= args.num_samples:
            break
        item = dataset_instructions[idx]
        problem_id = item["id"]
        image_id = item["imageId"]
        question : str = item["question"]
        items[problem_id] = {
            "imageId": image_id,
            "question": question,
            "answer": item["answer"],
        }
        
        image = image_mappings.get(image_id)
        image = imgpatch.WrappedImage(image, image_id, CONTEXT)
        
        program_path = os.path.join(prog_out_dir, f"{problem_id}.prog")
        err_path = os.path.join(prog_out_dir, f"{problem_id}.err")
        if not args.rerun:
            if os.path.exists(program_path):
                print(f"⚠️ Skipping {problem_id} as the program file already exists.")
                continue
            if os.path.exists(err_path):
                print(f"⚠️ Skipping {problem_id} as the error file already exists.")
                continue
        
        program_prompt = question.join(prompt.split("{question}"))
        llm_messages = [{
            "role": "user",
            "content": [{"type": "text", "text": program_prompt}],
        }]
        kwargs = {
            "model": args.model_name,
            "messages": llm_messages,
        }
        if not args.model_name.startswith("gpt-5"):
            kwargs["temperature"] = 0.0

        print("\nBEGIN GEN LOOP")
        print(">> QUERY:", question)
        
        for attempt in range(args.num_attempts):
            response = client.chat.completions.create(**kwargs)
            model_output = response.choices[0].message.content.strip()
            print(">> ASSISTANT:", model_output)
            program = response_to_py_program(model_output, question)

            if args.regenerate is None or args.regenerate == "None":
                write_file(program_path, program)
                print(f"✅ Successfully saved program to {program_path}")
                break

            # mutation_checker = immut_checker.GQAMutationChecker(
            #     program=program,
            #     filename=f"{problem_id}.prog",
            #     image=image,
            #     ASYNC = False,
            # )
            
            try:
                # mutation_checker.exec()
                _epics_expr, _var_names = epics_syntax.from_python_str(program, "dummy.py")
                typeguard.check_type(_epics_expr, epics_syntax.Program)
                _epic_final = epics_vipergpt.finalize(_epics_expr, [image], epics_vipergpt.make_mappings(CONTEXT.METHODS), _var_names)
                
                write_file(program_path, program)
                print(f"✅ Successfully saved program to {program_path}")
                break
            except immut_common.IllegalMutationException as e:
                print(f">> ERROR on attempt {attempt}:", repr(e))
                e_name, = e.args
                write_file(err_path + f'.{attempt}', e_name)
                llm_messages.append({
                    "role": "assistant",
                    "content": model_output,
                })
                llm_messages.append({
                    "role": "user",
                    "content": f"The generated code could not be processed. Please regenerate correct {lang.upper()} code. Error: {str(e)}",
                })
                kwargs["messages"] = llm_messages
            except NotImplementedError as e:
                print(f">> ERROR on attempt {attempt}:", repr(e))
                traceback.print_exception(e)
                llm_messages.append({
                    "role": "assistant",
                    "content": model_output,
                })
                llm_messages.append({
                    "role": "user",
                    "content": f"The generated code is not supported! Please refer to the information on the custom interpreter. The error is: {str(e)}",
                })
                kwargs["messages"] = llm_messages
            except Exception as e:
                print(f">> ERROR on attempt {attempt}:", repr(e))
                traceback.print_exception(e)
                write_file(err_path + f'.{attempt}', "\n".join(traceback.format_exception(e)))
                llm_messages.append({
                    "role": "assistant",
                    "content": model_output,
                })
                llm_messages.append({
                    "role": "user",
                    "content": f"The generated code could not be processed. Please regenerate correct {lang.upper()} code. Error: {str(e)}",
                })
                kwargs["messages"] = llm_messages
    
    write_json(items_path, items)
    while not os.path.exists(items_path):
        time.sleep(1)
    print(f"\n✅ Finished processing {len(indices)} examples. Programs saved to {prog_out_dir}.")
                    
if __name__ == "__main__":
    main()