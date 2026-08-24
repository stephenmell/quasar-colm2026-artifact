import os
import datetime
import csv
import json
import dataclasses

def get_filepaths_from_dirs(dirs, extension):
    filepaths = []
    for dir in dirs:
        if os.path.isdir(dir):
            filepaths.extend(
                os.path.join(dir, f) for f in os.listdir(dir) if f.endswith(extension)
            )
    return filepaths

def create_dir_w_timestamp(dir_prefix):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = f"{dir_prefix}_{timestamp}"
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

# ==============================

def write_csv(filepath, data, header):
    with open(filepath, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)

def write_dicts_to_csv(filepath, data, fieldnames=None):
    if fieldnames is None:
        fieldnames = list(data[0].keys())  # Infer from first dict
    with open(filepath, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def read_file(filepath):
    with open(filepath, "r") as f:
        data = f.read()
    return data

def write_file(filepath, data):
    with open(filepath, "w") as f:
        f.write(data)

def read_jsonl(filepath):
    data = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def write_jsonl(filepath, data):
    with open(filepath, "w") as f:
        for data_entry in data:
            f.write(json.dumps(data_entry, cls=EnhancedJSONEncoder) + "\n")

def read_json(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, cls=EnhancedJSONEncoder)

def write_epics(filepath, data):
    from epic.epics_syntax import to_str
    filepath = os.path.splitext(filepath)[0] + ".epics"
    with open(filepath, "w") as f:
        f.write(to_str(data))

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            print(o)
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            if type(o) is frozenset or type(o) is set or type(o) is tuple:
                return list(o)
            return super().default(o)