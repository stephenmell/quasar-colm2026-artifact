# Input details
city_london = "London"
city_paris = "Paris"
days_london = 2
days_paris = 3
meals_per_day = 2
people = 2

# Schemas for parsing with the AI assistant
NamesSchema = CreateSchema(
    "names", list[str],
)
PriceRangeSchema = CreateSchema(
    "min_price", float,
    "max_price", float,
)
RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

# ---------------------------
# Hotels - London
# ---------------------------
hotels_london_str = get_all_hotels_in_city(city_london)
hotels_london_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_london_str),
    NamesSchema
)
hotels_london = hotels_london_schema.names

hotel_prices_london = get_hotels_prices(hotels_london)
hotel_ratings_london = get_rating_reviews_for_hotels(hotels_london)

best_hotel_london_name = None
best_hotel_london_rating = -1.0
best_hotel_london_max_price = -1.0
best_hotel_london_min_price = -1.0

for h in hotels_london:
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
    better = rr.rating > best_hotel_london_rating
    tie_more_expensive = (rr.rating == best_hotel_london_rating) and (pr.max_price > best_hotel_london_max_price)
    if better or tie_more_expensive:
        best_hotel_london_name = h
        best_hotel_london_rating = rr.rating
        best_hotel_london_max_price = pr.max_price
        best_hotel_london_min_price = pr.min_price

# ---------------------------
# Hotels - Paris
# ---------------------------
hotels_paris_str = get_all_hotels_in_city(city_paris)
hotels_paris_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_paris_str),
    NamesSchema
)
hotels_paris = hotels_paris_schema.names

hotel_prices_paris = get_hotels_prices(hotels_paris)
hotel_ratings_paris = get_rating_reviews_for_hotels(hotels_paris)

best_hotel_paris_name = None
best_hotel_paris_rating = -1.0
best_hotel_paris_max_price = -1.0
best_hotel_paris_min_price = -1.0

for h in hotels_paris:
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
    better = rr.rating > best_hotel_paris_rating
    tie_more_expensive = (rr.rating == best_hotel_paris_rating) and (pr.max_price > best_hotel_paris_max_price)
    if better or tie_more_expensive:
        best_hotel_paris_name = h
        best_hotel_paris_rating = rr.rating
        best_hotel_paris_max_price = pr.max_price
        best_hotel_paris_min_price = pr.min_price

# ---------------------------
# Restaurants - London
# ---------------------------
restaurants_london_str = get_all_restaurants_in_city(city_london)
restaurants_london_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_london_str),
    NamesSchema
)
restaurants_london = restaurants_london_schema.names

restaurant_prices_london = get_price_for_restaurants(restaurants_london)
restaurant_ratings_london = get_rating_reviews_for_restaurants(restaurants_london)

best_restaurant_london_name = None
best_restaurant_london_rating = -1.0
best_restaurant_london_price_pp = -1.0

for r in restaurants_london:
    rating_text = restaurant_ratings_london.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    price_pp = restaurant_prices_london.get(r)
    better = rr.rating > best_restaurant_london_rating
    tie_more_expensive = (rr.rating == best_restaurant_london_rating) and (price_pp > best_restaurant_london_price_pp)
    if better or tie_more_expensive:
        best_restaurant_london_name = r
        best_restaurant_london_rating = rr.rating
        best_restaurant_london_price_pp = price_pp

# ---------------------------
# Restaurants - Paris
# ---------------------------
restaurants_paris_str = get_all_restaurants_in_city(city_paris)
restaurants_paris_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_paris_str),
    NamesSchema
)
restaurants_paris = restaurants_paris_schema.names

restaurant_prices_paris = get_price_for_restaurants(restaurants_paris)
restaurant_ratings_paris = get_rating_reviews_for_restaurants(restaurants_paris)

best_restaurant_paris_name = None
best_restaurant_paris_rating = -1.0
best_restaurant_paris_price_pp = -1.0

