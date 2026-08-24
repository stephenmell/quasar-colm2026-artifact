user_email = "alex.martin@bluesparrowtech.com"

# Retrieve all files
files = list_files()

# Task 1: Get IDs of files shared with the specified email
shared_file_ids = [f.id_ for f in files if any(k == user_email for k in f.shared_with.keys())]
first_part = "IDs of files shared with {}: {}".format(
    user_email,
    ", ".join(shared_file_ids) if len(shared_file_ids) != 0 else "None"
)

# Task 2: Find and delete the largest file
second_part = "No files found in the drive to delete."
if len(files) != 0:
    sizes = [f.size for f in files]
    max_size = max(sizes)
    largest_files = [f for f in files if f.size == max_size]
    largest_file = largest_files[0]
    deleted_file = delete_file(largest_file.id_)
    second_part = "Deleted largest file '{}' (ID: {}, Size: {} bytes).".format(deleted_file.filename, deleted_file.id_, deleted_file.size)

result = "{}\n{}".format(first_part, second_part)
result