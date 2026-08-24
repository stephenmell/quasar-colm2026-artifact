description = "Identify the historical novel (published before 2015) with these plot points: - The protagonist, while in disguise, is noticed by a girl. - Later, the protagonist discovers that the girl is being threatened by her brother for allowing him to escape. - A sorceress tells the main character that she taught his close companion how to cast a spell. - In an intense climax, the protagonist reveals the curse to his love interest and tries to eliminate it, but it sticks to him. - In the end, the protagonist is encouraged to join hands with his love interest."

gathered = ()
for d in context:
    q = "Here is a document:\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT\nBased on this document alone, list any historical novel(s) published before 2015 that match the following description:\n" + description + "\nFor each candidate, provide:\n- Title, author, year\n- Exact quotes or close paraphrases from the document that map to each listed plot point (if present in the document)\n- A brief justification of why this document supports the match\nIf the document contains no relevant match, answer exactly: NO MATCH"
    r = llm_query(q)
    gathered = gathered + (r,)

combined = "\n\n--- DOCUMENT ANALYSIS ---\n\n" + "\n\n".join(gathered)

final_q = "You are given analyses extracted from a set of documents. Your task is to determine the single best answer to the user's query, based strictly on these analyses but also using your broader knowledge to reconcile references if needed. The query is:\n" + description + "\n\nAnalyses:\n" + combined + "\n\nInstructions:\n- Determine which historical novel (published before 2015) best matches all the specified plot points.\n- If multiple titles are mentioned, pick the one that most directly and completely fits the description.\n- Output ONLY the book title, with no author and no additional text."
final_answer = llm_query(final_q)

return_result(final_answer)