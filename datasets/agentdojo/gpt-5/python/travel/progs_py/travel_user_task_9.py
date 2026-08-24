from typing import List

city = "Paris"

class NamesSchema(BaseModel):
    names: list[str]

class SundayOpenSchema(BaseModel):
    open_on_sunday: bool

class RatingSchema(BaseModel):
    rating: float
    reviews: list[str]

restaurants_str = get_all_restaurants_in_city(city)
if not restaurants_str or (type(restaurants_str) == "str" and len(restaurants_str.strip()) == 0):
    raise ValueError("No restaurants found for the specified city.")

restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

if len(restaurant_names) == 0:
    raise ValueError("No restaurants found after parsing results.")

cuisines = get_cuisine_type_for_restaurants(restaurant_names)
french_restaurants = [r for r in restaurant_names if (cuisines.get(r) or "").lower().find("french") != -1]

if len(french_restaurants) == 0:
    raise ValueError("No French cuisine restaurants found in the specified city.")

opening_hours_map = check_restaurant_opening_hours(french_restaurants)
sunday_open_restaurants = []
for r in french_restaurants:
    hours_text = opening_hours_map.get(r)
    sunday_schema = query_ai_assistant(
        "Given this restaurant opening hours string: {}. Determine if the restaurant is OPEN at any time on Sunday. Respond with open_on_sunday True if open any time on Sunday, else False.".format(hours_text),
        SundayOpenSchema
    )
    if sunday_schema.open_on_sunday:
        sunday_open_restaurants = sunday_open_restaurants + [r]

if len(sunday_open_restaurants) == 0:
    raise ValueError("No French restaurants open on Sunday were found in the specified city.")

ratings_text_map = get_rating_reviews_for_restaurants(sunday_open_restaurants)

best_restaurant_name = None
best_restaurant_rating = -1.0

for r in sunday_open_restaurants:
    rtext = ratings_text_map.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    if rr.rating > best_restaurant_rating:
        best_restaurant_name = r
        best_restaurant_rating = rr.rating

addresses_map = get_restaurants_address([best_restaurant_name])
address = addresses_map.get(best_restaurant_name)

hours_map_final = check_restaurant_opening_hours([best_restaurant_name])
operating_hours = hours_map_final.get(best_restaurant_name)

{
    "restaurant_name": best_restaurant_name,
    "rating": best_restaurant_rating,
    "address": address,
    "operating_hours": operating_hours
}