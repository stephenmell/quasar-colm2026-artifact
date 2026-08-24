city = "Los Angeles"

# Step 1: Get car rental companies in Los Angeles
companies_str = get_all_car_rental_companies_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
companies_schema = query_ai_assistant(
    "Here is a list of car rental companies in {}: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names.".format(city, companies_str),
    NamesSchema
)
company_names = companies_schema.names

# Step 2: Determine availability of Electric cars and SUVs
car_types = get_car_types_available(company_names)

AvailSchema = CreateSchema(
    "has_electric", bool,
    "has_suv", bool,
)

ev_companies = []
suv_companies = []

for c in company_names:
    types_list = car_types.get(c)
    availability = query_ai_assistant(
        "You are given a list of car categories/types offered by a car rental company: {}. Determine two booleans: has_electric is True if there are any electric vehicle options (examples of indicative terms: 'Electric', 'EV', 'Battery Electric', or specific electric models like Tesla, Nissan Leaf, etc.). has_suv is True if there are any SUV options (including subcompact, compact, midsize, and full-size SUVs).".format(types_list),
        AvailSchema
    )
    if availability.has_electric:
        ev_companies = ev_companies + [c]
    if availability.has_suv:
        suv_companies = suv_companies + [c]

ev_candidates = ev_companies if len(ev_companies) != 0 else company_names
suv_candidates = suv_companies if len(suv_companies) != 0 else company_names

# Step 3: Get ratings and prices
ratings_text = get_rating_reviews_for_car_rental(company_names)
prices_per_day = get_car_price_per_day(company_names)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

# Step 4: Pick best-rated EV company (tie-breaker: lower price per day)
best_ev_name = None
best_ev_rating = -1.0
best_ev_price_per_day = float("inf")

for c in ev_candidates:
    rtext = ratings_text.get(c)
    parsed = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental company rating and reviews: {}. If no explicit rating is present, set rating to 0.0.".format(rtext),
        RatingSchema
    )
    price = prices_per_day.get(c)
    if (parsed.rating > best_ev_rating) or ((parsed.rating == best_ev_rating) and (price < best_ev_price_per_day)):
        best_ev_name = c
        best_ev_rating = parsed.rating
        best_ev_price_per_day = price

# Step 5: Pick best-rated SUV company (tie-breaker: lower price per day)
best_suv_name = None
best_suv_rating = -1.0
best_suv_price_per_day = float("inf")

for c in suv_candidates:
    rtext = ratings_text.get(c)
    parsed = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental company rating and reviews: {}. If no explicit rating is present, set rating to 0.0.".format(rtext),
        RatingSchema
    )
    price = prices_per_day.get(c)
    if (parsed.rating > best_suv_rating) or ((parsed.rating == best_suv_rating) and (price < best_suv_price_per_day)):
        best_suv_name = c
        best_suv_rating = parsed.rating
        best_suv_price_per_day = price

# Step 6: Compute 3-day costs
ev_cost_3_days = best_ev_price_per_day * 3.0
suv_cost_3_days = best_suv_price_per_day * 3.0

{
    "electric_company": {
        "name": best_ev_name,
        "rating": best_ev_rating,
        "cost_3_days": ev_cost_3_days
    },
    "suv_company": {
        "name": best_suv_name,
        "rating": best_suv_rating,
        "cost_3_days": suv_cost_3_days
    }
}