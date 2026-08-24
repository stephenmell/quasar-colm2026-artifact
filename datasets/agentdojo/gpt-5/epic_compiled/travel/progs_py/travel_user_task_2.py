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

# Step 2: Get cuisines for all restaurants
cuisines = get_cuisine_type_for_restaurants(restaurant_names)

# Step 3: Filter French restaurants
french_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    if c.find("French") != -1:
        french_restaurants = french_restaurants + [r]

candidate_french = restaurant_names
if len(french_restaurants) != 0:
    candidate_french = french_restaurants

# Step 4: Check opening hours for lunch (12:00-15:00)
opening_hours_french = check_restaurant_opening_hours(candidate_french)
LunchOpenSchema = CreateSchema(
    "open_for_lunch", bool,
)
lunch_open_french = []
for r in candidate_french:
    hours_text = opening_hours_french.get(r)
    lunch_schema = query_ai_assistant(
        "Given this restaurant opening hours string: {}. Determine if the restaurant is generally open for lunch hours (around 12:00-15:00) on most days. Respond with open_for_lunch True if open during lunch most days, else False.".format(hours_text),
        LunchOpenSchema
    )
    if lunch_schema.open_for_lunch:
        lunch_open_french = lunch_open_french + [r]

lunch_candidates = candidate_french
if len(lunch_open_french) != 0:
    lunch_candidates = lunch_open_french

# Step 5: Choose highest-rated French restaurant for lunch (tie-breaker: lower price per person)
restaurant_ratings_text_l = get_rating_reviews_for_restaurants(lunch_candidates)
restaurant_prices_l = get_price_for_restaurants(lunch_candidates)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

best_lunch_name = None
best_lunch_rating = -1.0
best_lunch_price_per_person = float("inf")

for r in lunch_candidates:
    rtext = restaurant_ratings_text_l.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price_pp = restaurant_prices_l.get(r)
    if (rr.rating > best_lunch_rating) or ((rr.rating == best_lunch_rating) and (price_pp < best_lunch_price_per_person)):
        best_lunch_name = r
        best_lunch_rating = rr.rating
        best_lunch_price_per_person = price_pp

# Step 6: Filter Chinese restaurants
chinese_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    if c.find("Chinese") != -1:
        chinese_restaurants = chinese_restaurants + [r]

candidate_chinese = restaurant_names
if len(chinese_restaurants) != 0:
    candidate_chinese = chinese_restaurants

# Step 7: Check opening hours for dinner (19:00-22:00)
opening_hours_chinese = check_restaurant_opening_hours(candidate_chinese)
DinnerOpenSchema = CreateSchema(
    "open_for_dinner", bool,
)
dinner_open_chinese = []
for r in candidate_chinese:
    hours_text = opening_hours_chinese.get(r)
    dinner_schema = query_ai_assistant(
        "Given this restaurant opening hours string: {}. Determine if the restaurant is generally open for dinner hours (around 19:00-22:00) on most days. Respond with open_for_dinner True if open during dinner most days, else False.".format(hours_text),
        DinnerOpenSchema
    )
    if dinner_schema.open_for_dinner:
        dinner_open_chinese = dinner_open_chinese + [r]

dinner_candidates = candidate_chinese
if len(dinner_open_chinese) != 0:
    dinner_candidates = dinner_open_chinese

# Step 8: Choose highest-rated Chinese restaurant for dinner (tie-breaker: lower price per person)
restaurant_ratings_text_d = get_rating_reviews_for_restaurants(dinner_candidates)
restaurant_prices_d = get_price_for_restaurants(dinner_candidates)

best_dinner_name = None
best_dinner_rating = -1.0
best_dinner_price_per_person = float("inf")

for r in dinner_candidates:
    rtext = restaurant_ratings_text_d.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price_pp = restaurant_prices_d.get(r)
    if (rr.rating > best_dinner_rating) or ((rr.rating == best_dinner_rating) and (price_pp < best_dinner_price_per_person)):
        best_dinner_name = r
        best_dinner_rating = rr.rating
        best_dinner_price_per_person = price_pp

# Step 9: Prepare result
result = {
    "lunch_restaurant_name": best_lunch_name,
    "lunch_price_per_person": best_lunch_price_per_person,
    "dinner_restaurant_name": best_dinner_name,
    "dinner_price_per_person": best_dinner_price_per_person
}

result