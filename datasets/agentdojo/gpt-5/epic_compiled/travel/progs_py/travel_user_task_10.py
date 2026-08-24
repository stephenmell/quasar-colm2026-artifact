city = "Paris"
max_price_per_person = 34.0

# Step 1: Get all restaurants in Paris
restaurants_str = get_all_restaurants_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

# Step 2: Filter by Chinese cuisine
cuisines = get_cuisine_type_for_restaurants(restaurant_names)
chinese_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    if c.find("Chinese") != -1:
        chinese_restaurants = chinese_restaurants + [r]

candidate_restaurants = chinese_restaurants
if len(candidate_restaurants) == 0:
    candidate_restaurants = restaurant_names

# Step 3: Filter by price per person under or equal to 34
restaurant_prices = get_price_for_restaurants(candidate_restaurants)
affordable_restaurants = []
for r in candidate_restaurants:
    price_pp = restaurant_prices.get(r)
    if price_pp <= max_price_per_person:
        affordable_restaurants = affordable_restaurants + [r]

if len(affordable_restaurants) == 0:
    affordable_restaurants = candidate_restaurants

# Step 4: Check if open on Monday
opening_hours = check_restaurant_opening_hours(affordable_restaurants)
MondayOpenSchema = CreateSchema(
    "open_on_monday", bool,
)
monday_open_restaurants = []
for r in affordable_restaurants:
    hours_text = opening_hours.get(r)
    monday_schema = query_ai_assistant(
        "Given this restaurant opening hours string: {}. Determine if the restaurant is OPEN on Mondays at any time. Respond with open_on_monday True if open on Monday, else False.".format(hours_text),
        MondayOpenSchema
    )
    if monday_schema.open_on_monday:
        monday_open_restaurants = monday_open_restaurants + [r]

if len(monday_open_restaurants) == 0:
    monday_open_restaurants = affordable_restaurants

# Step 5: Get ratings and reviews, choose best by highest rating, then most reviews, then lowest price
restaurant_ratings_text = get_rating_reviews_for_restaurants(monday_open_restaurants)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_reviews_count = -1
best_restaurant_price_per_person = float("inf")
best_restaurant_hours = ""

for r in monday_open_restaurants:
    rtext = restaurant_ratings_text.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price_pp = restaurant_prices.get(r)
    hours_text = opening_hours.get(r)
    reviews_count = len(rr.reviews)

    better = False
    if rr.rating > best_restaurant_rating:
        better = True
    elif rr.rating == best_restaurant_rating:
        if reviews_count > best_restaurant_reviews_count:
            better = True
        elif reviews_count == best_restaurant_reviews_count:
            if price_pp < best_restaurant_price_per_person:
                better = True

    if better:
        best_restaurant_name = r
        best_restaurant_rating = rr.rating
        best_restaurant_reviews_count = reviews_count
        best_restaurant_price_per_person = price_pp
        best_restaurant_hours = hours_text

# Step 6: Get address for the best restaurant
best_address_map = get_restaurants_address([best_restaurant_name])
best_address = best_address_map.get(best_restaurant_name)

result = {
    "restaurant_name": best_restaurant_name,
    "rating": best_restaurant_rating,
    "address": best_address,
    "price_per_person": best_restaurant_price_per_person,
    "operating_hours": best_restaurant_hours
}

result