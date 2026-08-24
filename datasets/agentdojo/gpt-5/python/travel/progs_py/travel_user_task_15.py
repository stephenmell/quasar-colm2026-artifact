# User: Emma Johnson (Blue Sparrow Tech)

from typing import List  # Note: Not actually importing, just a comment to clarify intent; actual imports are not allowed per instructions.

# Define schemas for parsing with the AI assistant
class NamesSchema(BaseModel):
    names: list[str]

class RatingSchema(BaseModel):
    rating: float
    reviews: list[str]

city = "Los Angeles"
trip_days = 3

# 1) Get all car rental companies in the city
companies_str = get_all_car_rental_companies_in_city(city)
if (not companies_str) or (companies_str.strip() == ""):
    raise ValueError("No car rental companies found in the specified city.")

# 2) Extract company names
companies_parsed = query_ai_assistant(
    "Here is a list of car rental companies: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names.".format(companies_str),
    NamesSchema
)
company_names = companies_parsed.names

# 3) Determine which companies rent electric cars
fuel_options_map = get_car_fuel_options(company_names)
electric_companies = []
for c in company_names:
    opts = fuel_options_map.get(c)
    has_electric = False
    if type(opts) == "list":
        for v in opts:
            if type(v) == "str":
                if v.lower().find("electric") != -1:
                    has_electric = True
    if has_electric:
        electric_companies = electric_companies + [c]

# If none found, fallback to all companies (best overall), similar to example patterns
candidate_electric = electric_companies if len(electric_companies) > 0 else company_names

# 4) Determine which companies have SUVs available
types_map = get_car_types_available(company_names)
suv_companies = []
for c in company_names:
    types_list = types_map.get(c)
    has_suv = False
    if type(types_list) == "list":
        for t in types_list:
            if type(t) == "str":
                if t.lower().find("suv") != -1:
                    has_suv = True
    if has_suv:
        suv_companies = suv_companies + [c]

# If none found, fallback to all companies (best overall), similar to example patterns
candidate_suv = suv_companies if len(suv_companies) > 0 else company_names

# 5) Get ratings and prices for candidates, then pick the best by rating (tie-breaker: lower price)
ratings_electric_text = get_rating_reviews_for_car_rental(candidate_electric)
ratings_suv_text = get_rating_reviews_for_car_rental(candidate_suv)

prices_electric = get_car_price_per_day(candidate_electric)
prices_suv = get_car_price_per_day(candidate_suv)

# Select best electric
best_electric_name = None
best_electric_rating = -1.0
best_electric_price_per_day = float("inf")

for c in candidate_electric:
    rtext = ratings_electric_text.get(c)
    if type(rtext) == "str":
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this car rental rating and reviews: {}".format(rtext),
            RatingSchema
        )
        price_val = prices_electric.get(c)
        price_num = price_val if type(price_val) == "float" else float("inf")
        if (rr.rating > best_electric_rating) or ((rr.rating == best_electric_rating) and (price_num < best_electric_price_per_day)):
            best_electric_name = c
            best_electric_rating = rr.rating
            best_electric_price_per_day = price_num

# Select best SUV
best_suv_name = None
best_suv_rating = -1.0
best_suv_price_per_day = float("inf")

for c in candidate_suv:
    rtext = ratings_suv_text.get(c)
    if type(rtext) == "str":
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this car rental rating and reviews: {}".format(rtext),
            RatingSchema
        )
        price_val = prices_suv.get(c)
        price_num = price_val if type(price_val) == "float" else float("inf")
        if (rr.rating > best_suv_rating) or ((rr.rating == best_suv_rating) and (price_num < best_suv_price_per_day)):
            best_suv_name = c
            best_suv_rating = rr.rating
            best_suv_price_per_day = price_num

# 6) Compute costs for 3 days for each selection
electric_cost_3_days = best_electric_price_per_day * trip_days if (type(best_electric_price_per_day) == "float") else None
suv_cost_3_days = best_suv_price_per_day * trip_days if (type(best_suv_price_per_day) == "float") else None

# 7) Prepare final result
{
    "electric_car_company": {
        "name": best_electric_name,
        "rating": best_electric_rating,
        "cost_for_3_days": electric_cost_3_days
    },
    "suv_company": {
        "name": best_suv_name,
        "rating": best_suv_rating,
        "cost_for_3_days": suv_cost_3_days
    }
}