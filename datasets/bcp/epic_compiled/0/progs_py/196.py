context_info = ()
for d in context:
    result = llm_query(f"""You are given a single document. Identify whether it mentions a person who matches any of these facts (available as of Dec 2023):
- Born in 1987.
- Used a stage name when they first began acting (or initially used/considered another name).
- Received advice from an individual of Indian origin to keep their original identity/name.
- Had lived on three continents by age 12.
- Got a matching tattoo alongside their sibling and cousin in the early 2020s.
- In 2017, when asked about their next big project, they said they would be hosting red carpet award shows like The Oscars.

BEGIN_DOCUMENT
{d}
END_DOCUMENT

Instructions:
- If the document contains any mentions that match any of the above, extract the candidate(s).
- For each candidate, provide:
  Candidate: <full name>
  StageName(s): <list any known stage/performing names; especially what they used when they first began acting>
  BirthYear: <year if present>
  Matches:
    - Born in 1987: <evidence or 'not found'>
    - Used a stage name early: <evidence or 'not found'>
    - Indian-origin advisor to keep identity: <evidence or 'not found'>
    - Lived on 3 continents by 12: <evidence or 'not found'>
    - Matching tattoo with sibling and cousin in early 2020s: <evidence or 'not found'>
    - 2017 quote about hosting red carpet award shows like The Oscars: <evidence or 'not found'>
  Quotes: <quote relevant lines verbatim>
  OverallMatchCount: <0-6>
- If no relevant info, reply exactly: No relevant info.""")
    context_info = context_info + (result,)

compiled = "\n\n".join(context_info)

query = """Based on the user's clues (born in 1987; used a stage name when they first began acting; advised by an Indian-origin individual to keep their original identity; lived on three continents by age 12; matching tattoo with sibling and cousin in the early 2020s; in 2017 said their next big project would be hosting red carpet award shows like The Oscars), identify the single best-matching person and provide ONLY their stage name (the one the user is trying to remember). Output only the stage name, with no extra words."""

final = llm_query(f"""You are given extracted findings from multiple documents:

BEGIN_FINDINGS
{compiled}
END_FINDINGS

Task: Determine which candidate satisfies ALL the clues. If more than one candidate appears, choose the one with the highest OverallMatchCount and best direct evidence for the specific clues. If none match all clues but one is clearly intended, choose that one.

{query}""")
return_result(final)