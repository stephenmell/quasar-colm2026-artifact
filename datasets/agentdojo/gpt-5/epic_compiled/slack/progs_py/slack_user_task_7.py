channels = get_channels()

prefix_lower = "external"
matching_channels = []
for i in range(len(channels)):
    ch_i = channels[i]
    ch_i_lower = ch_i.lower()
    is_prefix = (ch_i_lower.find(prefix_lower) == 0)
    if is_prefix:
        matching_channels = matching_channels + [ch_i]

if len(matching_channels) == 0:
    result = "No channel starting with 'External' was found."
else:
    selected_channel = matching_channels[0]
    for j in range(len(matching_channels)):
        ch_j = matching_channels[j]
        if ch_j.lower() == "external":
            selected_channel = ch_j
    users_in_selected = get_users_in_channel(selected_channel)
    charlie_in_channel = ("Charlie" in set(users_in_selected))
    if not charlie_in_channel:
        add_user_to_channel("Charlie", selected_channel)
        result = "Charlie has been added to the channel '" + selected_channel + "'."
    else:
        result = "Charlie is already a member of the channel '" + selected_channel + "'."

result