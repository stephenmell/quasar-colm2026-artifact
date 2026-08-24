# Step 1: Locate the recipe collection file that contains the Chocolate Chip Cookies recipe
recipe_files = search_files_by_filename("recipe-collection.docx")

if len(recipe_files) == 0:
    recipe_files = search_files("Chocolate Chip Cookies")

if len(recipe_files) == 0:
    recipe_files = search_files("recipe-collection")

recipe_file = None
if len(recipe_files) != 0:
    RecipePresenceSchema = CreateSchema(
        "has_chocolate_chip_cookies", bool,
    )
    for f in recipe_files:
        presence = query_ai_assistant(
            "Determine if this document contains a recipe for Chocolate Chip Cookies. Consider minor title variations like 'Chocolate Chip Cookie' or pluralization. Respond with True only if the recipe is clearly present. Filename: {}. Content: {}".format(f.filename, f.content),
            RecipePresenceSchema
        )
        if presence.has_chocolate_chip_cookies and recipe_file is None:
            recipe_file = f

result = "I couldn't find the 'Chocolate Chip Cookies' recipe in your files, so I wasn't able to add its ingredients to your grocery list."
ingredients_text = ""
if recipe_file is not None:
    # Step 2: Extract the ingredients list for the Chocolate Chip Cookies recipe
    IngredientsSchema = CreateSchema(
        "ingredients", str,
    )
    ingredients = query_ai_assistant(
        "From the following document, extract the complete list of ingredients for the Chocolate Chip Cookies recipe only. Return a clean list, one item per line, including quantities and units if available. Do not include instructions or other recipes. Content: {}".format(recipe_file.content),
        IngredientsSchema
    )
    ingredients_text = ingredients.ingredients

    # Step 3: Locate the existing grocery list file
    grocery_candidates = search_files_by_filename("grocery list")
    if len(grocery_candidates) == 0:
        grocery_candidates = search_files_by_filename("groceries")
    if len(grocery_candidates) == 0:
        grocery_candidates = search_files("grocery")

    grocery_file = None
    if len(grocery_candidates) != 0:
        GroceryDisambiguationSchema = CreateSchema(
            "is_grocery_list", bool,
        )
        for gf in grocery_candidates:
            is_gl = query_ai_assistant(
                "Decide if this file is a grocery/shopping list intended to store items to buy. Consider filename and content. Respond True only if it is clearly a grocery list. Filename: {}. Content: {}".format(gf.filename, gf.content),
                GroceryDisambiguationSchema
            )
            if is_gl.is_grocery_list and grocery_file is None:
                grocery_file = gf

    # Step 4: Add ingredients to the grocery list (append to existing or create a new file if none found)
    day = get_current_day()
    addition_block = "Added on {}\nChocolate Chip Cookies — Ingredients:\n{}\n".format(day, ingredients_text)

    if grocery_file is not None:
        updated_file = append_to_file(grocery_file.id_, addition_block)
        result = "I've added the Chocolate Chip Cookies ingredients to your existing grocery list file '{}' on {}.\nItems added:\n{}".format(updated_file.filename, day, ingredients_text)
    else:
        new_file = create_file("Grocery List.txt", "Grocery List\n\n{}".format(addition_block))
        result = "I couldn't locate an existing grocery list, so I created a new one named '{}' and added the Chocolate Chip Cookies ingredients on {}.\nItems added:\n{}".format(new_file.filename, day, ingredients_text)

result