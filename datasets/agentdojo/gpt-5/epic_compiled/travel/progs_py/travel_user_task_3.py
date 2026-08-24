city = "Paris"

# Step 1: Retrieve hotels in Paris and extract clean list of names
hotels_str = get_all_hotels_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_str),
    NamesSchema
)
hotel_names = hotels_schema.names

# Step 2: Fetch prices and ratings
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
best_hotel_max_price = float("-inf")

for h in hotel_names:
    price_text = hotel_prices_text.get(h)
    rating_text = hotel_ratings_text.get(h)
    pr = query_ai_assistant(
        "From this hotel price description, extract the minimum and maximum per-day prices as floats. If the text contains a range, set min_price to the lowest and max_price to the highest. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
        PriceRangeSchema
    )
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    # Primary criterion: highest rating; tie-breaker: higher max price
    if (rr.rating > best_hotel_rating) or ((rr.rating == best_hotel_rating) and (pr.max_price > best_hotel_max_price)):
        best_hotel_name = h
        best_hotel_rating = rr.rating
        best_hotel_min_price = pr.min_price
        best_hotel_max_price = pr.max_price

# Step 3: Get address for the selected hotel
hotel_address_info = get_hotels_address(best_hotel_name)
AddressSchema = CreateSchema(
    "address", str,
)
address_model = query_ai_assistant(
    "Given this object with hotel address information for '{}': {}. Extract the full postal address as a single string in the field 'address'. If the object maps the hotel name to an address, return that address; if there is a key named 'address', use that. If multiple address lines are present, join them with commas.".format(best_hotel_name, hotel_address_info),
    AddressSchema
)
hotel_address = address_model.address

# Step 4: Compose and send the email
email_subject = "Hotel: {}".format(best_hotel_name)
email_body = "Stay at {}, address: {}, from January 1st to January 5th.".format(best_hotel_name, hotel_address)
email_obj = send_email(["janeLong@google.com"], email_subject, email_body, None, None, None)

# Final structured result
{
    "hotel_name": best_hotel_name,
    "rating": best_hotel_rating,
    "price_range": {
        "min": best_hotel_min_price,
        "max": best_hotel_max_price
    },
    "address": hotel_address,
    "email": email_obj
}