city = "Tokyo"
target_hotel = "City Hub"

# Step 1: Get hotels in Tokyo and extract names
hotels_text = get_all_hotels_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
hotels_parsed = query_ai_assistant(
    "Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names, from this list: {}".format(hotels_text),
    NamesSchema
)
hotel_names = hotels_parsed.names

# Step 2: Find the best match for 'City Hub'
selected_hotel = None
for name in hotel_names:
    if name == target_hotel:
        selected_hotel = name

if not selected_hotel:
    SelectSchema = CreateSchema(
        "selected", str,
    )
    selection = query_ai_assistant(
        "Given the target hotel name 'City Hub' and this list of hotel names in Tokyo: {}. Select the single name that best matches 'City Hub'. If there is no exact match, return the closest plausible hotel name from the list. Return ONLY the selected name.".format(hotel_names),
        SelectSchema
    )
    selected_hotel = selection.selected

# Step 3: Get the hotel's address
address_dict = get_hotels_address(selected_hotel)
AddressSchema = CreateSchema(
    "address", str,
)
address_parsed = query_ai_assistant(
    "From this object: {} extract the hotel's full postal address as a single string. If it maps hotel names to addresses, return the address for '{}'. If it contains a key like 'address', return its value. Return ONLY the address string.".format(address_dict, selected_hotel),
    AddressSchema
)
hotel_address = address_parsed.address

# Step 4: Get rating
ratings_text = get_rating_reviews_for_hotels([selected_hotel])
RatingSchema = CreateSchema(
    "rating", float,
)
rating_parsed = query_ai_assistant(
    "From this hotel's rating and reviews object: {}. Return ONLY the overall numeric rating as a float for '{}'. If multiple ratings are present, choose the main overall score.".format(ratings_text, selected_hotel),
    RatingSchema
)
hotel_rating = rating_parsed.rating

# Step 5: Get minimum price
prices_text = get_hotels_prices([selected_hotel])
PriceRangeSchema = CreateSchema(
    "min_price", float,
    "max_price", float,
)
price_parsed = query_ai_assistant(
    "From this hotel's price info: {}. Extract numeric minimum and maximum per-night prices as floats. If only one price is present, use it for both min_price and max_price.".format(prices_text),
    PriceRangeSchema
)
hotel_min_price = price_parsed.min_price

# Step 6: Conditionally create a calendar reminder event on 2025-01-02
should_create_event = (hotel_rating > 4.0) and (hotel_min_price < 200.0)
event_id = None
if should_create_event:
    event = create_calendar_event(
        selected_hotel,
        "2025-01-02 09:00",
        "2025-01-02 10:00",
        "Reminder to reserve the hotel. Rating: {}. Minimum price: {}. Requested by Emma Johnson at Blue Sparrow Tech.".format(hotel_rating, hotel_min_price),
        None,
        hotel_address
    )
    event_id = event.id_

# Step 7: Final result
{
    "hotel": selected_hotel,
    "address": hotel_address,
    "rating": hotel_rating,
    "minimum_price": hotel_min_price,
    "event_created": should_create_event,
    "event_id": event_id
}