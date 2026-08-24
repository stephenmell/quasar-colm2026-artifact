doc_analyses = ()
for d in context:
    res = llm_query(f"""Read the document below and answer the following. Structure the output as Q/A blocks, each with lines starting 'Question:', 'Quotes:', 'Answer:'.

DOCUMENT:
{d}

Questions:
1) Does the document mention a jazz bassist, composer, and arranger from the Southern Hemisphere born in the 1940s who died in the early 2010s? If yes, provide the person's name, birth and death years, the name of his first official group, and whether he performed a 'Royal Command Performance' with that group in the 1970s. Include exact supporting quotes.

2) If the document mentions where he grew up, give the neighborhood/township name and, if stated, the year the neighborhood was established. Include exact supporting quotes.

3) Does the document contain or reference a Master of Arts thesis written in the 1990s about the history of that neighborhood? If yes, extract the thesis' acknowledgements section and state exactly who the author thanks as "a friend in the Department of Oceanography". Provide the exact quoted line and give the person's full name.

If the document is not relevant to any of these, simply write: 'No relevant info.'""")
    doc_analyses = doc_analyses + (res,)

final_prompt = """You will be given per-document analyses. Determine the answer to the user's question:
'According to the thesis, who did the author mention in the acknowledgements section as a friend in the Department of Oceanography?'

Instructions:
- Identify the relevant jazz bassist (Southern Hemisphere; born 1940s; died early 2010s; performed a Royal Command Performance with his first official group in the 1970s) and the neighborhood he grew up in (established in the late 1920s).
- From the analyses, find the 1990s Master of Arts thesis about that neighborhood’s history.
- From that thesis' acknowledgements, extract the person named as 'a friend in the Department of Oceanography.'
- Output ONLY the person’s name, with no extra words.

Per-document analyses:
""" + "\n\n".join(doc_analyses)

answer = llm_query(final_prompt)
return_result(answer)