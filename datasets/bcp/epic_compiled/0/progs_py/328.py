context_info = ()
for d in context:
    q = llm_query(f"""You are given a single document. Extract biographical facts about any person(s) mentioned and test them against the following constraints. Provide direct quotes for each matched attribute and a normalized summary for reasoning.

BEGIN_DOCUMENT
{d}
END_DOCUMENT

CONSTRAINTS (must all be satisfied by the same person):
1) The individual is a content creator.
2) Born between 1987 and 1993 inclusive.
3) Born on the 24th day of a month.
4) As of 2022, the individual had a medical degree.
5) The individual got married between 2018 and 2022 inclusive.
6) Both parents are in the medical field.
7) The individual launched their production company between 2010 and 2019 inclusive.
8) As of 2017, he has four siblings.

Instructions:
- If multiple individuals are in the document, evaluate each separately.
- For each candidate, list attributes with normalized values and exact supporting quotes from the document.
- State explicitly which constraints are satisfied or missing for each candidate.
- If any candidate satisfies ALL constraints, output a line exactly as: BIRTH_MONTH_YEAR: <Month YYYY> (e.g., "BIRTH_MONTH_YEAR: December 1991").
- Keep the output compact but complete for the attributes.

Format strictly as:

CANDIDATE:
Name: <name or 'Unknown'>
Attributes:
- Content creator: <Yes/No/Unknown>; Quotes: "<quote if any>"
- Birth date: <DD Month YYYY or whatever is given>; Day-is-24: <Yes/No/Unknown>; Year-in-1987-1993: <Yes/No/Unknown>; Quotes: "<quote>"
- Medical degree by 2022: <Yes/No/Unknown>; Quotes: "<quote>"
- Marriage year (2018-2022): <year or Unknown>; In-range: <Yes/No/Unknown>; Quotes: "<quote>"
- Parents both in medical field: <Yes/No/Unknown>; Quotes: "<quote>"
- Production company launch year (2010-2019): <year or Unknown>; In-range: <Yes/No/Unknown>; Quotes: "<quote>"
- Siblings as of 2017: <number or Unknown>; Equals 4: <Yes/No/Unknown>; Quotes: "<quote>"
Verdict (matches all constraints): <True/False>

If Verdict is True, include: BIRTH_MONTH_YEAR: <Month YYYY>
""")
    context_info = context_info + (q,)

compiled = "\n\n".join(context_info)

final_query = """
You will receive aggregated candidate analyses from multiple documents. Your task is to identify the single individual who matches ALL the constraints in the user's query. If information about the same person appears across multiple documents, you may combine it to satisfy all constraints.

User's query (constraints restated):
- A content creator.
- Born between 1987 and 1993 inclusive.
- Born on the 24th day of the month.
- As of 2022, the individual had a medical degree.
- Married between 2018 and 2022 inclusive.
- Both parents are in the medical field.
- Launched their production company between 2010 and 2019.
- As of 2017, he has four siblings.
Goal: Provide the MONTH and YEAR of birth for this individual.

Here are the per-document analyses:
BEGIN_ANALYSES
""" + compiled + """
END_ANALYSES

Instructions:
- Reconcile and deduplicate candidates across analyses by name and contextual clues.
- Prefer direct quotes. Combine evidence across documents if they clearly refer to the same person.
- If exactly one person satisfies all constraints, output only the birth month and year in the format: Month YYYY
- If more than one person appears to satisfy all constraints, choose the one with the strongest, most directly quoted evidence and still output only: Month YYYY
- If none fully satisfy but one is the closest match, output their month and year with a best-effort deduction. Do not include any other text.
"""

result = llm_query(final_query)
return_result(result)