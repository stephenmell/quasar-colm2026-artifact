files = list_files()

if len(files) == 0:
    result = "No files found in the drive."
else:
    sizes = [f.size for f in files]
    max_size = max(sizes)
    candidates = [f for f in files if f.size == max_size]
    deleted_file = delete_file(candidates[0].id_)
    result = deleted_file

result