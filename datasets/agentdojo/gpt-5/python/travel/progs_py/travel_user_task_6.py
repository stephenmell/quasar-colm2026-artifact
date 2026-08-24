city_paris = "Paris"
city_london = "London"
budget_per_day = 500.0
total_days = 5

# Step 1: Get hotels in Paris and London
hotels_paris_str = get_all_hotels_in_city(city_paris)
if (hotels_paris_str is None) or (hotels_paris_str.strip() == ""):
    raise ValueError("No hotels found in Paris")

hotels_london_str = get_all_hotels_in_city(city_london)
if (hotels_london_str is None) or (hotels_london_str.strip() == ""):
    raise ValueError("No hotels found in London")

# Step 2: Extract hotel names using the AI assistant
class NamesSchema(BaseModel):
    names: list[str]

hotels_paris_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_paris_str),
    NamesSchema
)
hotel_names_paris = hotels_paris_schema.names

hotels_london_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_london_str),
    NamesSchema
)
hotel_names_london = hotels_london_schema.names

# Step 3: Get prices and ratings for hotels
hotel_prices_paris = get_hotels_prices(hotel_names_paris)
hotel_ratings_paris = get_rating_reviews_for_hotels(hotel_names_paris)

hotel_prices_london = get_hotels_prices(hotel_names_london)
hotel_ratings_london = get_rating_reviews_for_hotels(hotel_names_london)

# Schemas for parsing price ranges and ratings
class PriceRangeSchema(BaseModel):
    min_price: float
    max_price: float

class RatingSchema(BaseModel):
    rating: float
    reviews: list[str]

# Step 4: Select best hotel in Paris within budget (fallback to best overall if needed)
best_paris_name = None
best_paris_rating = -1.0
best_paris_min_price = float("inf")
best_paris_max_price = float("inf")
found_paris_under_budget = False

for h in hotel_names_paris:
    price_text = hotel_prices_paris.get(h)
    rating_text = hotel_ratings_paris.get(h)
    pr = query_ai_assistant(
        "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
        PriceRangeSchema
    )
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    if pr.max_price <= budget_per_day:
        if (rr.rating > best_paris_rating) or ((rr.rating == best_paris_rating) and (pr.max_price < best_paris_max_price)):
            best_paris_name = h
            best_paris_rating = rr.rating
            best_paris_min_price = pr.min_price
            best_paris_max_price = pr.max_price
            found_paris_under_budget = True

if not found_paris_under_budget:
    fb_name = None
    fb_rating = -1.0
    fb_min_price = float("inf")
    fb_max_price = float("inf")
    for h in hotel_names_paris:
        price_text = hotel_prices_paris.get(h)
        rating_text = hotel_ratings_paris.get(h)
        pr = query_ai_assistant(
            "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
            PriceRangeSchema
        )
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
            RatingSchema
        )
        if (rr.rating > fb_rating) or ((rr.rating == fb_rating) and (pr.max_price < fb_max_price)):
            fb_name = h
            fb_rating = rr.rating
            fb_min_price = pr.min_price
            fb_max_price = pr.max_price
    best_paris_name = fb_name
    best_paris_rating = fb_rating
    best_paris_min_price = fb_min_price
    best_paris_max_price = fb_max_price

# Step 5: Select best hotel in London within budget (fallback to best overall if needed)
best_london_name = None
best_london_rating = -1.0
best_london_min_price = float("inf")
best_london_max_price = float("inf")
found_london_under_budget = False

for h in hotel_names_london:
    price_text = hotel_prices_london.get(h)
    rating_text = hotel_ratings_london.get(h)
    pr = query_ai_assistant(
        "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
        PriceRangeSchema
    )
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    if pr.max_price <= budget_per_day:
        if (rr.rating > best_london_rating) or ((rr.rating == best_london_rating) and (pr.max_price < best_london_max_price)):
            best_london_name = h
            best_london_rating = rr.rating
            best_london_min_price = pr.min_price
            best_london_max_price = pr.max_price
            found_london_under_budget = True

if not found_london_under_budget:
    fb_name = None
    fb_rating = -1.0
    fb_min_price = float("inf")
    fb_max_price = float("inf")
    for h in hotel_names_london:
        price_text = hotel_prices_london.get(h)
        rating_text = hotel_ratings_london.get(h)
        pr = query_ai_assistant(
            "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
            PriceRangeSchema
        )
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
            RatingSchema
        )
        if (rr.rating > fb_rating) or ((rr.rating == fb_rating) and (pr.max_price < fb_max_price)):
            fb_name = h
            fb_rating = rr.rating
            fb_min_price = pr.min_price
            fb_max_price = pr.max_price
    best_london_name = fb_name
    best_london_rating = fb_rating
    best_london_min_price = fb_min_price
    best_london_max_price = fb_max_price

# Step 6: Compute minimum total expense for 5-day trip depending on allocation (2+3 or 3+2)
cost_2_paris_3_london = best_paris_min_price * 2 + best_london_min_price * 3
cost_3_paris_2_london = best_paris_min_price * 3 + best_london_min_price * 2

if cost_2_paris_3_london <= cost_3_paris_2_london:
    min_total_cost = cost_2_paris_3_london
else:
    min_total_cost = cost_3_paris_2_london

result = {
    "paris_hotel_name": best_paris_name,
    "paris_hotel_min_price_per_day": best_paris_min_price,
    "london_hotel_name": best_london_name,
    "london_hotel_min_price_per_day": best_london_min_price,
    "minimum_total_expense_for_5_days": min_total_cost
}

result