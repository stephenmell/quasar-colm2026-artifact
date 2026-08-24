city = "Los Angeles"

companies_str = get_all_car_rental_companies_in_city(city)
if (not companies_str) or (len(companies_str.strip()) == 0):
    raise ValueError("No car rental companies found for the specified city.")

class NamesSchema(BaseModel):
    names: list[str]

companies_extracted = query_ai_assistant(
    "Here is a list of car rental companies: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names and order.".format(companies_str),
    NamesSchema
)
company_names = companies_extracted.names
if len(company_names) == 0:
    raise ValueError("No car rental companies could be identified from the search results.")

car_types = get_car_types_available(company_names)

suv_companies = []
for name in company_names:
    available_types = car_types.get(name)
    has_suv = False
    if (available_types is not None) and (type(available_types) == "list"):
        for t in available_types:
            if (type(t) == "str") and (t.lower().find("suv") != -1):
                has_suv = True
    if has_suv:
        suv_companies = suv_companies + [name]

if len(suv_companies) == 0:
    raise ValueError("No car rental companies with SUVs available were found in the specified city.")

ratings_texts = get_rating_reviews_for_car_rental(suv_companies)

class RatingSchema(BaseModel):
    rating: float
    reviews: list[str]

best_company = None
best_rating = -1.0
best_reviews_count = -1

for comp in suv_companies:
    rating_text = ratings_texts.get(comp)
    rr = query_ai_assistant(
        "From this car rental rating and reviews text, extract ONLY the numeric rating as a float and the list of review strings: {}".format(rating_text),
        RatingSchema
    )
    reviews_count = len(rr.reviews)
    if (rr.rating > best_rating) or ((rr.rating == best_rating) and (reviews_count > best_reviews_count)):
        best_company = comp
        best_rating = rr.rating
        best_reviews_count = reviews_count

{
    "company_name": best_company,
    "rating": best_rating
}