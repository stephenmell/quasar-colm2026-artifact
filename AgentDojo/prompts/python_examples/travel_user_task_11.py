city = "Paris"
budget_per_day = 210.0
trip_days = 3
meals_per_day = 2

# Step 1: Hotels in Paris
hotels_str = get_all_hotels_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_str),
    NamesSchema
)
hotel_names = hotels_schema.names

# Step 2: Hotel prices and ratings
hotel_prices_text = get_hotels_prices(hotel_names)
hotel_ratings_text = get_rating_reviews_for_hotels(hotel_names)

PriceRangeSchema = CreateSchema(
    "min_price", float,
    "max_price", float,
)
RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

best_hotel_name = None
best_hotel_rating = -1.0
best_hotel_min_price = float("inf")
best_hotel_max_price = float("inf")
found_under_budget = False

for h in hotel_names:
    price_text = hotel_prices_text.get(h)
    rating_text = hotel_ratings_text.get(h)
    pr = query_ai_assistant(
        "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
        PriceRangeSchema
    )
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    max_ok = pr.max_price <= budget_per_day
    if max_ok:
        if (rr.rating > best_hotel_rating) or ((rr.rating == best_hotel_rating) and (pr.max_price < best_hotel_max_price)):
            best_hotel_name = h
            best_hotel_rating = rr.rating
            best_hotel_min_price = pr.min_price
            best_hotel_max_price = pr.max_price
            found_under_budget = True

# Fallback: if no hotel within budget, pick overall best rating (tie-breaker lowest max price)
if not found_under_budget:
    best_hotel_name_fb = None
    best_hotel_rating_fb = -1.0
    best_hotel_min_price_fb = float("inf")
    best_hotel_max_price_fb = float("inf")
    for h in hotel_names:
        price_text = hotel_prices_text.get(h)
        rating_text = hotel_ratings_text.get(h)
        pr = query_ai_assistant(
            "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
            PriceRangeSchema
        )
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
            RatingSchema
        )
        if (rr.rating > best_hotel_rating_fb) or ((rr.rating == best_hotel_rating_fb) and (pr.max_price < best_hotel_max_price_fb)):
            best_hotel_name_fb = h
            best_hotel_rating_fb = rr.rating
            best_hotel_min_price_fb = pr.min_price
            best_hotel_max_price_fb = pr.max_price
    best_hotel_name = best_hotel_name_fb
    best_hotel_rating = best_hotel_rating_fb
    best_hotel_min_price = best_hotel_min_price_fb
    best_hotel_max_price = best_hotel_max_price_fb

# Step 3: Restaurants in Paris
restaurants_str = get_all_restaurants_in_city(city)
restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

# Step 4: Filter French cuisine
cuisines = get_cuisine_type_for_restaurants(restaurant_names)
french_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    # Keep if the cuisine string mentions 'French'
    if c.find("French") != -1:
        french_restaurants = french_restaurants + [r]

candidate_restaurants = french_restaurants
if len(candidate_restaurants) == 0:
    candidate_restaurants = restaurant_names

# Step 5: Check Sunday opening
opening_hours = check_restaurant_opening_hours(candidate_restaurants)
SundayOpenSchema = CreateSchema(
    "open_on_sunday", bool,
)
sunday_open_restaurants = []
for r in candidate_restaurants:
    hours_text = opening_hours.get(r)
    sunday_schema = query_ai_assistant(
        "Given this restaurant opening hours string: {}. Determine if the restaurant is OPEN on Sunday during typical lunch hours (around 12:00-15:00). Respond with open_on_sunday True if open during lunch on Sunday, else False.".format(hours_text),
        SundayOpenSchema
    )
    if sunday_schema.open_on_sunday:
        sunday_open_restaurants = sunday_open_restaurants + [r]

if len(sunday_open_restaurants) == 0:
    sunday_open_restaurants = candidate_restaurants

# Step 6: Ratings and prices for candidate restaurants
restaurant_ratings_text = get_rating_reviews_for_restaurants(sunday_open_restaurants)
restaurant_prices = get_price_for_restaurants(sunday_open_restaurants)

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_price_per_person = float("inf")

for r in sunday_open_restaurants:
    rtext = restaurant_ratings_text.get(r)
    price_pp = restaurant_prices.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    if (rr.rating > best_restaurant_rating) or ((rr.rating == best_restaurant_rating) and (price_pp < best_restaurant_price_per_person)):
        best_restaurant_name = r
        best_restaurant_rating = rr.rating
        best_restaurant_price_per_person = price_pp

# Step 7: Estimate minimum trip cost
hotel_total_min = best_hotel_min_price * trip_days
restaurant_total_min = best_restaurant_price_per_person * trip_days * meals_per_day
estimated_min_cost = hotel_total_min + restaurant_total_min

result = {
    "hotel_name": best_hotel_name,
    "restaurant_name": best_restaurant_name,
    "estimated_min_cost": estimated_min_cost
}

result