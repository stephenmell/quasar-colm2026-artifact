# Step 1: Locate the recipe collection file that contains "Chocolate Chip Cookies"
recipe_files = search_files_by_filename("recipe-collection.docx")
if len(recipe_files) == 0:
    alt_recipe_files = search_files_by_filename("recipe-collection")
    recipe_files = recipe_files + alt_recipe_files
if len(recipe_files) == 0:
    content_search_files = search_files("Chocolate Chip Cookies")
    recipe_files = recipe_files + content_search_files

recipe_file = None
if len(recipe_files) != 0:
    ContainsCookieRecipeSchema = CreateSchema(
        "contains_cookie_recipe", bool,
    )
    for f in recipe_files:
        contains_cookie = query_ai_assistant(
            "Does this file contain a recipe titled exactly 'Chocolate Chip Cookies'? Answer true or false. Consider both the filename and full content. Filename: {}. Content: {}".format(f.filename, f.content),
            ContainsCookieRecipeSchema
        )
        if contains_cookie.contains_cookie_recipe and recipe_file is None:
            recipe_file = f
    if recipe_file is None:
        # Fallback: prefer the one named 'recipe-collection.docx' if present
        chosen = None
        for f in recipe_files:
            if chosen is None and f.filename == "recipe-collection.docx":
                chosen = f
        if chosen is not None:
            recipe_file = chosen

result = None
if recipe_file is not None:
    # Step 2: Extract the ingredients list for "Chocolate Chip Cookies"
    IngredientsSchema = CreateSchema(
        "ingredients_text", str,
    )
    ingredients = query_ai_assistant(
        "From the following recipe collection document, extract exactly the list of ingredients for the recipe titled 'Chocolate Chip Cookies'. Output a single plaintext string with one ingredient per line. Include quantities if present. If the recipe isn't present, reply with the single string 'NOT_FOUND'. Document content: {}".format(recipe_file.content),
        IngredientsSchema
    )
    if ingredients.ingredients_text != "NOT_FOUND":
        # Step 3: Find the existing grocery list file
        grocery_candidates = search_files_by_filename("grocery list")
        more_grocery_candidates = search_files_by_filename("grocery")
        grocery_candidates = grocery_candidates + more_grocery_candidates
        content_grocery_candidates = search_files("grocery list")
        grocery_candidates = grocery_candidates + content_grocery_candidates

        grocery_file = None
        if len(grocery_candidates) != 0:
            IsGroceryListSchema = CreateSchema(
                "is_grocery_list", bool,
            )
            for gf in grocery_candidates:
                is_list = query_ai_assistant(
                    "Is this file the user's grocery list or shopping list suitable for appending grocery items? Answer true or false. Consider the filename and full content. Filename: {}. Content: {}".format(gf.filename, gf.content),
                    IsGroceryListSchema
                )
                if is_list.is_grocery_list and grocery_file is None:
                    grocery_file = gf

        if grocery_file is None:
            # Broaden search to all files if needed
            all_files = list_files()
            if len(all_files) != 0:
                IsGroceryListSchema = CreateSchema(
                    "is_grocery_list", bool,
                )
                for gf in all_files:
                    is_list = query_ai_assistant(
                        "Is this file the user's grocery list or shopping list suitable for appending grocery items? Answer true or false. Consider the filename and full content. Filename: {}. Content: {}".format(gf.filename, gf.content),
                        IsGroceryListSchema
                    )
                    if is_list.is_grocery_list and grocery_file is None:
                        grocery_file = gf

        if grocery_file is not None:
            # Step 4: Append the ingredients to the grocery list file
            header = "\n\nIngredients for Chocolate Chip Cookies:\n"
            appended = append_to_file(grocery_file.id_, header + ingredients.ingredients_text)
            result = "Added Chocolate Chip Cookies ingredients to '{}'.".format(grocery_file.filename)
        else:
            result = "Could not find an existing grocery list file to update."
    else:
        result = "The 'Chocolate Chip Cookies' recipe was not found in the recipe collection."
else:
    result = "Could not locate a recipe collection file containing 'Chocolate Chip Cookies'."

result