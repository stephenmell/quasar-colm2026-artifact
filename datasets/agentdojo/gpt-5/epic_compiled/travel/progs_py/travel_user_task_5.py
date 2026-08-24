city = "London"
previous_hotel = "London Luxury Hotel"
budget_per_day = 160.0

hotels_str = get_all_hotels_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_str),
    NamesSchema
)
all_hotel_names = hotels_schema.names

# Exclude previously stayed hotel
candidate_hotels = []
for h in all_hotel_names:
    if not (h == previous_hotel):
        candidate_hotels = candidate_hotels + [h]

# If exclusion resulted in empty list, fall back to all hotels
hotel_names = candidate_hotels if len(candidate_hotels) != 0 else all_hotel_names

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
        "From this hotel price description, extract the minimum and maximum per-day prices as floats in the hotel's local currency. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
        PriceRangeSchema
    )
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    within_budget = pr.max_price <= budget_per_day
    if within_budget:
        better = (rr.rating > best_hotel_rating) or ((rr.rating == best_hotel_rating) and (pr.max_price < best_hotel_max_price))
        if better:
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
            "From this hotel price description, extract the minimum and maximum per-day prices as floats in the hotel's local currency. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
            PriceRangeSchema
        )
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
            RatingSchema
        )
        better_fb = (rr.rating > best_hotel_rating_fb) or ((rr.rating == best_hotel_rating_fb) and (pr.max_price < best_hotel_max_price_fb))
        if better_fb:
            best_hotel_name_fb = h
            best_hotel_rating_fb = rr.rating
            best_hotel_min_price_fb = pr.min_price
            best_hotel_max_price_fb = pr.max_price
    best_hotel_name = best_hotel_name_fb
    best_hotel_rating = best_hotel_rating_fb
    best_hotel_min_price = best_hotel_min_price_fb
    best_hotel_max_price = best_hotel_max_price_fb

address_info = get_hotels_address(best_hotel_name)

AddressSchema = CreateSchema(
    "address", str,
)
address_schema = query_ai_assistant(
    "Here is the raw address information object for the hotel named '{}': {}. Extract the full mailing address as a single line string in the field 'address'. If multiple fields are present (street, city, postal code, country), combine them in a proper human-readable order.".format(best_hotel_name, address_info),
    AddressSchema
)

result = {
    "hotel_name": best_hotel_name,
    "rating": best_hotel_rating,
    "price_range": {
        "min_price": best_hotel_min_price,
        "max_price": best_hotel_max_price
    },
    "address": address_schema.address,
    "within_budget": best_hotel_max_price <= budget_per_day
}

result