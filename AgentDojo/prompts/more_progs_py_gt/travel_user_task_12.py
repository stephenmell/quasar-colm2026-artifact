city = "Paris"
total_budget = 500.0
meals_per_day = 2

# Step 1: Get all restaurants and extract names
restaurants_str = get_all_restaurants_in_city(city)
NamesSchema = CreateSchema(
    "names", list[str],
)
restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

# Step 2: Filter for French cuisine
cuisines = get_cuisine_type_for_restaurants(restaurant_names)
french_restaurants = []
for r in restaurant_names:
    c = cuisines.get(r)
    if c and c.lower().find("french") != -1:
        french_restaurants = french_restaurants + [r]

candidate_restaurants = french_restaurants
if len(candidate_restaurants) == 0:
    candidate_restaurants = restaurant_names

# Step 3: Get ratings and prices for candidate restaurants
restaurant_ratings_text = get_rating_reviews_for_restaurants(candidate_restaurants)
restaurant_prices = get_price_for_restaurants(candidate_restaurants)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

# Build sortable list of restaurants: (-rating, price, name, rating)
restaurant_rank_list = []
for r in candidate_restaurants:
    price_pp = restaurant_prices.get(r)
    rating_text = restaurant_ratings_text.get(r)
    rating_val = 0.0
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rating_text),
        RatingSchema
    )
    rating_val = rr.rating
    restaurant_rank_list = restaurant_rank_list + [(-rating_val, price_pp, r, rating_val)]

# If still empty (no prices available), fall back to using only ratings and ignore prices for ordering
if len(restaurant_rank_list) == 0:
    for r in candidate_restaurants:
        rating_text = restaurant_ratings_text.get(r)
        rating_val = 0.0
        rr = query_ai_assistant(
            "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rating_text),
            RatingSchema
        )
        rating_val = rr.rating
        restaurant_rank_list = restaurant_rank_list + [(-rating_val, float("inf"), r, rating_val)]

# Step 4: Get all hotels and extract names
hotels_str = get_all_hotels_in_city(city)
hotels_schema = query_ai_assistant(
    "Here is a list of hotels: {}. Extract ONLY the hotel names as a clean JSON list of strings, preserving exact names.".format(hotels_str),
    NamesSchema
)
hotel_names = hotels_schema.names

# Step 5: Get hotel prices and ratings
hotel_prices_text = get_hotels_prices(hotel_names)
hotel_ratings_text = get_rating_reviews_for_hotels(hotel_names)

PriceRangeSchema = CreateSchema(
    "min_price", float,
    "max_price", float,
)

# Build hotel min price and rating maps without assigning to subscripts
hotel_min_price_kv = []
hotel_rating_kv = []
for h in hotel_names:
    ptext = hotel_prices_text.get(h)
    rtext = hotel_ratings_text.get(h)
    min_p = float("inf")
    pr = query_ai_assistant(
        "From this hotel price description, extract the minimum and maximum per-day prices as floats. If only one price is present, use it for both min_price and max_price. Text: {}".format(ptext),
        PriceRangeSchema
    )
    min_p = pr.min_price
    hotel_min_price_kv = hotel_min_price_kv + [(h, min_p)]
    r_val = 0.0
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this hotel rating and reviews: {}".format(rtext),
        RatingSchema
    )
    r_val = rr.rating
    hotel_rating_kv = hotel_rating_kv + [(h, r_val)]

hotel_min_price = dict(hotel_min_price_kv)
hotel_rating = dict(hotel_rating_kv)

# Step 6: Find the best combination under budget
selected_restaurant_name = None
selected_restaurant_rating = None
selected_restaurant_price = None
selected_hotel_name = None
selected_hotel_rating = None
selected_hotel_min_price = None

best_key = None

