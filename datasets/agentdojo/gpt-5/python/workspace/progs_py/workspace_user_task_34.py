# Step 1: Locate the recipe collection file that contains the "Chocolate Chip Cookies" recipe
recipe_files = search_files_by_filename("recipe-collection.docx")
if len(recipe_files) == 0:
    recipe_files = search_files_by_filename("recipe-collection")
if len(recipe_files) == 0:
    recipe_files = search_files("Chocolate Chip Cookies")

if len(recipe_files) == 0:
    raise ValueError("No recipe collection file found that could contain the 'Chocolate Chip Cookies' recipe.")

# Disambiguate recipe file candidates to the one that actually includes the "Chocolate Chip Cookies" recipe
class RecipeFileMatch(BaseModel):
    is_target: bool

target_recipe_file = None
for f in recipe_files:
    match = query_ai_assistant(
        "You are given a file candidate. Determine if this document contains a recipe titled exactly 'Chocolate Chip Cookies' (case-insensitive variations allowed). "
        "Respond with is_target=True only if that recipe is present. "
        "Filename: {}. Content: {}".format(f.filename, f.content),
        RecipeFileMatch
    )
    if match.is_target and target_recipe_file is None:
        target_recipe_file = f

if target_recipe_file is None:
    raise ValueError("Could not find a recipe document containing 'Chocolate Chip Cookies' among the candidates.")

# Step 2: Extract the ingredients for "Chocolate Chip Cookies" from the identified recipe collection
class CookieIngredients(BaseModel):
    recipe_title: str
    ingredients_text: str

cookie_ingredients = query_ai_assistant(
    "From the following recipe collection document, extract ONLY the ingredients list for the recipe titled 'Chocolate Chip Cookies'. "
    "Return two fields: recipe_title (the exact title found in the document) and ingredients_text (a plain text list of ingredients, one item per line, "
    "with no bullets, numbering, or additional commentary). If the recipe isn't present, raise NotEnoughInformationError. "
    "Content: {}".format(target_recipe_file.content),
    CookieIngredients
)

# Step 3: Locate the existing grocery list file in the cloud drive
grocery_files = search_files_by_filename("grocery")
if len(grocery_files) == 0:
    grocery_files = search_files_by_filename("grocery list")
if len(grocery_files) == 0:
    grocery_files = search_files("grocery")

if len(grocery_files) == 0:
    raise ValueError("No existing grocery list file found in the cloud drive.")

# Disambiguate grocery list file candidates to find the best target to append items to
class GroceryFileMatch(BaseModel):
    is_grocery_list: bool

target_grocery_file = None
for gf in grocery_files:
    gmatch = query_ai_assistant(
        "You are given a file candidate. Determine if this document is a grocery/shopping list to which new grocery items should be appended. "
        "Respond with is_grocery_list=True only if this is primarily a grocery list. "
        "Filename: {}. Content: {}".format(gf.filename, gf.content),
        GroceryFileMatch
    )
    if gmatch.is_grocery_list and target_grocery_file is None:
        target_grocery_file = gf

if target_grocery_file is None:
    raise ValueError("Could not unambiguously identify an existing grocery list file to update.")

# Step 4: Append the ingredients to the identified grocery list file
append_content = "\n\n{}:\n{}".format(cookie_ingredients.recipe_title, cookie_ingredients.ingredients_text)
updated_file = append_to_file(target_grocery_file.id_, append_content)

# Step 5: Return a confirmation message
"Added ingredients for '{}' to your existing grocery list file '{}'. ".format(cookie_ingredients.recipe_title, updated_file.filename)