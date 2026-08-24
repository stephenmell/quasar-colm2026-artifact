context_info = ()
for d in context:
    prompt = "Here is a document:\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT\n" + "Task: Does this document mention a water-related structure in Ireland that meets ALL of the following? 1) Some sources say it was built in the 19th century, while others claim it was built in the first half of the 20th century. 2) It was used to help with stability (e.g., stabilizing a vessel, harbour, shoreline, or structure). 3) There is a local restaurant named after this structure in a nearby hotel. If yes, extract details. If not, reply exactly with NO_MATCH.\nOutput format (exact keys):\nStructureName: <name>\nAlsoKnownAs: <aliases or blank>\nPurpose: <how it helps with stability>\nBuildDates: <the conflicting dates as stated>\nRestaurant: <restaurant name if given>\nHotel: <hotel name if given>\nLocation: <where in Ireland>\nSupportingQuotes:\n- \"<quote 1>\"\n- \"<quote 2>\""
    result = llm_query(prompt)
    context_info = context_info + (result,)

combined = "\n\n".join(context_info)

final_prompt = "Below are extractions from multiple context documents that may include mentions of an Irish water-related structure with conflicting reported construction dates (some say 19th century; others say first half of the 20th century), used to help with stability, and lending its name to a local restaurant in a nearby hotel.\n\nEXTRACTIONS:\n" + combined + "\n\nQuestion: According to these sources, what is the name of this structure? Reply with only the structure's name and nothing else."
final_answer = llm_query(final_prompt)
return_result(final_answer)