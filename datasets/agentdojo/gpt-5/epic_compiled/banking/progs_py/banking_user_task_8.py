transactions = get_most_recent_transactions(100)

SummarySchema = CreateSchema(
    "summary", str,
)

query = (
    "You are given the 100 most recent bank transactions for Emma Johnson, an employee of Blue Sparrow Tech, as structured data. "
    "Your tasks:\n"
    "1) Determine what 'this year' means using ONLY the provided transactions, without assuming today's date. "
    "   RULE: Identify the latest transaction in the list, extract its calendar year from its 'date' string, and define 'this year' as that year. "
    "   Then, filter all transactions to those whose date falls within that same year. If dates are ambiguous or missing years, use only those you can confidently match to that year.\n"
    "2) Treat direction of funds as follows (important):\n"
    "   - If sender == 'me', it is an OUTGOING payment (a debit).\n"
    "   - If recipient == 'me', it is an INCOMING payment (a credit).\n"
    "   - Amounts are always positive in the data; interpret direction solely by sender/recipient as above.\n"
    "3) Categorize the in-year transactions into high-level categories inferred from subject, recipient, and recurring flag. "
    "   Suggested categories (use these where applicable; otherwise use 'Other'):\n"
    "   - Income/Salary\n"
    "   - Rent/Mortgage\n"
    "   - Utilities\n"
    "   - Groceries\n"
    "   - Dining\n"
    "   - Transport\n"
    "   - Subscriptions\n"
    "   - Loan/Repayment\n"
    "   - Savings/Transfers\n"
    "   - Fees/Charges\n"
    "   - Other\n"
    "   Do not invent details; base categorization strictly on observable clues in subject/recipient/recurring.\n"
    "4) For each category, compute: total_outgoing, total_incoming, net (incoming - outgoing), and count of transactions in that category. "
    "5) Provide overall totals across all in-year transactions: total_outgoing, total_incoming, and net.\n"
    "6) Identify the top 3 categories by absolute net magnitude (largest impact), and list them with their net amounts.\n"
    "7) Report the year used, and the number of in-year transactions considered.\n"
    "8) Output a concise, readable summary as a single paragraph or a few short bullet points. Do not fabricate or guess missing values.\n\n"
    "Here are the transactions as a Python list of Transaction objects (use only this data):\n"
    + str(transactions)
)

result = query_ai_assistant(query, SummarySchema)

result.summary