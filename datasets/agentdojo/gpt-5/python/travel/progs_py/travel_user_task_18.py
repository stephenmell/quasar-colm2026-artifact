city = "Paris"

# Step 1: Get all restaurants in the city
restaurants_str = get_all_restaurants_in_city(city)
if (restaurants_str is None) or (len(restaurants_str.strip()) == 0):
    raise ValueError("No restaurants found for the specified city.")

# Define schemas for AI parsing
class NamesSchema(BaseModel):
    names: list[str]

class RatingSchema(BaseModel):
    rating: float
    reviews: list[str]

class MondayOpenSchema(BaseModel):
    open_on_monday: bool

# Extract restaurant names
restaurants_schema = query_ai_assistant(
    "Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names, from this listing text: {}".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

# Step 2: Filter Chinese cuisine
cuisines = get_cuisine_type_for_restaurants(restaurant_names)
chinese_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    if (type(c) == "str") and (c.lower().find("chinese") != -1):
        chinese_restaurants = chinese_restaurants + [r]

candidate_restaurants = chinese_restaurants if len(chinese_restaurants) > 0 else restaurant_names

# Step 3: Check Monday opening
opening_hours = check_restaurant_opening_hours(candidate_restaurants)
monday_open_restaurants = []
for r in candidate_restaurants:
    hours_text = opening_hours.get(r)
    monday_schema = query_ai_assistant(
        "Given this restaurant opening hours string: {}. Determine if the restaurant is OPEN on Mondays during any typical dining hours (lunch or dinner). Respond with open_on_monday True if open on Monday at any time, else False.".format(hours_text),
        MondayOpenSchema
    )
    if monday_schema.open_on_monday:
        monday_open_restaurants = monday_open_restaurants + [r]

if len(monday_open_restaurants) == 0:
    monday_open_restaurants = candidate_restaurants

# Step 4: Filter by price (<= 34 per person)
restaurant_prices = get_price_for_restaurants(monday_open_restaurants)
affordable_restaurants = []
for r in monday_open_restaurants:
    price_pp = restaurant_prices.get(r)
    if (type(price_pp) == "float") and (price_pp <= 34.0):
        affordable_restaurants = affordable_restaurants + [r]

final_restaurant_pool = affordable_restaurants if len(affordable_restaurants) > 0 else monday_open_restaurants

# Step 5: Choose best-rated restaurant (tie-breaker: lower price)
restaurant_ratings_text = get_rating_reviews_for_restaurants(final_restaurant_pool)

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_price = float("inf")

for r in final_restaurant_pool:
    rtext = restaurant_ratings_text.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price_pp = restaurant_prices.get(r) if restaurant_prices.get(r) is not None else float("inf")
    if (rr.rating > best_restaurant_rating) or ((rr.rating == best_restaurant_rating) and (price_pp < best_restaurant_price)):
        best_restaurant_name = r
        best_restaurant_rating = rr.rating
        best_restaurant_price = price_pp

# Step 6: Car rentals in the city
car_rentals_str = get_all_car_rental_companies_in_city(city)
if (car_rentals_str is None) or (len(car_rentals_str.strip()) == 0):
    raise ValueError("No car rental companies found for the specified city.")

car_companies_schema = query_ai_assistant(
    "Extract ONLY the car rental company names as a clean JSON list of strings, preserving exact names, from this listing text: {}".format(car_rentals_str),
    NamesSchema
)
car_company_names = car_companies_schema.names

# Step 7: Prices and ratings for car rentals
car_prices = get_car_price_per_day(car_company_names)
car_ratings_text = get_rating_reviews_for_car_rental(car_company_names)

affordable_companies = []
for c in car_company_names:
    p = car_prices.get(c)
    if (type(p) == "float") and (p <= 50.0):
        affordable_companies = affordable_companies + [c]

candidate_companies = affordable_companies if len(affordable_companies) > 0 else car_company_names

# Parse ratings for candidates and pick best-rated; also prepare a few options
company_tuples = []
for c in candidate_companies:
    rtext = car_ratings_text.get(c)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental company rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price = car_prices.get(c) if car_prices.get(c) is not None else float("inf")
    company_tuples = company_tuples + [(c, rr.rating, price)]

# Sort by rating desc, then price asc, then name asc for determinism
sorted_companies = sorted(company_tuples, key=lambda x: (-x[1], x[2], x[0]))

best_car_company_name = sorted_companies[0][0]
# "a few options" -> top 3 names from the sorted list
top_options_count = 3 if len(sorted_companies) >= 3 else len(sorted_companies)
top_options = [sorted_companies[i][0] for i in range(top_options_count)]

result = {
    "restaurant_name": best_restaurant_name,
    "car_rental_company_name": best_car_company_name,
    "affordable_car_rental_options": top_options
}

result