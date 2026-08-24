context_info = ()
for d in context:
    prompt = f"""You are given a document. Extract any person(s) who were or became President of their country between 1960 and 2000, and evaluate them against the following constraints:
1) Became the President of their country between 1960 and 2000.
2) Studied law at one of the oldest universities in their country (domestic; identify the university and whether it is among the oldest).
3) Got married about 25 years before being elected as President (approximately 23–27 years acceptable).
4) Was born in a city whose 2011 population was more than 65,000 but less than 130,000 (state the city and whether this holds).
5) Was elected as President in the same year an iconic video game debuted (name the year and a plausible iconic game that debuted then).

For each qualifying or potentially qualifying person mentioned in this document, provide a compact entry with:
- Name
- Country
- Presidency election year(s) (within 1960–2000)
- Studied law? University (and whether it is one of the oldest domestically)
- Marriage year (if given)
- Birth city (and whether the 2011 population is 65k–130k)
- Iconic video game that debuted in the same year as their presidential election (give at least one plausible example)
- Does this person meet all constraints? Yes/No
- Key quotes from the document supporting the facts (if available)

If the document does not mention any such person, say 'No relevant person in this document.'
Document:
{d}
"""
    result = llm_query(prompt)
    context_info = context_info + (result,)

aggregated = "\n\n-----\n\n".join(context_info)

final_prompt = "We need the first and last name of the single person who satisfies ALL of the following: became President between 1960–2000; studied law at one of the oldest universities in their country; married about 25 years before being elected President; born in a city whose 2011 population was >65,000 and <130,000; elected President in the same year an iconic video game debuted. Use the extracted notes below. If not decisively present, use your general knowledge as needed, but still satisfy all constraints. Return ONLY the person's first and last name, with nothing else.\n\nExtracted notes:\n" + aggregated

answer = llm_query(final_prompt)
return_result(answer.strip())