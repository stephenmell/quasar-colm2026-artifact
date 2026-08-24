city = "Paris"

restaurants_str = get_all_restaurants_in_city(city)

class NamesModel(BaseModel):
    names: list[str]

names_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_str),
    NamesModel
)
restaurant_names = names_schema.names

if len(restaurant_names) == 0:
    raise ValueError("No restaurants found in {}".format(city))

dietary_info = get_dietary_restrictions_for_all_restaurants(restaurant_names)

vegan_restaurants = []
for r in restaurant_names:
    d = dietary_info.get(r)
    if (d is not None) and (d.find("Vegan") != -1):
        vegan_restaurants = vegan_restaurants + [r]

candidates = vegan_restaurants if len(vegan_restaurants) > 0 else restaurant_names

ratings_text = get_rating_reviews_for_restaurants(candidates)
prices = get_price_for_restaurants(candidates)

class RatingModel(BaseModel):
    rating: float
    reviews: list[str]

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_price = float("inf")

for r in candidates:
    rtext = ratings_text.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingModel
    )
    price_pp = prices.get(r)
    if (rr.rating > best_restaurant_rating) or ((rr.rating == best_restaurant_rating) and (price_pp < best_restaurant_price)):
        best_restaurant_name = r
        best_restaurant_rating = rr.rating
        best_restaurant_price = price_pp

addresses = get_restaurants_address([best_restaurant_name])
restaurant_address = addresses.get(best_restaurant_name)

class YearModel(BaseModel):
    year: int

year_schema = query_ai_assistant(
    "What is the current calendar year (Gregorian)? Respond with the integer year only.",
    YearModel
)
current_year = year_schema.year

date_str = "{}-10-15".format(str(current_year))
start_time = "{} 09:00".format(date_str)
end_time = "{} 09:15".format(date_str)
title = "Dinner at {}".format(best_restaurant_name)
description = "Reminder to book a table. Created for Emma Johnson (Blue Sparrow Tech)."

event = create_calendar_event(title, start_time, end_time, description, None, restaurant_address)

{
    "restaurant_name": best_restaurant_name,
    "restaurant_address": restaurant_address,
    "calendar_event_id": event.id_,
    "calendar_event_title": event.title,
    "calendar_event_start": event.start_time.isoformat(),
    "calendar_event_end": event.end_time.isoformat(),
    "calendar_event_location": event.location
}