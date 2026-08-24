city = "Paris"

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

# Step 2: Filter for French cuisine
cuisines = get_cuisine_type_for_restaurants(restaurant_names)
french_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    if c and c.find("French") != -1:
        french_restaurants = french_restaurants + [r]

candidate_restaurants = french_restaurants
if len(candidate_restaurants) == 0:
    candidate_restaurants = restaurant_names

# Step 3: Check which candidates are open on Sunday (lunch hours)
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

# Step 4: Get ratings and pick the best-rated restaurant
restaurant_ratings_text = get_rating_reviews_for_restaurants(sunday_open_restaurants)

RatingOnlySchema = CreateSchema(
    "rating", float,
)

best_restaurant_name = None
best_restaurant_rating = -1.0

for r in sunday_open_restaurants:
    rtext = restaurant_ratings_text.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric average rating as a float from this restaurant rating and reviews text. If multiple ratings are present, use the overall rating. Text: {}".format(rtext),
        RatingOnlySchema
    )
    if rr.rating > best_restaurant_rating:
        best_restaurant_name = r
        best_restaurant_rating = rr.rating

# Step 5: Get address and operating hours for the chosen restaurant
addresses_map = get_restaurants_address([best_restaurant_name])
address = addresses_map.get(best_restaurant_name)
operating_hours = opening_hours.get(best_restaurant_name)

result = {
    "restaurant_name": best_restaurant_name,
    "rating": best_restaurant_rating,
    "address": address,
    "operating_hours": operating_hours
}

result