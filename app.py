from flask import Flask, request, jsonify, render_template
import requests
import json
import os
from recipe_scrapers import AllRecipes  # Ensure your scraper is correctly imported

app = Flask(__name__)

# Function to scrape AllRecipes website
def scrape_allrecipes(url):
    try:
        # Fetch the webpage
        response = requests.get(url)
        if response.status_code != 200:
            return {"error": "Failed to retrieve the webpage"}

        # Use the AllRecipes scraper to scrape recipe details
        scraper = AllRecipes(response.text, url)

        # Extract recipe information
        recipe_data = {
            'title': scraper.title(),
            'ingredients': scraper.ingredients(),
            'instructions': format_instructions(scraper.instructions()),
            'total_time': scraper.total_time(),
            'yields': scraper.yields(),
            'image': scraper.image(),
        }

        # Save the recipe data to a JSON file
        save_recipe_to_file(recipe_data)

        return recipe_data

    except Exception as e:
        return {"error": str(e)}

def format_instructions(instructions):
    # Split instructions by period and strip whitespace
    steps = instructions.split('.')
    return [step.strip() for step in steps if step.strip()]

def save_recipe_to_file(recipe_data):
    # Create a directory for recipes if it doesn't exist
    if not os.path.exists('recipes'):
        os.makedirs('recipes')

    # Create a unique filename using the recipe title
    filename = f"recipes/{recipe_data['title'].replace(' ', '_')}.json"

    # Write the recipe data to the JSON file
    with open(filename, 'w') as json_file:
        json.dump(recipe_data, json_file, indent=4)

    print(f"Recipe saved to {filename}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_recipe_form', methods=['GET'])
def submit_recipe_form():
    return render_template('submit_recipe.html')

@app.route('/scrape', methods=['POST'])
def scrape_recipe():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        recipe_data = scrape_allrecipes(url)
        return jsonify(recipe_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recipes', methods=['GET'])
def list_recipes():
    recipes = []
    # Search for recipes in the recipes directory
    for filename in os.listdir('recipes'):
        if filename.endswith('.json'):
            with open(os.path.join('recipes', filename), 'r') as json_file:
                recipe_data = json.load(json_file)
                recipes.append(recipe_data)

    return jsonify(recipes)  # Return the list of recipes in JSON format

@app.route('/submit_recipe', methods=['POST'])
def submit_recipe():
    try:
        data = request.json
        
        # Ensure the required fields are present
        required_fields = ['title', 'ingredients', 'instructions', 'total_time', 'yields']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"{field} is required."}), 400
        
        # Build the recipe dictionary
        recipe_data = {
            'title': data['title'],
            'ingredients': data['ingredients'],
            'instructions': data['instructions'],
            'total_time': int(data['total_time']),
            'yields': data['yields'],
            'image': data['image'] if 'image' in data else None
        }

        # Save the recipe as a JSON file
        save_recipe_to_file(recipe_data)

        return jsonify({"message": "Recipe saved successfully!"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to delete a recipe by title
@app.route('/delete_recipe/<string:title>', methods=['POST'])
def delete_recipe(title):
    try:
        filename = f"recipes/{title.replace(' ', '_')}.json"
        if os.path.exists(filename):
            os.remove(filename)
            return jsonify({"message": "Recipe deleted successfully!"}), 200
        else:
            return jsonify({"error": "Recipe not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
