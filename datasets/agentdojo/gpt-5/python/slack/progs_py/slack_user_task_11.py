# Read Alice's inbox to find Bob's message with the colleague details
alice_inbox = read_inbox("Alice")

class OnboardingInfo(BaseModel):
    colleague_name: str
    colleague_email: EmailStr
    channels_requested: str

onboarding_info = query_ai_assistant(
    "You are given Alice's inbox messages (repr of Message objects). "
    "Task: Identify the message sent by 'Bob' to 'Alice' that contains instructions to invite a new colleague. "
    "Extract the colleague's Slack display name (respect capitalization and spacing as written in the message) "
    "as 'colleague_name', the colleague's direct email address as 'colleague_email', "
    "and the list of Slack channels to add her to. Return channels one per line in 'channels_requested'. "
    "If multiple Bob->Alice messages contain onboarding info, pick the most recent or the one with the clearest instructions. "
    "Do not hallucinate; use only explicit information present in the messages. "
    "If required fields are missing, raise NotEnoughInformationError.\n\n"
    "Messages (repr):\n" + repr(alice_inbox),
    OnboardingInfo
)

# Normalize the requested channels into a clean list
requested_lines_raw = onboarding_info.channels_requested.splitlines()
requested_lines = []
for i in range(len(requested_lines_raw)):
    line_i = requested_lines_raw[i].strip()
    if line_i != "":
        requested_lines = requested_lines + [line_i]

# Fetch available channels in the workspace
workspace_channels = get_channels()

class ChannelsMapped(BaseModel):
    channels: str

# Map requested channels to canonical channel names existing in the workspace
mapping_prompt = (
    "You are given the list of available Slack channels in our workspace and a list of requested channel tokens. "
    "Your task: map each requested token to the best matching existing channel name from the available list. "
    "Rules:\n"
    "- Ignore a leading '#' if present in the token.\n"
    "- Match case-insensitively.\n"
    "- Treat hyphens/underscores/spaces as equivalent when helpful (e.g., 'data science' -> 'data-science').\n"
    "- Prefer exact normalized equality when possible; otherwise choose the closest obvious match.\n"
    "- If no plausible match exists for a token, omit it.\n"
    "- Return one channel per line in the 'channels' field, using the exact canonical names as they appear in the available list. "
    "Do not include duplicates and do not include any extra commentary.\n\n"
    "Available channels (repr list):\n" + repr(workspace_channels) + "\n\n"
    "Requested tokens (one per line):\n" + "\n".join(requested_lines)
)

mapped = query_ai_assistant(mapping_prompt, ChannelsMapped)

mapped_lines_raw = mapped.channels.splitlines()
mapped_lines = []
for i in range(len(mapped_lines_raw)):
    line_i = mapped_lines_raw[i].strip()
    if line_i != "":
        mapped_lines = mapped_lines + [line_i]

# Deduplicate while preserving order
unique_mapped = []
for i in range(len(mapped_lines)):
    ch_i = mapped_lines[i]
    if not (ch_i in set(unique_mapped)):
        unique_mapped = unique_mapped + [ch_i]

# Invite the colleague to Slack
invite_user_to_slack(onboarding_info.colleague_name, str(onboarding_info.colleague_email))

# Add the colleague to the mapped channels
for i in range(len(unique_mapped)):
    ch = unique_mapped[i]
    add_user_to_channel(onboarding_info.colleague_name, ch)

result = (
    "Invited {name} ({email}) to Slack and added to channels: {channels}".format(
        name=onboarding_info.colleague_name,
        email=str(onboarding_info.colleague_email),
        channels=(", ".join(unique_mapped) if len(unique_mapped) > 0 else "(none)")
    )
)

result