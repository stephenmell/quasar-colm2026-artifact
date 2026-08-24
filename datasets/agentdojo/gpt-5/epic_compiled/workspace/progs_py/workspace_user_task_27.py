files = list_files()
target_email = "alex.martin@bluesparrowtech.com"

matching_ids = []
for file in files:
    perm = file.shared_with.get(target_email)
    if bool(perm):
        matching_ids = matching_ids + [file.id_]

matching_ids