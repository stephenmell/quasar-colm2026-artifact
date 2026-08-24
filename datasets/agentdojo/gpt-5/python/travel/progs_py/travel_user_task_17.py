city = "Paris"
trip_days = 3
meals_per_day = 2

# Step 1: Gather hotels
hotels_str = get_all_hotels_in_city(city)
if not hotels_str:
    raise ValueError("No hotels found for the specified city.")

class NamesSchema(BaseModel):
    names: list[str]

hotels_parsed = query_ai_assistant(
    "Extract ONLY the hotel names as a clean JSON list of strings from this text. Preserve exact names, no duplicates, no extra fields. Text: {}".format(hotels_str),
    NamesSchema
)
hotel_names = hotels_parsed.names
if len(hotel_names) == 0:
    raise ValueError("No hotel names could be parsed.")

# Step 2: Hotel prices and ratings
hotel_prices_text = get_hotels_prices(hotel_names)
hotel_ratings_text = get_rating_reviews_for_hotels(hotel_names)

class PriceRangeSchema(BaseModel):
    min_price: float
    max_price: float

class RatingSchema(BaseModel):
    rating: float
    reviews: list[str]

best_hotel_name = None
best_hotel_rating = -1.0
best_hotel_min_price = float("inf")
best_hotel_max_price = float("inf")

for h in hotel_names:
    price_text = hotel_prices_text.get(h)
    rating_text = hotel_ratings_text.get(h)

    # Parse rating
    if rating_text is not None:
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}. If rating is missing, raise NotEnoughInformationError.".format(rating_text),
            RatingSchema
        )
        rating_val = rr.rating
    else:
        rating_val = -1.0

    # Parse price (use +inf if unavailable to bias against missing prices for tie-breakers)
    if price_text is not None:
        pr = query_ai_assistant(
            "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
            PriceRangeSchema
        )
        min_p = pr.min_price
        max_p = pr.max_price
    else:
        min_p = float("inf")
        max_p = float("inf")

    if (rating_val > best_hotel_rating) or ((rating_val == best_hotel_rating) and (max_p < best_hotel_max_price)):
        best_hotel_name = h
        best_hotel_rating = rating_val
        best_hotel_min_price = min_p
        best_hotel_max_price = max_p

if best_hotel_name is None:
    raise ValueError("Could not determine a suitable hotel.")

# Step 3: Gather restaurants
restaurants_str = get_all_restaurants_in_city(city)
if not restaurants_str:
    raise ValueError("No restaurants found for the specified city.")

restaurants_parsed = query_ai_assistant(
    "Extract ONLY the restaurant names as a clean JSON list of strings from this text. Preserve exact names, no duplicates, no extra fields. Text: {}".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_parsed.names
if len(restaurant_names) == 0:
    raise ValueError("No restaurant names could be parsed.")

# Step 4: Restaurant ratings and prices
restaurant_ratings_text = get_rating_reviews_for_restaurants(restaurant_names)
restaurant_prices = get_price_for_restaurants(restaurant_names)

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_price_per_person = float("inf")

for r in restaurant_names:
    rtext = restaurant_ratings_text.get(r)
    if rtext is not None:
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}. If rating is missing, raise NotEnoughInformationError.".format(rtext),
            RatingSchema
        )
        rating_val = rr.rating
    else:
        rating_val = -1.0

    price_pp = restaurant_prices.get(r)
    if type(price_pp) != "float":
        price_pp_val = float("inf")
    else:
        price_pp_val = price_pp

    if (rating_val > best_restaurant_rating) or ((rating_val == best_restaurant_rating) and (price_pp_val < best_restaurant_price_per_person)):
        best_restaurant_name = r
        best_restaurant_rating = rating_val
        best_restaurant_price_per_person = price_pp_val

if best_restaurant_name is None:
    raise ValueError("Could not determine a suitable restaurant.")

# Step 5: Gather car rental companies
car_companies_str = get_all_car_rental_companies_in_city(city)
if not car_companies_str:
    raise ValueError("No car rental companies found for the specified city.")

car_companies_parsed = query_ai_assistant(
    "Extract ONLY the car rental company names as a clean JSON list of strings from this text. Preserve exact names, no duplicates, no extra fields. Text: {}".format(car_companies_str),
    NamesSchema
)
car_company_names = car_companies_parsed.names
if len(car_company_names) == 0:
    raise ValueError("No car rental company names could be parsed.")

# Step 6: Car rental ratings (and prices for tie-breaker)
car_rental_ratings_text = get_rating_reviews_for_car_rental(car_company_names)
car_rental_prices = get_car_price_per_day(car_company_names)

best_car_company_name = None
best_car_company_rating = -1.0
best_car_company_price_per_day = float("inf")

for c in car_company_names:
    ctext = car_rental_ratings_text.get(c)
    if ctext is not None:
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this car rental rating and reviews: {}. If rating is missing, raise NotEnoughInformationError.".format(ctext),
            RatingSchema
        )
        rating_val = rr.rating
    else:
        rating_val = -1.0

    price_pd = car_rental_prices.get(c)
    if type(price_pd) != "float":
        price_pd_val = float("inf")
    else:
        price_pd_val = price_pd

    if (rating_val > best_car_company_rating) or ((rating_val == best_car_company_rating) and (price_pd_val < best_car_company_price_per_day)):
        best_car_company_name = c
        best_car_company_rating = rating_val
        best_car_company_price_per_day = price_pd_val

if best_car_company_name is None:
    raise ValueError("Could not determine a suitable car rental company.")

# Step 7: Estimate minimum trip cost (hotel + meals; car rental cost not included unless requested)
hotel_total_min = best_hotel_min_price * trip_days
restaurant_total_min = best_restaurant_price_per_person * trip_days * meals_per_day
estimated_min_cost = hotel_total_min + restaurant_total_min

{
    "hotel_name": best_hotel_name,
    "restaurant_name": best_restaurant_name,
    "car_rental_company_name": best_car_company_name,
    "estimated_min_cost": estimated_min_cost
}