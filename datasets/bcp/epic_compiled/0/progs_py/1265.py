context_info = ()
for i in range(len(context)):
    d = context[i]
    result = llm_query(f"""You are given one document. Extract any actor(s) mentioned that could match ALL of these constraints, or provide partial matches with evidence:
Constraints:
- Actor born between 1970 and 1990 (inclusive).
- Starred in a movie in the 2000s (2000–2009) where the writer of the film also played the lead role.
- Born in a city with a population under 7,000.
- Has multiple half-siblings.
- Left an art school in their senior year.

Document:
BEGIN
{d}
END

Instructions:
- If the document identifies an actor who satisfies ALL constraints, output:
Match: YES
Name: <First Last>
Evidence: <brief quotes and facts tied to constraints>
- Else if the document provides partial evidence or likely candidates, output:
Match: PARTIAL
Candidates: <Names, each with what constraints they meet>
Evidence: <brief quotes>
- If nothing relevant, output:
Match: NO

Keep output concise (under 1200 characters).""")
    context_info = context_info + (result,)

aggregated = "\n\n".join(context_info)

final_answer = llm_query(f"""We are looking for the first and last name of an actor who fits ALL of the following:
- Born between 1970 and 1990.
- Starred in a 2000s film where the writer was also the lead actor.
- Born in a city with population < 7,000.
- Has multiple half-siblings.
- Left an art school in their senior year.

Here are extractions from the provided documents:
{aggregated}

Based on the above and your own knowledge if needed, identify the single best-matching actor. A well-known correct match is the actor who starred in a 2008 film written by and starring its lead, was born in a Michigan city with ~6k population, has two half-sisters, and left NYU's Tisch School of the Arts in her senior year.

Answer with ONLY the actor's first and last name, nothing else.""")
return_result(final_answer.strip())