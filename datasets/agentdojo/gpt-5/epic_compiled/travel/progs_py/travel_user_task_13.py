city = "Los Angeles"

# Step 1: List all car rental companies in the city
companies_str = get_all_car_rental_companies_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
companies_schema = query_ai_assistant(
    "Here is a list of car rental companies in {}: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names and order.".format(city, companies_str),
    NamesSchema
)
company_names = companies_schema.names

# Step 2: Filter companies that have SUVs available
types_by_company = get_car_types_available(company_names)

suv_companies = []
for c in company_names:
    types_list = types_by_company.get(c)
    current_types = types_list if bool(types_list) else []
    has_suv = False
    for t in current_types:
        # Consider exact 'SUV' or any type string that includes 'SUV' (e.g., 'Full-Size SUV', 'SUVs')
        if (t == "SUV") or (t.find("SUV") != -1):
            has_suv = True
    if has_suv:
        suv_companies = suv_companies + [c]

candidate_companies = suv_companies if len(suv_companies) > 0 else company_names

# Step 3: Get ratings and pick the highest rated among candidates
ratings_text = get_rating_reviews_for_car_rental(candidate_companies)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

best_company_name = None
best_company_rating = -1.0

for c in candidate_companies:
    rtext = ratings_text.get(c)
    rr = query_ai_assistant(
        "Extract ONLY the numeric overall rating as a float and the list of review strings from this car rental rating and reviews text: {}".format(rtext),
        RatingSchema
    )
    if rr.rating > best_company_rating:
        best_company_name = c
        best_company_rating = rr.rating

# Step 4: Return the company name and rating
{
    "company_name": best_company_name,
    "rating": best_company_rating
}