# Plan:
# 1) Iterate over each context document and ask a sub-LLM to extract concise, structured notes matching the riddle:
#    - Event before year 1000 in a patriarchal/Patriarchate context that provoked public indignation
#    - Central individual's name, birthplace/region, and birth century
#    - First territorial authority received > 40 years after birth, including who entrusted/appointed them
#    - A later prominent post they received a few years later, held for < 10 years
#    - The second successor to this individual in that later post, and whether that figure reinstated a practice akin to damnatio memoriae
# 2) Aggregate these extracted notes
# 3) Use a sub-LLM to synthesize and answer ONLY: the name of the person who entrusted the central figure with their first territorial authority

context_info = ()
for d in context:
    prompt = "You are given a document. Extract only information relevant to the following riddle. Keep output concise and structured, using the specified field labels. If the document is irrelevant, output nothing.\n\nRiddle constraints:\n- An episode in a patriarchal society (or Patriarchate) before the year 1000 incited a wave of indignation among the local people.\n- The central figure was born in the same broad region and within the same century as the episode.\n- More than four decades after their birth, the central figure was entrusted with a position of territorial authority (e.g., governor, bishop, count, archon, etc.). Identify WHO entrusted/appointed them to that first territorial role.\n- A few years later, the figure received another prominent position, which they held for less than a decade.\n- The second successor to this figure in that prominent position reinstated a historical practice designed to obliterate certain individuals from official records and public memory (akin to damnatio memoriae). Identify that successor and the practice.\n\nOutput format (include only fields you can fill from this single document; skip fields you cannot support):\nCentralFigure: <Name>\nBirthRegion: <Region/City/Area>\nBirthCentury: <Century>\nEpisode: <Brief description and date>\nFirstTerritorialRole: <Title/Role>\nFirstTerritorialRoleDate: <Year or range>\nEntrustedBy: <Name of appointer/entruster>\nLaterProminentPost: <Title/Role>\nLaterProminentPostDate: <Year or range>\nLaterProminentPostTenure: <Duration>\nSecondSuccessorInThatPost: <Name>\nReinstatedPractice: <Description of practice; explain how it relates to erasing from records/public memory>\nKeyQuotes: <One or two short quotations from the document supporting the above>\n\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT\n"
    result = llm_query(prompt)
    context_info = context_info + (result,)

notes = ""
for r in context_info:
    if r is not None and len(r.strip()) > 0:
        notes = notes + r + "\n\n"

final_prompt = "You are given extracted notes from multiple documents. Your task is to resolve the riddle by finding a single best-fitting match across all notes. The riddle:\n- Before the year 1000, an episode in a patriarchal society/Patriarchate caused a wave of indignation among the people of that area.\n- The central figure was born in the same region and century.\n- More than four decades after their birth, they were entrusted with a first territorial position of authority; identify who entrusted/appointed them.\n- A few years later, they received another prominent position held for less than a decade.\n- The second successor to them in that later post reinstated a historical practice akin to 'damnatio memoriae' (erasing individuals from official records/public memory).\n\nUse only the notes below to identify the central figure and the entruster of their first territorial role. If multiple candidates appear, pick the one that satisfies ALL constraints most precisely based on the notes. Output ONLY the name of the person who entrusted/appointed the central figure to their first territorial position of authority. No explanations or extra text.\n\nNOTES BEGIN\n" + notes + "NOTES END\n"
answer = llm_query(final_prompt)
return_result(answer.strip())