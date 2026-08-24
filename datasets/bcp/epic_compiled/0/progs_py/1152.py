context_info = ()
for d in context:
    q = "Here is a document:\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT\nRead the document carefully. If it mentions any poet who matches any of the following traits, extract all relevant details with direct quotations and dates when available:\n- Lost two family members during a pandemic that occurred between 2005 and 2023 inclusive (e.g., COVID-19). Identify the pandemic and the family members if possible.\n- In an interview dated before 2015, the poet revealed they had never been read to as a child and also discussed their mental health condition. Provide the interview date, outlet, and the mental health condition discussed.\n- As of December 2023, the poet is married to an Appalachian writer. Provide the spouse’s name and confirm they are an Appalachian writer.\n- A poem by this poet that has the word “photograph” in its title. Provide the exact title and the first two lines of the poem verbatim if present in the document; otherwise provide the best available paraphrase or any lines quoted.\nIf the document contains nothing relevant, answer exactly: No relevant info.\nFormat your response as:\nPoet: [Name]\nEvidence:\n[Bullet quotes with citations or contextual cues]\nPoemTitle: [Title]\nFirstTwoLines: [Two lines verbatim if present; otherwise best available]\n"
    r = llm_query(q)
    context_info = context_info + (r,)

agg = ""
for r in context_info:
    agg = agg + "\n---\n" + r

final_q = "You are given extracted notes from multiple documents:\n" + agg + "\n\nTask:\n1) Identify the single poet who satisfies ALL of the following:\n- Lost two family members during a 2005–2023 pandemic.\n- In an interview dated before 2015 said they had never been read to as a child and discussed their mental health condition.\n- As of December 2023 is married to an Appalachian writer.\n- Wrote a poem with the word “photograph” in the title.\n2) From that poem, provide the exact first two lines if available in the notes. If they are not present in the notes but you know them, provide them accurately.\n3) Then answer this question in the fewest words possible, quoting if appropriate: In that poem, what does the child ask the speaker for in the first two lines of the poem?\nOnly output the final direct answer to the question, not the reasoning."
answer = llm_query(final_q)
return_result(answer)