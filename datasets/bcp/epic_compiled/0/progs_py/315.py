# Plan:
# 1) Scan each context document to identify if it contains a European club founded in the 1920s with league record:
#    W7-D16-L15, GF 37, GD -12, GA < 50 (i.e., likely 49), prior to 2023; extract club/season and (if present) second-top league scorer minutes.
# 2) From all identification results, ask an LLM to select the single best-matching club-season (e.g., "Celta de Vigo|2019–20|La Liga").
# 3) With the selected target, scan all documents again to extract the club’s second-highest league goal-scorer and total league minutes.
# 4) Ask an LLM to choose the best minutes figure from the candidates and output only the number of minutes.

id_results = ()
for d in context:
    prompt = "You are given a document. Determine whether it contains information about a European football club founded in the 1920s that, in a single league season prior to 2023, recorded exactly the following league statistics: 7 wins, 16 draws, 15 losses; 37 goals scored (GF); goal difference -12; and fewer than 50 goals conceded (i.e., likely 49). If such a club-season appears in the document, extract the following:\n- Club name\n- Founding year (if mentioned; otherwise 'unknown')\n- League name\n- Season (e.g., 2019–20)\n- GF, GA, GD, W, D, L\nAdditionally, if this same document includes league-only player statistics for that club-season, identify the club's second-highest league goal scorer and report their total minutes played in the league (minutes should be for league matches, not all competitions). If multiple players tie for second-most goals, choose the one with the most minutes; if still tied, choose any.\nReturn your findings in this exact template (use 'unknown' where data is missing):\nFOUND: yes/no\nCLUB: <club>\nFOUNDING_YEAR: <year>\nLEAGUE: <league>\nSEASON: <season>\nGF: <gf>\nGA: <ga>\nGD: <gd>\nW: <w>\nD: <d>\nL: <l>\nSECOND_SCORER_NAME: <name or unknown>\nSECOND_SCORER_GOALS: <goals or unknown>\nSECOND_SCORER_MINUTES: <minutes or unknown>\nEVIDENCE: <short quotes from the document that support these values>\n\nDocument begins below:\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT"
    result = llm_query(prompt)
    id_results = id_results + (result,)

id_synthesis_prompt = "Below are extraction results from multiple documents about a target club-season. Your task: select the single club-season that EXACTLY matches all constraints: the club is European and founded in the 1920s; the season is prior to 2023; and the league record is W7-D16-L15 with GF 37, GD -12, and GA < 50 (i.e., 49). Prefer entries with explicit matching evidence. Output exactly one line in the format:\nCLUB|SEASON|LEAGUE\nIf no match is found, output:\nNONE\n\nBEGIN_RESULTS\n" + "\n\n---\n\n".join(id_results) + "\nEND_RESULTS"
target_info = llm_query(id_synthesis_prompt)

minutes_results = ()
for d in context:
    prompt2 = "We are targeting the following club-season (CLUB|SEASON|LEAGUE):\n" + target_info + "\n\nGiven the document below, if it contains league-only player statistics for the targeted club-season, identify the club's second-highest league goal-scorer and report the total minutes they played in the league. If multiple players tie for second-most league goals, choose the one with the most minutes; if still tied, choose any. Return exactly one line in this format:\nNAME|GOALS|MINUTES\nIf the document does not contain relevant league-only player minutes for the targeted club-season, return:\nNOT_FOUND\n\nDocument begins below:\nBEGIN_DOCUMENT\n" + d + "\nEND_DOCUMENT"
    res = llm_query(prompt2)
    minutes_results = minutes_results + (res,)

final_prompt = "We are interested in the total league minutes played by the second-highest league goal-scorer for the targeted club-season provided below.\nTARGET: " + target_info + "\n\nHere are candidate extractions (each either 'NAME|GOALS|MINUTES' or 'NOT_FOUND') from different documents:\n" + "\n".join(minutes_results) + "\n\nInstructions:\n- Choose the best-supported candidate that clearly corresponds to the targeted club-season and that provides MINUTES.\n- If multiple candidates provide minutes, prefer the one with explicit evidence or the most precise minutes figure.\n- Output ONLY the number of minutes (digits only, no commas, no spaces, no words). If unknown, output 'unknown'."
final_answer = llm_query(final_prompt)

return_result(final_answer)