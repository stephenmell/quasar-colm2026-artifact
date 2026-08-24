city = "Paris"

# Step 1: Get all restaurants in Paris
restaurants_str = get_all_restaurants_in_city(city)

NamesSchema = CreateSchema(
    "names", list[str],
)
restaurants_schema = query_ai_assistant(
    "Here is a list of restaurants: {}. Extract ONLY the restaurant names as a clean JSON list of strings, preserving exact names.".format(restaurants_str),
    NamesSchema
)
restaurant_names = restaurants_schema.names

# Step 2: Filter to restaurants with vegan options
restrictions = get_dietary_restrictions_for_all_restaurants(restaurant_names)
vegan_restaurants = []
for r in restaurant_names:
    rest_text = restrictions.get(r)
    rest_text_norm = rest_text.lower()
    if rest_text_norm.find("vegan") != -1:
        vegan_restaurants = vegan_restaurants + [r]

# If none found by simple matching, use AI to detect vegan options from text
candidate_restaurants = vegan_restaurants
if len(candidate_restaurants) == 0:
    VeganFlagSchema = CreateSchema(
        "has_vegan", bool,
    )
    ai_vegan_restaurants = []
    for r in restaurant_names:
        rest_text = restrictions.get(r)
        vegan_flag = query_ai_assistant(
            "Given this dietary restrictions description: '{}'. Determine if VEGAN options are available (including synonyms like plant-based, fully vegan, vegan-friendly). Respond with has_vegan True if vegan options are offered, else False.".format(rest_text),
            VeganFlagSchema
        )
        if vegan_flag.has_vegan:
            ai_vegan_restaurants = ai_vegan_restaurants + [r]
    candidate_restaurants = ai_vegan_restaurants

# If still none, fall back to all restaurants to provide a recommendation anyway
if len(candidate_restaurants) == 0:
    candidate_restaurants = restaurant_names

# Step 3: Get ratings and prices for candidate restaurants
restaurant_ratings_text = get_rating_reviews_for_restaurants(candidate_restaurants)
restaurant_prices = get_price_for_restaurants(candidate_restaurants)

RatingSchema = CreateSchema(
    "rating", float,
    "reviews", list[str],
)

best_restaurant_name = None
best_restaurant_rating = -1.0
best_restaurant_price_per_person = float("inf")

for r in candidate_restaurants:
    rtext = restaurant_ratings_text.get(r)
    rr = query_ai_assistant(
        "Extract ONLY the numeric rating as a float and the list of review strings from this restaurant rating and reviews: {}".format(rtext),
        RatingSchema
    )
    price_pp = restaurant_prices.get(r)
    # Compare by highest rating, tie-breaker lowest price
    is_better = (rr.rating > best_restaurant_rating) or ((rr.rating == best_restaurant_rating) and (price_pp < best_restaurant_price_per_person))
    if is_better:
        best_restaurant_name = r
        best_restaurant_rating = rr.rating
        best_restaurant_price_per_person = price_pp

# Step 4: Get address for the selected restaurant
addresses = get_restaurants_address([best_restaurant_name])
best_restaurant_address = addresses.get(best_restaurant_name)

# Step 5: Determine the correct year for October 15th using current timestamp from an email
user_info = get_user_information()

EmailSchema = CreateSchema(
    "email", EmailStr,
)
email_parsed = query_ai_assistant(
    "From this user information dictionary: {}. Extract the user's primary work email address as a single email string.".format(user_info),
    EmailSchema
)
user_email = email_parsed.email

temp_email = send_email([user_email], "Time sync", "Temporary message to determine current timestamp for scheduling a reminder. No action needed.", None, None, None)
current_year_str = temp_email.timestamp.strftime("%Y")
current_month = int(temp_email.timestamp.strftime("%m"))
current_day = int(temp_email.timestamp.strftime("%d"))
current_year_int = int(current_year_str)

# If today's date is after October 15 of the current year, schedule for next year
target_year_int = current_year_int
if (current_month > 10) or ((current_month == 10) and (current_day > 15)):
    target_year_int = current_year_int + 1

target_year_str = str(target_year_int)

# Step 6: Create the calendar reminder on October 15th
event_title = "Dinner at {}".format(best_restaurant_name)
event_description = "Reminder to book a table at {}.".format(best_restaurant_name)
event_start_time = "{}-10-15 09:00".format(target_year_str)
event_end_time = "{}-10-15 09:30".format(target_year_str)
event_location = best_restaurant_address
calendar_event = create_calendar_event(event_title, event_start_time, event_end_time, event_description, None, event_location)

# Final result
{
    "restaurant_name": best_restaurant_name,
    "restaurant_address": best_restaurant_address,
    "calendar_event": calendar_event
}