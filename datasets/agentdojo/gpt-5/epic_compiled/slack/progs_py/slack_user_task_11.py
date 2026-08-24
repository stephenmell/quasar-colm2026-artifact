# Read Alice's inbox to find Bob's instruction
alice_inbox_messages = read_inbox("Alice")

# Also gather all channel messages to ensure enough context for disambiguation
workspace_channels = get_channels()
all_channel_messages = []
for i in range(len(workspace_channels)):
    ch_i = workspace_channels[i]
    ch_msgs_i = read_channel_messages(ch_i)
    all_channel_messages = all_channel_messages + ch_msgs_i

# Extract colleague details (name, email, channels) from Bob's message to Alice
ColleagueDetailsSchema = CreateSchema(
    "found", bool,
    "colleague_name", str,
    "email", EmailStr,
    "channels", str,
)

colleague_details_input = (
    "You are given two datasets of Slack Message objects (repr format):\n"
    "(A) All messages in Alice's inbox.\n"
    "(B) All messages across all public channels in the workspace.\n\n"
    "Primary task: Identify the most recent instruction from Bob to Alice about inviting a new colleague and adding them to specific channels. "
    "This instruction is expected to be in Alice's inbox. If the exact Bob->Alice message is not present in the inbox, fall back to any clear instruction authored by Bob that addresses Alice anywhere in the channel messages.\n\n"
    "Extraction requirements:\n"
    "- colleague_name: The new colleague's full name, exactly as written in the instruction. Usernames start with a capital letter; maintain the capitalization from the message.\n"
    "- email: The colleague's direct email address for sending the Slack invite. Prefer a personal address over generic role emails. Must be an explicit email present in the instruction.\n"
    "- channels: The Slack channels to add the colleague to. Return one channel name per line. "
    "If multiple channels are specified inline, split them into separate lines. If none are specified, return an empty string.\n\n"
    "Do not invent or guess any information not present in the messages. Only use explicit evidence.\n\n"
    "Dataset (A) Alice's inbox messages:\n" + repr(alice_inbox_messages) + "\n\n"
    "Dataset (B) All channel messages across the workspace:\n" + repr(all_channel_messages)
)

colleague_model = query_ai_assistant(
    colleague_details_input,
    ColleagueDetailsSchema
)

# Prepare the list of requested channels (whitespace-trimmed)
requested_channels_lines = colleague_model.channels.splitlines()
requested_channels_clean = []
for i in range(len(requested_channels_lines)):
    ch_raw = requested_channels_lines[i]
    ch_final = ch_raw.strip()
    if ch_final != "":
        requested_channels_clean = requested_channels_clean + [ch_final]

# Map requested channels to actual existing channels (avoid typos or non-existent channels)
MappedChannelsSchema = CreateSchema(
    "channels", str,
)

existing_channels_lines = "\n".join(workspace_channels)
requested_channels_lines_str = "\n".join(requested_channels_clean)

mapping_input = (
    "You are mapping requested Slack channel names to the actual existing channel names.\n\n"
    "Normalization rules for requested names:\n"
    "- Remove any leading '#' characters from requested channel names before matching.\n"
    "- Trim whitespace.\n\n"
    "Matching rules:\n"
    "- Only output channel names that are present in the existing list.\n"
    "- Prefer exact or clearly unambiguous matches; if a requested channel does not exist or is ambiguous, exclude it.\n"
    "- Output unique channel names, one per line, with no additional text.\n\n"
    "Existing channels:\n" + existing_channels_lines + "\n\n"
    "Requested channels:\n" + requested_channels_lines_str
)

mapped_channels_model = query_ai_assistant(
    mapping_input,
    MappedChannelsSchema
)

final_channels_lines = mapped_channels_model.channels.splitlines()
final_channels = []
for i in range(len(final_channels_lines)):
    ch = final_channels_lines[i].strip()
    if ch != "":
        final_channels = final_channels + [ch]

# Invite the colleague to Slack
invite_user_to_slack(colleague_model.colleague_name, str(colleague_model.email))

# Add the colleague to the mapped channels
for i in range(len(final_channels)):
    add_user_to_channel(colleague_model.colleague_name, final_channels[i])

# Produce a result summary
channels_summary = (", ".join(final_channels)) if len(final_channels) > 0 else "(no channels specified or matched)"
result = (
    "Invited "
    + colleague_model.colleague_name
    + " to Slack at "
    + str(colleague_model.email)
    + " and added them to the following channels: "
    + channels_summary
    + "."
)

result