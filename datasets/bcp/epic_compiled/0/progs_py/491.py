extractions = ()
for d in context:
    prompt = "You will be given one document. Identify any rock band(s) mentioned and extract details, but ONLY include bands whose formation year is 1999. For each qualifying band, provide a compact entry starting with 'CANDIDATE:' and include: Band Name; Formation Year; Origin Country; Country Area in km² (approx); Is area between 700 and 800 inclusive (Yes/No); Style notes, specifically whether it blends folk music with modern rock (Yes/No + short note); Bass guitarist's name as of 16 December 2023; Bassist's date of birth; Bassist's zodiac sign; Is bassist's sign Cancer (Yes/No). Include short supporting quotes from the document where applicable. Keep each candidate to 5-8 lines total. If the document contains no band formed in 1999, output nothing.\n\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT"
    result = llm_query(prompt)
    extractions = extractions + (result,)

combined = "\n\n===== NEXT DOCUMENT =====\n\n".join(extractions)

final_prompt = "From the following candidate entries (already filtered to bands formed in 1999), select the single band that satisfies ALL of the following:\n- The band's origin country has land area between 700 and 800 km² (inclusive).\n- The band blends or combines elements of folk music with modern rock in its style.\n- The band's bass guitarist (as of 16 December 2023) has zodiac sign Cancer.\n\nIf multiple candidates fit, choose the best documented match. If no candidates fully match, propose one band from your broader knowledge that does. IMPORTANT: Return ONLY the exact band name, with no extra words or punctuation.\n\nCANDIDATES:\n" + combined

answer = llm_query(final_prompt)
return_result(answer.strip())