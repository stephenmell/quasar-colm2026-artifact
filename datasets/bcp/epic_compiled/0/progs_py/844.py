context_summaries = ()
i = 0
for d in context:
    i = i + 1
    result = llm_query(f"""You will be given one document. Identify authors mentioned and check for six specific attributes. Be precise and cite exact phrases.

BEGIN_DOCUMENT_{i}
{d}
END_DOCUMENT_{i}

Task:
- List every author explicitly mentioned in the document. For each author, state whether the document provides evidence for the following six attributes. Quote the exact supporting text for any "Yes".
  1) Was (or is) a university instructor.
  2) Their books have been translated into twenty-plus languages.
  3) Has worked as an editor (any editorial role counts: book/magazine/journal/contributing editor, etc.).
  4) Their parents were members of the NRA (National Rifle Association).
  5) Had a recurring nightmare about a wolf creature (e.g., werewolf/wolf-man/wolf-like being; recurring dream or nightmare).
  6) Has three children, two of which are adopted (i.e., total three children, exactly two adopted).

Output format for each author:
Author: <Full Name>
Matches: <X>/6
- Attr1 (university instructor): <Yes/No> | Quote: "<quote or write 'None'>"
- Attr2 (20+ languages): <Yes/No> | Quote: "<quote or 'None'>"
- Attr3 (editor): <Yes/No> | Quote: "<quote or 'None'>"
- Attr4 (parents NRA): <Yes/No> | Quote: "<quote or 'None'>"
- Attr5 (recurring wolf nightmare): <Yes/No> | Quote: "<quote or 'None'>"
- Attr6 (3 children, 2 adopted): <Yes/No> | Quote: "<quote or 'None'>"
Other possibly relevant biographical details quoted verbatim:
"<short relevant excerpts>"

If the document mentions no authors or none with any relevant info, output:
No relevant author.
""")
    context_summaries = context_summaries + (result,)

aggregate = llm_query("""You will be given extracted notes from multiple documents. Using them together, identify the single author who, as of December 31, 2023, satisfies ALL of the following:
1) Was a university instructor.
2) Their books have been translated into twenty-plus languages.
3) Has worked as an editor.
4) Their parents were members of the NRA.
5) Had a recurring nightmare about a wolf creature.
6) Has three children, two of which are adopted.

Instructions:
- Consider that different documents may provide different subsets of evidence about the same author; combine evidence across documents if the same author appears multiple times.
- Prefer direct, quoted evidence for each attribute.
- If exactly one author fulfills all six attributes based on the combined evidence, output ONLY their full name, nothing else.
- If more than one candidate appears, choose the one with the strongest direct evidence matching all six attributes and output ONLY their full name.
- If no candidate clearly satisfies all six, output: Unknown

Here are the extracted notes:
""" + "\n\n-----\n\n".join(context_summaries))

return_result(aggregate)