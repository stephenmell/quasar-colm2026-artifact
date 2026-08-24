"""Extract the 80 sampled BCP problems from the full corpus.

The BCP corpus (`decrypted.jsonl`, 2.0 GB -- it embeds gold, evidence and
negative documents per query) is not shipped.  Everything the runner needs is
the 80 rows named by datasets/bcp/indices.json, which this script copies,
byte-for-byte per row, into datasets/bcp/problems.jsonl (~224 MB).
run_bcp.py reads that file where upstream BCP/run.py reads decrypted.jsonl.

Usage:
    uv run python extract_bcp_problems.py CORPUS_JSONL [-o OUT_JSONL]

    CORPUS_JSONL   path to the full decrypted.jsonl
    -o             output path (default: datasets/bcp/problems.jsonl)
"""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
INDICES_PATH = os.path.join(HERE, "datasets", "bcp", "indices.json")
DEFAULT_OUT = os.path.join(HERE, "datasets", "bcp", "problems.jsonl")

def main():
    parser = argparse.ArgumentParser(description="Extract the sampled BCP problems.")
    parser.add_argument("corpus", help="path to the full decrypted.jsonl")
    parser.add_argument("-o", "--output", default=DEFAULT_OUT)
    args = parser.parse_args()

    with open(INDICES_PATH, "r") as f:
        wanted = {str(i) for i in json.load(f)}

    found = {}
    with open(args.corpus, "r", encoding="utf-8") as f:
        for line in f:
            qid = json.loads(line)["query_id"]
            if qid in wanted:
                assert qid not in found, f"duplicate query_id {qid}"
                found[qid] = line

    missing = wanted - found.keys()
    assert not missing, f"corpus is missing sampled query_ids: {sorted(missing)}"

    with open(args.output, "w", encoding="utf-8") as f:
        for qid in sorted(found, key=int):
            f.write(found[qid])
    print(f"wrote {len(found)} problems to {args.output}")

if __name__ == "__main__":
    main()
