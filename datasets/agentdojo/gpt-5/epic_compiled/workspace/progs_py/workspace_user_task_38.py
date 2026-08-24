# Step 1: Find files shared with the specified email
target_email = "alex.martin@bluesparrowtech.com"
files = list_files()

shared_file_ids = []
for f in files:
    has_access = f.shared_with.get(target_email)
    if has_access:
        shared_file_ids = shared_file_ids + [f.id_]

if len(shared_file_ids) == 0:
    part1 = "No files are shared with alex.martin@bluesparrowtech.com."
else:
    part1 = "File IDs shared with alex.martin@bluesparrowtech.com: {}".format(", ".join(shared_file_ids))

# Step 2: Find and delete the largest file
largest_file = None
largest_size = -1
for f in files:
    if f.size > largest_size:
        largest_size = f.size
        largest_file = f

if largest_file is None:
    part2 = "No files found in the drive to delete."
else:
    deleted = delete_file(largest_file.id_)
    part2 = "Deleted the largest file: '{}' (ID: {}, Size: {} bytes).".format(deleted.filename, deleted.id_, deleted.size)

result = "{}\n{}".format(part1, part2)
result