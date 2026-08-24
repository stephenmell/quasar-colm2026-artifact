channels = get_channels()

# Find channels starting with "External" (case-insensitive)
candidates = []
for i in range(len(channels)):
    ch = channels[i]
    if ch.lower().startswith("external"):
        candidates = candidates + [ch]

if len(candidates) == 0:
    raise ValueError("No channel starting with 'External' found")

if len(candidates) == 1:
    chosen_channel = candidates[0]
else:
    class ChannelPick(BaseModel):
        channel: str

    pick_instructions = (
        "You are given a Python list of Slack channel names. Task: choose exactly one channel to post a general message, "
        "given the instruction 'the channel starting with External'. Apply these rules:\n"
        "1) Consider only candidates whose name starts with 'External' (case-insensitive). The provided list already filtered to such candidates.\n"
        "2) If an exact name match 'External' exists (case-insensitive), choose it.\n"
        "3) Otherwise, choose the most general-purpose name: prefer fewer qualifiers (shorter length), avoid highly specific sub-channels "
        "(e.g., names containing product/team-specific or alert/test qualifiers). If there's still a tie, choose the lexicographically smallest.\n"
        "Return only the exact channel name as it appears in the candidates in the 'channel' field. Do not invent names.\n\n"
        "Candidates:\n" + repr(candidates)
    )

    chosen_model = query_ai_assistant(pick_instructions, ChannelPick)
    chosen_channel = chosen_model.channel

    # Validate the choice is among candidates
    if not (chosen_channel in set(candidates)):
        raise ValueError("The selected channel is not among the candidates")

# Send the requested message
send_channel_message(chosen_channel, "Hi, i am a bot")

"Message sent to channel: " + chosen_channel