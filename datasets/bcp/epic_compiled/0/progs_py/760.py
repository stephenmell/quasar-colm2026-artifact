context_info = ()
for d in context:
    result = llm_query(f"""You are given a single document. Extract any person(s) in the document possibly matching the following query. Do not use any outside knowledge; rely strictly on the document.

QUERY ATTRIBUTES:
- Born in the 1930s in a country in Africa.
- Divorced from their spouse in the 1960s.
- Their mother was a stage actress.
- Studied drama in a city where they later died between 2016 and 2023.
- Starred in a 1950s movie that was directed by a director who received an NSFC (National Society of Film Critics) Award between 1974 and 1982.

For each candidate person mentioned in the document, provide:
Candidate:
- Full name:
- Born: (year or decade; city/country)
- Mother is a stage actress: (yes/no/unknown)
- Spouse and divorce: (name and year if any)
- Studied drama: (city and institution if given)
- Death: (year and city)
- 1950s film(s) they starred in: (title(s))
- Director(s) of those 1950s film(s):
- Any explicit mention in the document that the director received an NSFC Award between 1974 and 1982: (quote or 'none')
Supporting Quotes:
- Include the exact sentences/lines from the document that support each filled attribute above.
If the document contains no relevant person, output: 'No candidates in this document.'

BEGIN_DOCUMENT
{d}
END_DOCUMENT""")
    context_info = context_info + (result,)

synthesis = llm_query("You will be given extractions from multiple documents (each produced from the user's context) regarding potential candidates. Using ONLY these extractions (no outside knowledge), identify the single person who matches ALL the following constraints:\n- Born in the 1930s in a country in Africa.\n- Divorced from their spouse in the 1960s.\n- Their mother was a stage actress.\n- Studied drama in a city where they later died between 2016 and 2023.\n- Starred in a 1950s movie that was directed by a director who received an NSFC (National Society of Film Critics) Award between 1974 and 1982.\n\nHere are the per-document extractions:\n" + "\n\n-----\n\n".join(context_info) + "\n\nAnswer with ONLY the full name of the person that meets all criteria. If uncertain, choose the best-supported candidate and still answer with ONLY the full name.")
return_result(synthesis)