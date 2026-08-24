context_info = ()
for d in context:
    prompt = "Here is a document:\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT\n\nFrom this document, extract any explicitly mentioned facts from the list below. If a fact is not present, omit it. Use one line per item exactly as shown:\n\nCompany: <company name>\nCo-founders: <names>\nPaternal leave 2018: <name and details>\nBorn same year as country won pre-2000 World Championship: <name; birth year; country; sport/event; championship year>\n2021 net worth between $430M and $440M: <name; estimate>\nValuation in September 2019: <figure and currency>\n"
    result = llm_query(prompt)
    context_info = context_info + (result,)

aggregated = "\n---\n".join(context_info)

final_prompt = "Here are extracted snippets from the context:\n" + aggregated + "\n\nUsing only the information above, identify the single company that matches all three conditions:\n1) One co-founder was born in the year their country won a pre-2000 World Championship in a sport.\n2) That co-founder took paternal leave in 2018.\n3) As of 2021, the other co-founder had an estimated net worth between $430 million and $440 million.\n\nProvide only that company's valuation in September 2019. Reply with only the figure and currency (e.g., $3.2 billion)."
final_answer = llm_query(final_prompt)

return_result(final_answer)