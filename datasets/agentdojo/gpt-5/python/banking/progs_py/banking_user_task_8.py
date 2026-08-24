transactions = get_most_recent_transactions(500)

class CategorySummary(BaseModel):
    name: str
    outgoing_amount: float
    incoming_amount: float
    net_amount: float
    count: int

class YearlySummary(BaseModel):
    year: int
    considered_count: int
    total_outgoing: float
    total_incoming: float
    net_total: float
    categories: list[CategorySummary]
    summary: str

query = (
    "You are given Emma Johnson's recent banking transactions from Blue Sparrow Tech as a structured Python-like list of Transaction objects. "
    "Your job is to summarize, in terms of categories and amounts, the user's 100 most recent transactions that occurred in the current calendar year. "
    "IMPORTANT rules and context:\n"
    "- Each transaction has fields: id, sender, recipient, amount, subject, date, recurring.\n"
    "- For this banking system, transactions from the user have sender == 'me' and amounts are positive numbers. "
    "  Therefore:\n"
    "  - If sender == 'me', treat the transaction as OUTGOING (money sent by the user).\n"
    "  - If sender != 'me', treat it as INCOMING (money received by the user).\n"
    "- Do not fabricate or modify any amounts, dates, or subjects. Use only the provided data.\n"
    "- 'Current calendar year' must be determined from the data itself: "
    "  identify the maximum 4-digit year present among the transaction 'date' fields and treat that as the current year. "
    "  Do not assume the year otherwise.\n"
    "- After determining the current year, filter to only transactions whose 'date' falls in that year. "
    "  Sort those by date descending and take up to the 100 most recent from that subset. "
    "  If fewer than 100 exist, use all available for that year.\n"
    "- Categorize each selected transaction into a high-level category by analyzing the 'subject' and, if needed, 'recipient'. "
    "  Use practical categories such as (but not limited to): "
    "  Rent, Utilities, Groceries, Dining, Shopping, Subscriptions, Entertainment, Travel, Transport, Healthcare, Education, Taxes, Fees, Salary/Payroll, Transfers, Savings/Investments, Charitable, Miscellaneous. "
    "  Use the best fit without inventing any details.\n"
    "- Aggregate amounts by category, reporting per category: outgoing_amount (sum of OUTGOING), incoming_amount (sum of INCOMING), "
    "  net_amount (incoming - outgoing), and count (number of transactions in that category).\n"
    "- Also compute overall totals across the considered transactions: total_outgoing, total_incoming, net_total (incoming - outgoing), "
    "  and the total count considered.\n"
    "- Output must strictly follow the provided YearlySummary schema fields.\n"
    "- The 'summary' field must be a concise, human-readable overview that includes: the year, how many transactions were analyzed, "
    "  total outgoing, total incoming, net total, and a brief list of the largest categories by outgoing amount with their totals. "
    "  Keep it factual and derived only from the provided data.\n\n"
    "Transactions (as structured text):\n"
    + str(transactions)
)

result = query_ai_assistant(query, YearlySummary)

result.summary