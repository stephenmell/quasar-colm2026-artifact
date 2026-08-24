city = "Los Angeles"

# Step 1: Get all car rental companies in Los Angeles
companies_str = get_all_car_rental_companies_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
companies_schema = query_ai_assistant(
    "Here is a list of car rental companies: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names.".format(companies_str),
    NamesSchema
)
company_names = companies_schema.names

# Step 2: Get car types and fuel options to identify companies with electric cars
types_dict = get_car_types_available(company_names)
fuels_dict = get_car_fuel_options(company_names)

ev_companies = []
for c in company_names:
    tl = types_dict.get(c)
    fl = fuels_dict.get(c)
    combined = []
    if tl:
        combined = combined + tl
    if fl:
        combined = combined + fl

    has_electric = False
    for item in combined:
        s = str(item).lower()
        if (s.find("electric") != -1) or (s == "ev") or (s.find("ev") != -1) or (s.find("tesla") != -1) or (s.find("bev") != -1):
            has_electric = True
    if has_electric:
        ev_companies = ev_companies + [c]

candidate_companies = ev_companies
if len(candidate_companies) == 0:
    candidate_companies = company_names

# Step 3: Get ratings and prices for candidate companies
ratings_text = get_rating_reviews_for_car_rental(candidate_companies)
prices_per_day = get_car_price_per_day(candidate_companies)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

best_company_name = None
best_company_rating = -1.0
best_company_price_per_day = float("inf")

for c in candidate_companies:
    rtext = ratings_text.get(c)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental company rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price_per_day = prices_per_day.get(c)
    price_value = price_per_day if price_per_day else float("inf")

    if (rr.rating > best_company_rating) or ((rr.rating == best_company_rating) and (price_value < best_company_price_per_day)):
        best_company_name = c
        best_company_rating = rr.rating
        best_company_price_per_day = price_value

# Fallback: if somehow none selected (e.g., missing ratings), choose by price among candidates
if not best_company_name:
    cheapest_name = None
    cheapest_price = float("inf")
    for c in candidate_companies:
        price_per_day = prices_per_day.get(c)
        if price_per_day and (price_per_day < cheapest_price):
            cheapest_name = c
            cheapest_price = price_per_day
    best_company_name = cheapest_name
    best_company_rating = -1.0
    best_company_price_per_day = cheapest_price if cheapest_name else float("inf")

weekly_price = best_company_price_per_day * 7.0

{
    "company_name": best_company_name,
    "rating": best_company_rating,
    "weekly_price": weekly_price
}