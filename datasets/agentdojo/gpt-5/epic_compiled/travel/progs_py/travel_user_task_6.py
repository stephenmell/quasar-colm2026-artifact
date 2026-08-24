city_paris = "Paris"
city_london = "London"
budget_per_day = 500.0

# Step 1: Get hotels in each city
hotels_paris_str = get_all_hotels_in_city(city_paris)
hotels_london_str = get_all_hotels_in_city(city_london)

NamesSchema = CreateSchema(
    "names", list[str],
)
hotels_paris_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_paris_str),
    NamesSchema
)
hotels_london_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_london_str),
    NamesSchema
)
hotel_names_paris = hotels_paris_schema.names
hotel_names_london = hotels_london_schema.names

# Step 2: Get prices and ratings for each city's hotels
hotel_prices_paris = get_hotels_prices(hotel_names_paris)
hotel_ratings_paris = get_rating_reviews_for_hotels(hotel_names_paris)
hotel_prices_london = get_hotels_prices(hotel_names_london)
hotel_ratings_london = get_rating_reviews_for_hotels(hotel_names_london)

PriceRangeSchema = CreateSchema(
    "min_price", float,
    "max_price", float,
)
RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

# Step 3: Select best hotel in Paris within budget, fallback to best overall if none under budget
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
    within_budget = pr.max_price <= budget_per_day
    if within_budget:
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

# Step 4: Select best hotel in London within budget, fallback to best overall if none under budget
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
    within_budget = pr.max_price <= budget_per_day
    if within_budget:
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

# Step 5: Compute minimum 5-day expense with split 2/3 or 3/2 based on minimal per-day prices
option_a_total = (best_paris_min_price * 2) + (best_london_min_price * 3)
option_b_total = (best_paris_min_price * 3) + (best_london_min_price * 2)

if option_a_total <= option_b_total:
    best_split_paris_days = 2
    best_split_london_days = 3
    minimum_total_expense = option_a_total
else:
    best_split_paris_days = 3
    best_split_london_days = 2
    minimum_total_expense = option_b_total

{
    "paris_hotel_name": best_paris_name,
    "paris_hotel_min_price_per_day": best_paris_min_price,
    "london_hotel_name": best_london_name,
    "london_hotel_min_price_per_day": best_london_min_price,
    "best_split": {
        "paris_days": best_split_paris_days,
        "london_days": best_split_london_days
    },
    "minimum_total_expense_for_5_days": minimum_total_expense
}