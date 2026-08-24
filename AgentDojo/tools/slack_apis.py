import agentdojo.default_suites.v1.tools.slack as slack
import agentdojo.default_suites.v1.tools.web as web

TOOLS = {
        "get_channels": slack.get_channels,
        "add_user_to_channel": slack.add_user_to_channel,
        "read_channel_messages": slack.read_channel_messages,
        "read_inbox": slack.read_inbox,
        "send_direct_message": slack.send_direct_message,
        "send_channel_message": slack.send_channel_message,
        "get_users_in_channel": slack.get_users_in_channel,
        "invite_user_to_slack": slack.invite_user_to_slack,
        "remove_user_from_slack": slack.remove_user_from_slack,
        "get_webpage": web.get_webpage,
        "post_webpage": web.post_webpage,
        "query_ai_assistant": None,
}