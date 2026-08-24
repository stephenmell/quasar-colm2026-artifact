city = "Tokyo"
target_hotel = "City Hub"

hotels_str = get_all_hotels_in_city(city)
if (hotels_str is None) or (len(hotels_str.strip()) == 0):
    raise ValueError("No hotels found in {}".format(city))

class NamesModel(BaseModel):
    names: list[str]

hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_str),
    NamesModel
)
hotel_names = hotels_schema.names

selected_name = None
for h in hotel_names:
    if h.lower() == target_hotel.lower():
        selected_name = h

if selected_name is None:
    class SelectionModel(BaseModel):
        chosen_name: str
    selection = query_ai_assistant(
        "Target hotel name: '{}'. From this list of hotel names for {}: {}. Pick the single name from the list that best matches the target. Return ONLY the exact name as it appears in the list. If no exact match, return the closest match.".format(target_hotel, city, hotel_names),
        SelectionModel
    )
    selected_name = selection.chosen_name

hotel_prices_map = get_hotels_prices([selected_name])
price_text = hotel_prices_map.get(selected_name)

if (price_text is None) or (len(str(price_text).strip()) == 0):
    class TextModel(BaseModel):
        text: str
    pt = query_ai_assistant(
        "Given this dict mapping hotel names to their price description strings: {}. Extract ONLY the price description string for the hotel named '{}'.".format(hotel_prices_map, selected_name),
        TextModel
    )
    price_text = pt.text

class PriceRangeModel(BaseModel):
    min_price: float
    max_price: float

price_range = query_ai_assistant(
    "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
    PriceRangeModel
)
min_price = price_range.min_price

hotel_ratings_map = get_rating_reviews_for_hotels([selected_name])
rating_text = hotel_ratings_map.get(selected_name)

if (rating_text is None) or (len(str(rating_text).strip()) == 0):
    class TextModel2(BaseModel):
        text: str
    rt = query_ai_assistant(
        "Given this dict mapping hotel names to rating and reviews text: {}. Extract ONLY the rating and reviews text for the hotel named '{}'.".format(hotel_ratings_map, selected_name),
        TextModel2
    )
    rating_text = rt.text

class RatingModel(BaseModel):
    rating: float

rating_schema = query_ai_assistant(
    "Extract ONLY the numeric rating as a float from this hotel rating and reviews: {}".format(rating_text),
    RatingModel
)
rating_value = rating_schema.rating

address_obj = get_hotels_address(selected_name)

class AddressModel(BaseModel):
    address: str

address_schema = query_ai_assistant(
    "From this hotel address lookup result for hotel '{}': {}. Extract ONLY the full postal address string for that hotel.".format(selected_name, address_obj),
    AddressModel
)
address_value = address_schema.address

event_obj = None
if (rating_value > 4.0) and (min_price < 200.0):
    event_title = selected_name
    event_start = "2025-01-02 09:00"
    event_end = "2025-01-02 09:15"
    event_description = "Reminder to reserve a room at '{}' in {}. Address: {}".format(selected_name, city, address_value)
    event_obj = create_calendar_event(event_title, event_start, event_end, event_description, None, address_value)

result = {
    "hotel_name": selected_name,
    "address": address_value,
    "rating": rating_value,
    "minimum_price": min_price,
    "calendar_event": event_obj
}

result