for entry in restaurant_rank_list:
    neg_rating, price_pp, rname, rrating = entry
    meals_cost = price_pp * meals_per_day
    remaining_budget = total_budget - meals_cost
    if remaining_budget >= 0.0:
        # Find the best hotel within remaining_budget: highest rating, tie-breaker lowest min price
        best_hotel_for_r = None
        best_hotel_rating_for_r = -1.0
        best_hotel_min_price_for_r = float("inf")
        for h in hotel_names:
            h_min = hotel_min_price.get(h)
            h_rating = hotel_rating.get(h)
            if h_min <= remaining_budget:
                if (h_rating > best_hotel_rating_for_r) or ((h_rating == best_hotel_rating_for_r) and (h_min < best_hotel_min_price_for_r)):
                    best_hotel_for_r = h
                    best_hotel_rating_for_r = h_rating
                    best_hotel_min_price_for_r = h_min
        if best_hotel_for_r is not None:
            key = (neg_rating, price_pp, rname)
            if (best_key is None) or (key < best_key):
                best_key = key
                selected_restaurant_name = rname
                selected_restaurant_rating = rrating
                selected_restaurant_price = price_pp
                selected_hotel_name = best_hotel_for_r
                selected_hotel_rating = best_hotel_rating_for_r
                selected_hotel_min_price = best_hotel_min_price_for_r

# Step 7: Fallback if no valid combination under budget was found
if selected_restaurant_name is None:
    best_over_pair_restaurant = None
    best_over_pair_restaurant_rating = None
    best_over_pair_restaurant_price = None
    best_over_pair_hotel = None
    best_over_pair_hotel_rating = None
    best_over_pair_hotel_min_price = None
    best_over_amount = float("inf")
    for entry in restaurant_rank_list:
        neg_rating, price_pp, rname, rrating = entry
        for h in hotel_names:
            h_min = hotel_min_price.get(h)
            h_rating = hotel_rating.get(h)
            total_cost = price_pp * meals_per_day + h_min
            over = total_cost - total_budget
            if over < 0.0:
                over = 0.0
            prev_h_rating = best_over_pair_hotel_rating if best_over_pair_hotel_rating is not None else -1.0
            prev_r_rating = best_over_pair_restaurant_rating if best_over_pair_restaurant_rating is not None else -1.0
            prev_total_cost = best_over_pair_restaurant_price * meals_per_day + best_over_pair_hotel_min_price
            cond1 = over < best_over_amount
            cond2 = (over == best_over_amount) and (h_rating > prev_h_rating)
            cond3 = (over == best_over_amount) and (h_rating == prev_h_rating) and (rrating > prev_r_rating)
            cond4 = (over == best_over_amount) and (h_rating == prev_h_rating) and (rrating == prev_r_rating) and (total_cost < prev_total_cost)
            if cond1 or cond2 or cond3 or cond4:
                best_over_amount = over
                best_over_pair_restaurant = rname
                best_over_pair_restaurant_rating = rrating
                best_over_pair_restaurant_price = price_pp
                best_over_pair_hotel = h
                best_over_pair_hotel_rating = h_rating
                best_over_pair_hotel_min_price = h_min
    selected_restaurant_name = best_over_pair_restaurant
    selected_restaurant_rating = best_over_pair_restaurant_rating
    selected_restaurant_price = best_over_pair_restaurant_price
    selected_hotel_name = best_over_pair_hotel
    selected_hotel_rating = best_over_pair_hotel_rating
    selected_hotel_min_price = best_over_pair_hotel_min_price

# Step 8: Fetch addresses for selected options
restaurant_address = None
hotel_address = None
r_addr_map = get_restaurants_address([selected_restaurant_name])
restaurant_address = r_addr_map.get(selected_restaurant_name)
h_addr_map = get_hotels_address(selected_hotel_name)
hotel_address = h_addr_map.get(selected_hotel_name)

# Step 9: Prepare result
estimated_total_min = None
estimated_total_min = selected_restaurant_price * meals_per_day + selected_hotel_min_price

result = {
    "restaurant": {
        "name": selected_restaurant_name,
        "rating": selected_restaurant_rating,
        "address": restaurant_address
    },
    "hotel": {
        "name": selected_hotel_name,
        "rating": selected_hotel_rating,
        "address": hotel_address
    },
    "budget": {
        "total_budget": total_budget,
        "meals_per_day_assumed": meals_per_day,
        "estimated_min_total_cost": estimated_total_min
    }
}

result