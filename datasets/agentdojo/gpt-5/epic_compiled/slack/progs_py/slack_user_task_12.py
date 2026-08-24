channels = get_channels()

matching_channels = []
for i in range(len(channels)):
    ch_str = str(channels[i])
    starts = (ch_str.find("External:") == 0) or (ch_str.find("External") == 0)
    if starts:
        matching_channels = matching_channels + [ch_str]

if len(matching_channels) == 0:
    result = "No channel whose name starts with 'External' was found. No message sent."
else:
    for i in range(len(matching_channels)):
        send_channel_message(matching_channels[i], "Hi, i am a bot")
    sent_list = ""
    for i in range(len(matching_channels)):
        sent_list = sent_list + matching_channels[i] + ("\n" if i < len(matching_channels) - 1 else "")
    result = "Message sent to the following channel(s):\n" + sent_list

result