context_info = ()
for d in context:
    prompt = """You will be given a single document. Extract and list only the facts that match ANY of the following clues, if present. If a clue is not present, skip it.

For each matched clue, provide:
- Clue label (e.g., "Lead author on element extraction", "Microwave-assisted digestion preferred", "Mineralizer fluid nearly to dryness then transferred to ~10 mL volumetric and diluted with quadruple-distilled water", "Phenolic acids are primary phenolics", "Positive impact on human health", "Heavy metal evaluation important for health protection")
- Exact quote(s) from the document supporting it
- The biological entity discussed (e.g., mushrooms, plants, cereals, bee pollen, etc.)
- The element mentioned (if any) and its atomic number (confirm it is between 20 and 40)
- The paper title or citation snippet if available
- The author name(s) as listed, and clearly indicate if the author appears as the LEAD (first) author

Here is the document:
BEGIN_DOCUMENT
""" + d + """
END_DOCUMENT
"""
    result = llm_query(prompt)
    context_info = context_info + (result,)

aggregated = "\n\n".join(context_info)

final_query = """You are given extracted notes from multiple documents. Your task: Identify the single author whose body of work best matches ALL of the following clues simultaneously, as evidenced by the extracted notes. If multiple authors are possible, choose the one supported by the most and strongest matches, prioritizing explicit quotes.

Clues to satisfy (for the SAME biological entity across the clues, if possible):
1) The author wrote a paper on a certain biological entity and how to extract an element with an atomic number between 20 and 40 from that entity. The author was the lead author on that paper.
2) According to a paper by this author, these specific biological entities have been scientifically proven to positively impact human health.
3) According to a paper by this author, microwave-assisted digestion is a widely used technique and often a preferred approach for element extraction.
4) In a paper by this author, the methods state that the mineralizer fluid was evaporated nearly to a dry residue, then quantitatively transferred into volumetric flasks somewhere between 8 mL and 12 mL in size (i.e., ~10 mL), and diluted to volume with quadruple-distilled water.
5) According to a paper by this author, phenolic acids are the primary type of phenolic compounds found in these specific biological entities.
6) According to a paper by this author, evaluating these specific organic entities for their heavy metal content is important for ensuring human health protection.

Here are the extracted notes:
BEGIN_EXTRACTED_NOTES
""" + aggregated + """
END_EXTRACTED_NOTES

Instructions:
- Determine the single best-matching author name (full name).
- Ensure the biological entity is consistent across the clues (e.g., mushrooms, if indicated).
- Ensure that at least one element explicitly mentioned has an atomic number between 20 and 40 (e.g., Ca=20, As=33, Se=34, Zn=30, Cu=29, etc.), AND that the author was lead author on the relevant extraction/determination paper.
- Prefer direct quotes that explicitly mention (a) microwave-assisted digestion as widely used/preferred, (b) the mineralizer-to-dryness then 10 mL volumetric with quadruple-distilled water procedure, (c) phenolic acids as primary phenolics, (d) health benefits, and (e) heavy metal evaluation importance.

Output format:
- ONLY the author's full name. No justification, no extra text.
"""
result = llm_query(final_query)
return_result(result)