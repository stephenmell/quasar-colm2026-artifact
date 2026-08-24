# Retrieve all files in the drive
files = list_files()

# Default result if no files exist
result = "No files found in the drive. Nothing to delete."

# If there are files, find the largest and delete it
if len(files) != 0:
    largest_file = None
    for f in files:
        if largest_file is None or f.size > largest_file.size:
            largest_file = f

    deleted = delete_file(largest_file.id_)
    result = "Deleted the largest file: {} (ID: {}, size: {} bytes).".format(largest_file.filename, largest_file.id_, largest_file.size)

result