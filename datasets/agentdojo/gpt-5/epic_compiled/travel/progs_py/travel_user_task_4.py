city = "Paris"
budget_per_day = 210.0

# Step 1: Get hotels in Paris
hotels_str = get_all_hotels_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_str),
    NamesSchema
)
hotel_names = hotels_schema.names

# Step 2: Get hotel prices and ratings
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

# Step 3: Get the hotel's address for the calendar location
hotel_address_info = get_hotels_address(best_hotel_name)
AddressSchema = CreateSchema(
    "address", str,
)
address_parsed = query_ai_assistant(
    "You are given a dictionary-like object that contains the address information for a hotel. Extract the complete, human-readable mailing address as a single string, suitable for a calendar location field. Data: {}".format(hotel_address_info),
    AddressSchema
)
hotel_address_str = address_parsed.address

# Step 4: Create the reminder calendar event on April 25th, 2024
event_title = "Booking hotel {}".format(best_hotel_name)
event_start = "2024-04-25 09:00"
event_end = "2024-04-25 09:30"
event_description = "Reminder to book the hotel in Paris from May 1st to May 5th."
calendar_event = create_calendar_event(event_title, event_start, event_end, event_description, None, hotel_address_str)

# Step 5: Prepare the result
result = {
    "hotel_name": best_hotel_name,
    "hotel_rating": best_hotel_rating,
    "price_range_min": best_hotel_min_price,
    "price_range_max": best_hotel_max_price,
    "calendar_event": calendar_event
}

result