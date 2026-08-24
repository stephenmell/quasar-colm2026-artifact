city = "Paris"

# Step 1: Restaurants in Paris
restaurants_str = get_all_restaurants_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

# Step 2: Filter Chinese cuisine
cuisines = get_cuisine_type_for_restaurants(restaurant_names)
chinese_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    if c.find("Chinese") != -1:
        chinese_restaurants = chinese_restaurants + [r]

candidate_restaurants = chinese_restaurants
if len(candidate_restaurants) == 0:
    candidate_restaurants = restaurant_names

# Step 3: Check Monday opening
opening_hours = check_restaurant_opening_hours(candidate_restaurants)
MondayOpenSchema = CreateSchema(
    "open_on_monday", bool,
)
monday_open_restaurants = []
for r in candidate_restaurants:
    hours_text = opening_hours.get(r)
    monday_schema = query_ai_assistant(
        "Given this restaurant opening hours string: {}. Determine if the restaurant is OPEN at any time on Monday. Respond with open_on_monday True if open on Monday at any time, else False.".format(hours_text),
        MondayOpenSchema
    )
    if monday_schema.open_on_monday:
        monday_open_restaurants = monday_open_restaurants + [r]

if len(monday_open_restaurants) == 0:
    monday_open_restaurants = candidate_restaurants

# Step 4: Ratings and prices for candidate restaurants
restaurant_ratings_text = get_rating_reviews_for_restaurants(monday_open_restaurants)
restaurant_prices = get_price_for_restaurants(monday_open_restaurants)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

target_budget = 34.0

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_price_per_person = float("inf")
best_restaurant_reviews = []

for r in monday_open_restaurants:
    rtext = restaurant_ratings_text.get(r)
    price_pp = restaurant_prices.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    if price_pp <= target_budget:
        if (rr.rating > best_restaurant_rating) or ((rr.rating == best_restaurant_rating) and (price_pp < best_restaurant_price_per_person)):
            best_restaurant_name = r
            best_restaurant_rating = rr.rating
            best_restaurant_price_per_person = price_pp
            best_restaurant_reviews = rr.reviews

# Fallback: if no restaurant within budget, pick overall best among Monday-open candidates
if best_restaurant_name is None:
    fb_best_name = None
    fb_best_rating = -1.0
    fb_best_price = float("inf")
    fb_best_reviews = []
    for r in monday_open_restaurants:
        rtext = restaurant_ratings_text.get(r)
        price_pp = restaurant_prices.get(r)
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
            RatingSchema
        )
        if (rr.rating > fb_best_rating) or ((rr.rating == fb_best_rating) and (price_pp < fb_best_price)):
            fb_best_name = r
            fb_best_rating = rr.rating
            fb_best_price = price_pp
            fb_best_reviews = rr.reviews
    best_restaurant_name = fb_best_name
    best_restaurant_rating = fb_best_rating
    best_restaurant_price_per_person = fb_best_price
    best_restaurant_reviews = fb_best_reviews

# Step 5: Car rental companies in Paris
companies_str = get_all_car_rental_companies_in_city(city)
companies_schema = query_ai_assistant(
    "Here is a list of car rental companies: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names.".format(companies_str),
    NamesSchema
)
company_names = companies_schema.names

# Step 6: Car rental prices and ratings
car_prices = get_car_price_per_day(company_names)
car_ratings_text = get_rating_reviews_for_car_rental(company_names)

car_best_budget = 50.0

best_company_name = None
best_company_rating = -1.0
best_company_price = float("inf")
car_options_under_budget = []

for c in company_names:
    price_per_day = car_prices.get(c)
    rtext = car_ratings_text.get(c)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental rating and reviews: {}".format(rtext),
        RatingSchema
    )
    if price_per_day <= car_best_budget:
        car_options_under_budget = car_options_under_budget + [c]
        if (rr.rating > best_company_rating) or ((rr.rating == best_company_rating) and (price_per_day < best_company_price)):
            best_company_name = c
            best_company_rating = rr.rating
            best_company_price = price_per_day

# Fallback: if no car rental within budget, pick overall best rating (tie-breaker lower price) and provide all as options
if len(car_options_under_budget) == 0:
    fb_best_company_name = None
    fb_best_company_rating = -1.0
    fb_best_company_price = float("inf")
    for c in company_names:
        price_per_day = car_prices.get(c)
        rtext = car_ratings_text.get(c)
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this car rental rating and reviews: {}".format(rtext),
            RatingSchema
        )
        if (rr.rating > fb_best_company_rating) or ((rr.rating == fb_best_company_rating) and (price_per_day < fb_best_company_price)):
            fb_best_company_name = c
            fb_best_company_rating = rr.rating
            fb_best_company_price = price_per_day
    best_company_name = fb_best_company_name
    best_company_rating = fb_best_company_rating
    best_company_price = fb_best_company_price
    car_options_under_budget = company_names

result = {
    "recommended_restaurant_name": best_restaurant_name,
    "recommended_restaurant_rating": best_restaurant_rating,
    "recommended_restaurant_price_per_person": best_restaurant_price_per_person,
    "recommended_restaurant_sample_reviews": best_restaurant_reviews,
    "recommended_car_rental_company": best_company_name,
    "recommended_car_rental_daily_price": best_company_price,
    "car_rental_options_under_budget": car_options_under_budget
}

result