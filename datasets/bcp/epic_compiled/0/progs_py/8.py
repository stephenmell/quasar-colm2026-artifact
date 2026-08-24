# The goal: Identify a short-lived 1990s TV series whose cast includes:
# - an actor born in Tennessee,
# - an actor who was a Caribbean immigrant,
# - an actor whose father was a law enforcement officer for more than 3 decades.
#
# Approach:
# 1) For each context document, ask a sub-LLM to extract any relevant 1990s TV series and cast, along with
#    the three specific actor traits (with quotes from the doc).
# 2) Aggregate those extractions.
# 3) Ask a sub-LLM to determine which single 1990s short-lived series satisfies all three constraints
#    across the aggregated evidence, and provide the series title as the final answer.

context_summaries = ()
for d in context:
    q = """You are given one document. Extract only information directly supported by this document.
Task:
- Identify any 1990s TV series mentioned and note if they were short-lived (one season or otherwise explicitly described as short-lived/cancelled quickly).
- List actors connected to those series (as presented in this document), and capture any of the following actor traits if present in the document:
  A) Born in Tennessee (cite city/state if mentioned)
  B) Caribbean immigrant (born in a Caribbean nation and immigrated to the U.S.; cite origin and immigration language)
  C) Father was a law enforcement officer for more than 3 decades (cite father’s law enforcement role and duration)
- For each item, provide brief direct quotes from the document that justify both the linkage (actor-to-series) and the trait.

Format your output as entries. For each series you find in the document:
Series: <series title> (<year(s)>)
Short-lived?: <yes/no/unclear + any details>
Actor evidence:
- <Actor name>: <trait(s) detected among A/B/C or 'none'> 
  Quotes:
  - <quote linking actor to series>
  - <quote supporting trait(s)>

Only include items that are directly supported by explicit text in this document. If the document doesn’t contain relevant info, output nothing."""
    r = llm_query("BEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT\n" + q)
    context_summaries = context_summaries + (r,)

aggregated = "\n\n".join(context_summaries)

final_q = """You are given extracted evidence from multiple documents. Your job: determine which 1990s TV series (short-lived) satisfies ALL THREE of the following, considering evidence across documents:
1) It starred at least one actor who was born in Tennessee.
2) It starred at least one actor who was a Caribbean immigrant (born in the Caribbean and immigrated to the U.S.).
3) It starred at least one actor whose father was a law enforcement officer for more than three decades.

Instructions:
- Use only the provided evidence to match actors to series and to verify the traits with quotes.
- If multiple series are candidates, choose the best-supported one.
- Output ONLY the title of the TV series (no explanation, no extra words).

Evidence:
""" + aggregated

answer = llm_query(final_q)
return_result(answer)