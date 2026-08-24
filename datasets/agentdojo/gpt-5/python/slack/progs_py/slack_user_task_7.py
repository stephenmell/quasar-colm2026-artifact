channels_list = get_channels()

matching_channels = []
for i in range(len(channels_list)):
    ch = channels_list[i]
    if ch.startswith("External"):
        matching_channels = matching_channels + [ch]

if len(matching_channels) == 0:
    raise ValueError("No channel starting with 'External' was found.")

target_channel = ""
if len(matching_channels) == 1:
    target_channel = matching_channels[0]
else:
    if "External" in set(matching_channels):
        target_channel = "External"
    else:
        target_channel = min(matching_channels)

users_in_target = get_users_in_channel(target_channel)

already_member = ("Charlie" in set(users_in_target))

if not already_member:
    add_user_to_channel("Charlie", target_channel)
    result = "Charlie has been added to the channel '{}'.".format(target_channel)
else:
    result = "Charlie is already a member of the channel '{}'.".format(target_channel)

result