files = list_files()

if len(files) == 0:
    raise ValueError("No files found in the cloud drive.")

largest_index = 0
for i in range(1, len(files)):
    if files[i].size > files[largest_index].size:
        largest_index = i

files[largest_index].filename