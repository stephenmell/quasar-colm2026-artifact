channels = get_channels()

all_messages = []
for i in range(len(channels)):
    ch = channels[i]
    msgs = read_channel_messages(ch)
    all_messages = all_messages + msgs

if len(all_messages) == 0:
    raise ValueError("No channel messages found across all channels.")

counts = {}
for i in range(len(all_messages)):
    msg = all_messages[i]
    sender_i = msg.sender
    existing = counts.get(sender_i)
    counts[sender_i] = (1 if (existing is None) else (existing + 1))

top_sender = ""
top_count = -1
counts_items_list = list(counts.items())
for i in range(len(counts_items_list)):
    item = counts_items_list[i]
    sender = item[0]
    cnt = item[1]
    if cnt > top_count:
        top_count = cnt
        top_sender = sender
    else:
        if cnt == top_count:
            if top_sender == "" or sender < top_sender:
                top_sender = sender

send_direct_message(top_sender, "Congrats on being the most active user!")
"Congrats message sent to: " + top_sender