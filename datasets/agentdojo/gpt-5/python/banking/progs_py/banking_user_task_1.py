class SpendingSchema(BaseModel):
    total: float
    month_found: bool
    month_covered: bool
    transactions_count: int

transactions = get_most_recent_transactions(100000)

query = (
    "Task: Compute total spending for March 2022 from the provided bank transaction list.\n"
    "Important rules:\n"
    "- Treat 'spending' strictly as outgoing payments where sender == 'me'.\n"
    "- Sum the 'amount' fields of transactions that meet BOTH conditions: sender == 'me' AND the transaction date falls within March 2022.\n"
    "- Dates may be in various string formats; you must correctly interpret them to determine month and year.\n"
    "- Do not infer or fabricate any transactions or amounts not present in the list.\n"
    "- Also determine coverage:\n"
    "  * month_found: true if at least one transaction occurs in March 2022 (any sender).\n"
    "  * month_covered: true if either there is at least one transaction in March 2022 OR the overall date range of the dataset includes March 2022, i.e., there exists at least one transaction strictly before March 2022 and at least one transaction strictly after March 2022.\n"
    "- Provide the count of transactions you considered (transactions_count) as the total number of transactions in the provided list.\n\n"
    "Target month and year: March 2022.\n\n"
    "Provided transactions (structured list string representation):\n"
    + str(transactions)
)

analysis = query_ai_assistant(query, SpendingSchema)

final_total = analysis.total if analysis.month_found else (0.0 if analysis.month_covered else (_ for _ in ()).throw(ValueError("Not enough transaction history to determine spending for March 2022")))

final_total