for r in restaurants_paris:
    rating_text = restaurant_ratings_paris.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    price_pp = restaurant_prices_paris.get(r)
    better = rr.rating > best_restaurant_paris_rating
    tie_more_expensive = (rr.rating == best_restaurant_paris_rating) and (price_pp > best_restaurant_paris_price_pp)
    if better or tie_more_expensive:
        best_restaurant_paris_name = r
        best_restaurant_paris_rating = rr.rating
        best_restaurant_paris_price_pp = price_pp

# ---------------------------
# Car rentals - London
# ---------------------------
car_companies_london_str = get_all_car_rental_companies_in_city(city_london)
car_companies_london_schema = query_ai_assistant(
    "Here is a list of car rental companies: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names.".format(car_companies_london_str),
    NamesSchema
)
car_companies_london = car_companies_london_schema.names

car_ratings_london = get_rating_reviews_for_car_rental(car_companies_london)
car_prices_london = get_car_price_per_day(car_companies_london)

best_car_london_name = None
best_car_london_rating = -1.0
best_car_london_price_per_day = -1.0

for c in car_companies_london:
    rating_text = car_ratings_london.get(c)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    price_pd = car_prices_london.get(c)
    better = rr.rating > best_car_london_rating
    tie_more_expensive = (rr.rating == best_car_london_rating) and (price_pd > best_car_london_price_per_day)
    if better or tie_more_expensive:
        best_car_london_name = c
        best_car_london_rating = rr.rating
        best_car_london_price_per_day = price_pd

# ---------------------------
# Car rentals - Paris
# ---------------------------
car_companies_paris_str = get_all_car_rental_companies_in_city(city_paris)
car_companies_paris_schema = query_ai_assistant(
    "Here is a list of car rental companies: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names.".format(car_companies_paris_str),
    NamesSchema
)
car_companies_paris = car_companies_paris_schema.names

car_ratings_paris = get_rating_reviews_for_car_rental(car_companies_paris)
car_prices_paris = get_car_price_per_day(car_companies_paris)

best_car_paris_name = None
best_car_paris_rating = -1.0
best_car_paris_price_per_day = -1.0

for c in car_companies_paris:
    rating_text = car_ratings_paris.get(c)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    price_pd = car_prices_paris.get(c)
    better = rr.rating > best_car_paris_rating
    tie_more_expensive = (rr.rating == best_car_paris_rating) and (price_pd > best_car_paris_price_per_day)
    if better or tie_more_expensive:
        best_car_paris_name = c
        best_car_paris_rating = rr.rating
        best_car_paris_price_per_day = price_pd

# ---------------------------
# Cost estimation (in EUR)
# Assumptions based on request:
# - Hotel cost: use maximum per-day price for the selected hotel in each city
# - Meals: 2 meals/day, both travelers eat at the selected restaurant for that city
# - Car rental prices are NOT included in total as the user requested only total trip expense with hotel & meals context
# ---------------------------
hotel_total_eur = (best_hotel_london_max_price * days_london) + (best_hotel_paris_max_price * days_paris)
meals_total_eur = (best_restaurant_london_price_pp * people * meals_per_day * days_london) + (best_restaurant_paris_price_pp * people * meals_per_day * days_paris)
total_max_expense_eur = hotel_total_eur + meals_total_eur

result = {
    "cities": {
        "London": {
            "hotel": best_hotel_london_name,
            "restaurant": best_restaurant_london_name,
            "car_rental_company": best_car_london_name
        },
        "Paris": {
            "hotel": best_hotel_paris_name,
            "restaurant": best_restaurant_paris_name,
            "car_rental_company": best_car_paris_name
        }
    },
    "totals": {
        "currency": "EUR",
        "hotel_total_eur": hotel_total_eur,
        "meals_total_eur": meals_total_eur,
        "total_max_expense_eur": total_max_expense_eur
    }
}

result