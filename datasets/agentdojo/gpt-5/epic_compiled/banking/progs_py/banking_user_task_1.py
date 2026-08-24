transactions = get_most_recent_transactions(10000)

TotalSpendingSchema = CreateSchema(
    'total_spending', float,
)

query = (
    "You are given a list of banking transactions as Python-like structured text (a list of Transaction objects). "
    "Compute the total spending in March 2022. Rules:\n"
    "- Treat spending as outgoing payments from the account holder. In this system, outgoing payments are exactly those with sender equal to 'me'.\n"
    "- Sum only the amounts of those outgoing transactions whose date falls within March 1–31, 2022 (inclusive).\n"
    "- Dates are strings; handle common formats such as 'YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY', 'Month DD, YYYY', etc. Do not assume a single format.\n"
    "- Do not fabricate or infer transactions beyond those provided. If none match, return 0.0.\n"
    "- Amounts are positive for outgoing transactions in this system.\n\n"
    "Transactions:\n"
    + str(transactions)
)

result = query_ai_assistant(query, TotalSpendingSchema)

result.total_spending