import agentdojo.default_suites.v1.tools.file_reader as file_reader
import agentdojo.default_suites.v1.tools.banking_client as banking_client
import agentdojo.default_suites.v1.tools.user_account as user_account


TOOLS = {
        "get_iban": banking_client.get_iban,
        "send_money": banking_client.send_money,
        "schedule_transaction": banking_client.schedule_transaction,
        "update_scheduled_transaction": banking_client.update_scheduled_transaction,
        "get_balance": banking_client.get_balance,
        "get_most_recent_transactions": banking_client.get_most_recent_transactions,
        "get_scheduled_transactions": banking_client.get_scheduled_transactions,
        "read_file": file_reader.read_file,
        "get_user_info": user_account.get_user_info,
        "update_password": user_account.update_password,
        "update_user_info": user_account.update_user_info,
        "query_ai_assistant": None,
}