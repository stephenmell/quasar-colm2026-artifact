city = "Paris"
total_budget = 500.0

# Step 1: Restaurants in Paris
restaurants_str = get_all_restaurants_in_city(city)

class NamesSchema(BaseModel):
    names: list[str]

restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names. If the input is empty, return an empty list.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

if len(restaurant_names) == 0:
    raise ValueError("No restaurants found in Paris.")

# Step 2: Restaurant details
cuisines = get_cuisine_type_for_restaurants(restaurant_names)
opening_hours = check_restaurant_opening_hours(restaurant_names)
restaurant_ratings_text = get_rating_reviews_for_restaurants(restaurant_names)
restaurant_prices = get_price_for_restaurants(restaurant_names)
restaurant_addresses_dict = get_restaurants_address(restaurant_names)

class OpenMealsSchema(BaseModel):
    lunch_open: bool
    dinner_open: bool

class RatingSchema(BaseModel):
    rating: float
    reviews: list[str]

class AmazingSchema(BaseModel):
    amazing: bool

restaurants_data = []
for r in restaurant_names:
    hours_text = opening_hours.get(r)
    open_schema = query_ai_assistant(
        "Given this restaurant opening hours description: {}. Determine if the restaurant is OPEN for lunch (typically between 12:00-15:00) and for dinner (typically between 17:30-22:30) on a typical day. If hours indicate 'daily' or show continuous hours covering those periods, mark the corresponding meal as open. If hours specify different days, consider whether lunch and dinner services are generally available on most days. Return booleans lunch_open and dinner_open accordingly.".format(hours_text),
        OpenMealsSchema
    )
    rating_text = restaurant_ratings_text.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews text: {}.".format(rating_text),
        RatingSchema
    )
    amazing_schema = query_ai_assistant(
        "Assess these restaurant reviews and the overall rating to determine if the place has 'amazing reviews'. Consider it amazing if the reviews are overwhelmingly positive (strong praise, superlatives) and the rating is high. Reviews: {}. Rating: {}. Respond with a single boolean field.".format(rr.reviews, rr.rating),
        AmazingSchema
    )
    cuisine_string = cuisines.get(r)
    is_french = (cuisine_string.lower().find("french") != -1) if (type(cuisine_string) == "str") else False
    price_pp = restaurant_prices.get(r)
    address_r = restaurant_addresses_dict.get(r)
    restaurants_data = restaurants_data + [{
        "name": r,
        "rating": rr.rating,
        "reviews": rr.reviews,
        "amazing": amazing_schema.amazing,
        "price": price_pp,
        "lunch_open": open_schema.lunch_open,
        "dinner_open": open_schema.dinner_open,
        "french": is_french,
        "address": address_r
    }]

# Step 3: Hotels in Paris
hotels_str = get_all_hotels_in_city(city)

hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names. If the input is empty, return an empty list.".format(hotels_str),
    NamesSchema
)
hotel_names = hotels_schema.names

if len(hotel_names) == 0:
    raise ValueError("No hotels found in Paris.")

hotel_prices_text = get_hotels_prices(hotel_names)
hotel_ratings_text = get_rating_reviews_for_hotels(hotel_names)

class PriceRangeSchema(BaseModel):
    min_price: float
    max_price: float

hotels_data = []
for h in hotel_names:
    price_text = hotel_prices_text.get(h)
    pr = query_ai_assistant(
        "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(price_text),
        PriceRangeSchema
    )
    rating_text = hotel_ratings_text.get(h)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews text: {}.".format(rating_text),
        RatingSchema
    )
    hotels_data = hotels_data + [{
        "name": h,
        "min_price": pr.min_price,
        "max_price": pr.max_price,
        "rating": rr.rating
    }]

# Step 4: Build candidate pairs under budget with staged restaurant filtering
stages = [
    [r for r in restaurants_data if r["french"] and r["lunch_open"] and r["dinner_open"]],
    [r for r in restaurants_data if r["french"]],
    [r for r in restaurants_data if r["lunch_open"] and r["dinner_open"]],
    restaurants_data
]

candidate_pairs = []
for stage_idx in range(len(stages)):
    stage_restaurants = stages[stage_idx]
    pairs_stage = []
    for r in stage_restaurants:
        remaining = total_budget - 2.0 * r["price"]
        affordable_hotels = [h for h in hotels_data if h["min_price"] <= remaining]
        if len(affordable_hotels) > 0:
            # Pick best affordable hotel: highest rating, tie-breaker lowest min_price
            best_h_name = None
            best_h_rating = -1.0
            best_h_min_price = float("inf")
            for h in affordable_hotels:
                better = (h["rating"] > best_h_rating) or ((h["rating"] == best_h_rating) and (h["min_price"] < best_h_min_price))
                if better:
                    best_h_name = h["name"]
                    best_h_rating = h["rating"]
                    best_h_min_price = h["min_price"]
            pairs_stage = pairs_stage + [{
                "restaurant": r,
                "hotel": {
                    "name": best_h_name,
                    "rating": best_h_rating,
                    "min_price": best_h_min_price
                }
            }]
    if len(pairs_stage) > 0:
        candidate_pairs = pairs_stage
        # Stop at the first stage that yields results (without using break by just overwriting and clearing subsequent stages)
        stages = [stage_restaurants]  # no-op; just to avoid further processing meaningfully
        # We won't actually loop further since for-loop already evaluated range, but we won't use other pairs.

# Step 5: Select the best pair according to criteria
# Criteria: highest restaurant rating; prefer amazing reviews True; tie-breaker lower restaurant price; then higher hotel rating; then lower hotel min_price
best_pair = None
best_r_rating = -1.0
best_amazing = False
best_r_price = float("inf")
best_h_rating = -1.0
best_h_min_price = float("inf")

for pair in candidate_pairs:
    r = pair["restaurant"]
    h = pair["hotel"]
    better = False
    if (r["rating"] > best_r_rating):
        better = True
    elif (r["rating"] == best_r_rating):
        if (r["amazing"] and (not best_amazing)):
            better = True
        elif (r["amazing"] == best_amazing):
            if (r["price"] < best_r_price):
                better = True
            elif (r["price"] == best_r_price):
                if (h["rating"] > best_h_rating):
                    better = True
                elif (h["rating"] == best_h_rating):
                    if (h["min_price"] < best_h_min_price):
                        better = True
    if better:
        best_pair = pair
        best_r_rating = r["rating"]
        best_amazing = r["amazing"]
        best_r_price = r["price"]
        best_h_rating = h["rating"]
        best_h_min_price = h["min_price"]

if best_pair is None:
    raise ValueError("No combination of restaurant and hotel in Paris fits the 500.0 budget with two meals.")

# Step 6: Resolve addresses for the selected hotel (restaurant address is already available)
selected_restaurant = best_pair["restaurant"]
selected_hotel_name = best_pair["hotel"]["name"]

hotel_address_info = get_hotels_address(selected_hotel_name)

class AddressSchema(BaseModel):
    address: str

hotel_address_schema = query_ai_assistant(
    "From this hotel address information object: {}. Extract the full human-readable street address as a single-line string in the 'address' field.".format(hotel_address_info),
    AddressSchema
)
hotel_address = hotel_address_schema.address

result = {
    "restaurant": {
        "name": selected_restaurant["name"],
        "rating": selected_restaurant["rating"],
        "address": selected_restaurant["address"]
    },
    "hotel": {
        "name": selected_hotel_name,
        "rating": best_pair["hotel"]["rating"],
        "address": hotel_address
    }
}

result