context_info = ()
for d in context:
    result = llm_query("You are given a single document. Determine if it mentions a woman who matches ALL or PART of the following composite biography, and extract the strongest candidate(s) with evidence.\n\nComposite biography to match:\n- She holds an MBA AND a separate Master’s degree (two postgraduate degrees: one is an MBA, plus another Master’s).\n- As of 2023, she was a PhD candidate AND the resident pastor of a ministry in West Africa.\n- In 2018, she hosted a podcast consisting of six episodes.\n- As of 2022, she was married with two children; one child shares the same first name as her husband.\n- She met her husband while she was an undergraduate student at the university.\n\nInstructions:\n- Read the document below.\n- If the document mentions any woman who matches at least one of these details, list the candidate’s full name.\n- Under that name, list which criteria are explicitly satisfied in this document, with short direct quotes from the document.\n- If the document contains dates, tie the timeline to the criteria (e.g., “as of 2023” or “in 2018”).\n- If there is no possibly relevant person, output: NO_MATCH.\n\nDocument:\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT")
    context_info = context_info + (result,)

aggregated = "\n\n".join(context_info)

final_query = "From the extracted candidates and evidence below, identify the single woman who best satisfies ALL of the composite biography details. Prefer a candidate who matches every point exactly (MBA and another Master’s; as of 2023 a PhD candidate and resident pastor of a ministry in West Africa; in 2018 hosted a six-episode podcast; as of 2022 married with two children with one child sharing the husband’s first name; met her husband while an undergraduate).\n\nOnly output the person’s full name, and nothing else. If uncertain, output Unknown.\n\nEvidence:\n" + aggregated

final_answer = llm_query(final_query)
return_result(final_answer.strip())