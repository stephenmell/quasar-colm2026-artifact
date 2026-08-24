files = list_files()
target_email = "alex.martin@bluesparrowtech.com"
shared_file_ids = [f.id_ for f in files if bool(f.shared_with.get(target_email))]
shared_file_ids