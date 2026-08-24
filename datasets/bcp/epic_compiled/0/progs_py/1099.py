context_info = ()
for d in context:
    result = llm_query(f"""Here is a document:
BEGIN_DOCUMENT
{d}
END_DOCUMENT

You are helping to solve a specific identification puzzle with these constraints:
- A 2017 article identifies a "song of the month" and calls it "the most beautiful piece of music in a long time" (approximate wording acceptable).
- In the same article, the "album of the month" is an album released in January of 2015, 2016, 2017, or 2018, by a band formed in 2003, 2004, 2005, or 2006.
- The "song of the month" has a music video that was released in December of one of 2013, 2014, 2015, or 2016.
- The song’s composer was born in June of one of 1968, 1969, 1970, or 1971.

Tasks:
1) Determine whether this document appears to be that 2017 article. If yes, extract:
   - Article date and author
   - The "song of the month": title, artist, composer name, composer birth month and year, and whether the music video was released in December 2013–2016 (include date and source URL if present)
   - The "album of the month": title, band name, band formation year, album release month and year (include date and source URL if present)
   - Include exact quotes from the article supporting the above, especially any "song of the month"/"album of the month" headings and the "most beautiful piece of music in a long time" wording
2) If not, does the document mention any candidate songs, composers, bands, or a "song of the month"/"album of the month" section that could be relevant to these constraints? Extract any possibly relevant details with quotes and URLs.

Answer in this strict template for this single document:
Match: Yes/No
Reasons:
Extracted:
- Article: [date], [author], [URL if present]
- Song of the month: [title] — [artist]; composer [name], born [month year]; video released [month year]; [video URL if present]
- Album of the month: [title] — [band]; band formed [year]; album released [month year]; [album URL if present]
Quotes:
[...key quotes...]
""")
    context_info = context_info + (result,)

aggregated = "\n\n".join(context_info)

final_answer = llm_query(f"""You will be given extractions from multiple documents. Using only these extractions, identify the single song that satisfies all constraints below. If more than one candidate appears, choose the one where ALL constraints are explicitly satisfied by the evidence.

Constraints to satisfy:
1) The music video of the song was released in December in one of these years: 2013, 2014, 2015, or 2016.
2) A 2017 article calls this song the author's "song of the month" and describes it as "the most beautiful piece of music in a long time" (approximate phrasing permitted).
3) In the same article, the "album of the month" is an album released in January of 2015, 2016, 2017, or 2018 by a band formed in 2003, 2004, 2005, or 2006.
4) The song's composer was born in June of 1968, 1969, 1970, or 1971.

Here are the extractions:
BEGIN_EXTRACTED_NOTES
{aggregated}
END_EXTRACTED_NOTES

Output ONLY the exact title of the song, nothing else (no artist name, no quotes, no punctuation beyond what is part of the title).""")

return_result(final_answer)