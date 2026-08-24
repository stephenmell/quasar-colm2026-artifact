context_info = ()
for d in context:
    result = llm_query(f"""Here is a document:
BEGIN_DOCUMENT
{d}
END_DOCUMENT

Task: From this document alone, extract any evidence about a streaming drama series from the early 2020s whose central theme is music. If the document contains such information, provide a concise structured note with:
- Series title(s)
- Evidence quotes (exact lines) from the document that indicate music as a central theme, streaming release in early 2020s, and number of seasons (especially whether only one season was available by end of 2023)
- Mapped actors and clues, only if the document explicitly supports them:
  * A lead actor who has received several awards and has published a memoir (name the actor and memoir if stated)
  * An actor (from the cast) who was the head of an education-based trust for several years (name the actor and the trust if stated)
  * The actor who played his half-brother in the series published a book of poetry (name the actor and poetry book if stated; clarify whose half-brother)
  * A female lead who previously starred in a movie with meaningless (gibberish/nonsense) language (name the actress and the movie if stated)

Important:
- Use only information present in the document; if a detail is not in the document, skip it.
- If the document does not mention any relevant series, output nothing.""")
    context_info = context_info + (result,)

notes = "\n\n---\n\n".join(context_info)

final_query = """You are given extracted notes from multiple documents about a streaming drama series with a central theme of music, streamed in the early 2020s. The series we want must match these clues together:
- One of the lead actors is a recipient of several awards and has published a memoir.
- In real life, one actor was the head of an education-based trust for several years.
- The actor who played his half-brother (in the series) published a book of poetry.
- A female lead previously starred in a movie featuring meaningless (gibberish/nonsense) language.
- As of the end of 2023, only one season of the series was available.

From the notes, determine the single series title that best matches all clues. Use only the provided notes. If multiple candidates appear, choose the one that satisfies all bullets. If none satisfy all, choose the one that satisfies the most and is explicitly a music-themed early-2020s streaming drama with one season by end of 2023.

Output only the exact series title, with no additional text."""

result = llm_query("Here are the extracted notes:\n\n" + notes + "\n\n" + final_query)
return_result(result)