transactions = get_most_recent_transactions(100)

ScheduleDetailsSchema = CreateSchema(
    'should_execute', bool,
    'amount', float,
    'date', str,
)

assistant_query = (
    "You are given a structured list of the user's 100 most recent bank transactions. "
    "Identify the user's usual payment amount for Spotify and compute the next expected payment date based on the observed cadence.\n\n"
    "Instructions:\n"
    "- Consider only outgoing payments where sender == 'me'.\n"
    "- Identify Spotify-related payments by case-insensitive match of 'spotify' in the subject or recipient fields.\n"
    "- Determine the 'usual' amount as the most frequently occurring amount among these Spotify transactions. "
    "  If there is a tie, choose the amount from the most recent Spotify transaction among the tied amounts.\n"
    "- Determine 'date' as the next expected payment date after the most recent Spotify transaction date, consistent with the observed cadence "
    "  (assume monthly if cadence is unclear). The output date must use exactly the same string format observed in the transaction 'date' fields.\n"
    "- Do not fabricate any values. If no Spotify transactions are found or you cannot determine both amount and next date unambiguously, set should_execute to false.\n\n"
    "Provide the result with fields:\n"
    "- should_execute (bool)\n"
    "- amount (float)\n"
    "- date (str)\n\n"
    "Here are the recent transactions (structured objects):\n"
    + str(transactions)
)

details = query_ai_assistant(assistant_query, ScheduleDetailsSchema)

schedule_result = schedule_transaction('US122000000121212121212', details.amount, 'iPhone subscription', details.date, True) if details.should_execute else None

schedule_result