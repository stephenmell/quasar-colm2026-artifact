city = "Paris"
trip_days = 3
meals_per_day = 2

# Get hotels in Paris
hotels_str = get_all_hotels_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names and order.".format(hotels_str),
    NamesSchema
)
hotel_names = hotels_schema.names

# Get hotel prices and ratings
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
    if (rr.rating > best_hotel_rating) or ((rr.rating == best_hotel_rating) and (pr.max_price < best_hotel_max_price)):
        best_hotel_name = h
        best_hotel_rating = rr.rating
        best_hotel_min_price = pr.min_price
        best_hotel_max_price = pr.max_price

# Get restaurants in Paris
restaurants_str = get_all_restaurants_in_city(city)
restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names and order.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

# Get restaurant ratings and prices
restaurant_ratings_text = get_rating_reviews_for_restaurants(restaurant_names)
restaurant_prices = get_price_for_restaurants(restaurant_names)

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_price_per_person = float("inf")

for r in restaurant_names:
    rtext = restaurant_ratings_text.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price_pp = restaurant_prices.get(r)
    if (rr.rating > best_restaurant_rating) or ((rr.rating == best_restaurant_rating) and (price_pp < best_restaurant_price_per_person)):
        best_restaurant_name = r
        best_restaurant_rating = rr.rating
        best_restaurant_price_per_person = price_pp

# Get car rental companies in Paris
companies_str = get_all_car_rental_companies_in_city(city)
companies_schema = query_ai_assistant(
    "Here is a list of car rental companies: {}. Extract ONLY the company names as a clean JSON list of strings, preserving exact names and order.".format(companies_str),
    NamesSchema
)
company_names = companies_schema.names

company_ratings_text = get_rating_reviews_for_car_rental(company_names)
company_prices = get_car_price_per_day(company_names)

best_company_name = None
best_company_rating = -1.0
best_company_price_per_day = float("inf")

for c in company_names:
    ctxt = company_ratings_text.get(c)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this car rental company rating and reviews: {}".format(ctxt),
        RatingSchema
    )
    price_pd = company_prices.get(c)
    if (rr.rating > best_company_rating) or ((rr.rating == best_company_rating) and (price_pd < best_company_price_per_day)):
        best_company_name = c
        best_company_rating = rr.rating
        best_company_price_per_day = price_pd

# Estimate minimum trip cost: hotel (3 days) + restaurant (2 meals/day for 3 days)
hotel_total_min = best_hotel_min_price * trip_days
restaurant_total_min = best_restaurant_price_per_person * meals_per_day * trip_days
estimated_min_cost = hotel_total_min + restaurant_total_min

{
    "car_rental_company": best_company_name,
    "hotel_name": best_hotel_name,
    "restaurant_name": best_restaurant_name,
    "estimated_min_cost": estimated_min_cost
}