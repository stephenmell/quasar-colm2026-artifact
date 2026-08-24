from AgentDojo.tools import (
    workspace_apis,
    travel_apis,
    banking_apis,
    slack_apis,
    suite_common,
)

TOOL_APIS = {
    "workspace": workspace_apis,
    "travel": travel_apis,
    "banking": banking_apis,
    "slack": slack_apis,
}

SUITE_GLOBALS = {
    "workspace": suite_common.get_globals_for_env(workspace_apis.TOOLS),
    "travel": suite_common.get_globals_for_env(travel_apis.TOOLS),
    "slack": suite_common.get_globals_for_env(slack_apis.TOOLS),
    "banking": suite_common.get_globals_for_env(banking_apis.TOOLS),
}

ALL_SUITES = list(TOOL_APIS.keys())