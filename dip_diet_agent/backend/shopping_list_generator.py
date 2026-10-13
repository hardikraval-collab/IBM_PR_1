"""
Shopping list generator for DIP Diet Agent.
Derives a categorized shopping list from meal plan ingredients.
"""
from typing import List, Dict
from backend.models import ShoppingListResponse, ShoppingItem
from backend.meal_plan_generator import generate_structured_meal_plan


# Category mapping for common ingredients
INGREDIENT_CATEGORIES = {
    # Vegetables
    "spinach": "Vegetables", "tomato": "Vegetables", "onion": "Vegetables",
    "carrot": "Vegetables", "broccoli": "Vegetables", "bell pepper": "Vegetables",
    "mushroom": "Vegetables", "cucumber": "Vegetables", "celery": "Vegetables",
    "mixed vegetables": "Vegetables", "seasonal vegetable": "Vegetables",
    "peas": "Vegetables", "corn": "Vegetables", "garlic": "Vegetables",
    "ginger": "Vegetables", "green chilli": "Vegetables", "kale": "Vegetables",

    # Fruits
    "banana": "Fruits", "apple": "Fruits", "berries": "Fruits",
    "mango": "Fruits", "watermelon": "Fruits", "papaya": "Fruits",
    "pomegranate": "Fruits", "kiwi": "Fruits", "avocado": "Fruits",
    "mixed berries": "Fruits", "cherry tomatoes": "Fruits",
    "lemon": "Fruits",

    # Grains & Cereals
    "brown rice": "Grains & Cereals", "rice": "Grains & Cereals",
    "quinoa": "Grains & Cereals", "oats": "Grains & Cereals",
    "whole wheat bread": "Grains & Cereals", "whole wheat roti": "Grains & Cereals",
    "roti": "Grains & Cereals", "idli batter": "Grains & Cereals",
    "beaten rice": "Grains & Cereals", "rice cake": "Grains & Cereals",
    "granola": "Grains & Cereals", "rolled oats": "Grains & Cereals",

    # Legumes & Pulses
    "toor dal": "Legumes & Pulses", "moong dal": "Legumes & Pulses",
    "dal": "Legumes & Pulses", "mixed dal": "Legumes & Pulses",
    "chickpeas": "Legumes & Pulses", "chole": "Legumes & Pulses",
    "kidney beans": "Legumes & Pulses", "rajma": "Legumes & Pulses",
    "black beans": "Legumes & Pulses", "red lentils": "Legumes & Pulses",
    "lentils": "Legumes & Pulses", "roasted chickpeas": "Legumes & Pulses",
    "roasted chana": "Legumes & Pulses",

    # Proteins (Non-Veg)
    "chicken breast": "Proteins (Non-Veg)", "fish fillet": "Proteins (Non-Veg)",
    "eggs": "Proteins (Non-Veg)", "salmon": "Proteins (Non-Veg)",

    # Proteins (Plant-Based)
    "tofu": "Plant Proteins", "firm tofu": "Plant Proteins",
    "paneer": "Plant Proteins", "tempeh": "Plant Proteins",
    "edamame": "Plant Proteins",

    # Dairy & Alternatives
    "greek yoghurt": "Dairy & Alternatives", "milk": "Dairy & Alternatives",
    "almond milk": "Dairy & Alternatives", "oat milk": "Dairy & Alternatives",
    "cheese": "Dairy & Alternatives", "curd": "Dairy & Alternatives",
    "raita": "Dairy & Alternatives", "coconut milk": "Dairy & Alternatives",

    # Nuts & Seeds
    "almonds": "Nuts & Seeds", "walnuts": "Nuts & Seeds",
    "pumpkin seeds": "Nuts & Seeds", "sunflower seeds": "Nuts & Seeds",
    "chia seeds": "Nuts & Seeds", "peanuts": "Nuts & Seeds",
    "mixed nuts": "Nuts & Seeds", "hemp seeds": "Nuts & Seeds",
    "coconut flakes": "Nuts & Seeds", "almond butter": "Nuts & Seeds",
    "peanut butter": "Nuts & Seeds",

    # Oils & Fats
    "olive oil": "Oils & Fats", "ghee": "Oils & Fats",
    "sesame oil": "Oils & Fats", "oil": "Oils & Fats",
    "coconut oil": "Oils & Fats",

    # Herbs & Spices
    "turmeric": "Herbs & Spices", "cumin": "Herbs & Spices",
    "mustard seeds": "Herbs & Spices", "curry leaves": "Herbs & Spices",
    "garam masala": "Herbs & Spices", "coriander": "Herbs & Spices",
    "thyme": "Herbs & Spices", "parsley": "Herbs & Spices",
    "chaat masala": "Herbs & Spices", "sambar powder": "Herbs & Spices",
    "spices": "Herbs & Spices", "red chilli": "Herbs & Spices",
    "black pepper": "Herbs & Spices", "tamarind": "Herbs & Spices",

    # Condiments & Others
    "hummus": "Condiments", "soy sauce": "Condiments",
    "nutritional yeast": "Condiments", "honey": "Condiments",
    "tahini": "Condiments",
}

QUANTITY_MAP = {
    "vegetables": "500g",
    "fruits": "250g",
    "grains & cereals": "500g",
    "legumes & pulses": "250g",
    "proteins (non-veg)": "300g",
    "plant proteins": "300g",
    "dairy & alternatives": "500ml / 250g",
    "nuts & seeds": "200g",
    "oils & fats": "250ml",
    "herbs & spices": "50g",
    "condiments": "1 jar / pack",
}

SHOPPING_TIPS = [
    "🛒 Buy seasonal and locally sourced vegetables for maximum freshness and nutrients.",
    "📦 Stock up on dry pantry items (lentils, oats, nuts) in bulk to save money.",
    "🥦 Choose a variety of coloured vegetables for a broad range of micronutrients.",
    "🏷️ Read ingredient labels — avoid products with added sugars, trans fats, or excess sodium.",
    "❄️ Wash and prep vegetables in advance for convenient healthy meals throughout the week.",
    "🌿 Fresh herbs can be grown at home — basil, coriander, and mint are easy to maintain.",
    "💧 Ensure you stock sufficient hydration: herbal teas, coconut water, or plain water.",
]


def generate_shopping_list(user_profile: dict) -> ShoppingListResponse:
    """
    Generate a shopping list from the user's weekly meal plan.
    """
    # Generate a weekly meal plan
    meal_plan = generate_structured_meal_plan(user_profile, plan_type="weekly")

    # Collect all ingredients
    ingredient_freq: Dict[str, int] = {}
    for day in meal_plan.days:
        for meal in day.meals:
            for ingredient in meal.ingredients:
                key = ingredient.lower().strip()
                ingredient_freq[key] = ingredient_freq.get(key, 0) + 1

    # Build categorized shopping list
    items: List[ShoppingItem] = []
    seen: set = set()

    for ingredient, count in sorted(ingredient_freq.items(), key=lambda x: x[0]):
        if ingredient in seen:
            continue
        seen.add(ingredient)

        # Find category
        category = "Other"
        for key, cat in INGREDIENT_CATEGORIES.items():
            if key in ingredient or ingredient in key:
                category = cat
                break

        # Determine quantity
        qty_key = category.lower()
        quantity = QUANTITY_MAP.get(qty_key, "as needed")
        if count > 3:
            quantity = f"2x {quantity}"

        items.append(ShoppingItem(
            item=ingredient.title(),
            quantity=quantity,
            category=category,
        ))

    # Sort by category
    items.sort(key=lambda x: (x.category, x.item))

    # Apply allergy filter — exclude any item whose name overlaps with an allergen
    allergies = [a.lower() for a in (user_profile.get("food_allergies") or [])]
    if allergies:
        def _contains_allergen(item_name: str) -> bool:
            name_lower = item_name.lower()
            for allergen in allergies:
                # Check full allergen string
                if allergen in name_lower or name_lower in allergen:
                    return True
                # Check individual words of the allergen (handles "peanuts" matching "peanut butter")
                for word in allergen.replace("-", " ").split():
                    stem = word.rstrip("s")  # crude stemming: "peanuts" → "peanut"
                    if stem and (stem in name_lower or word in name_lower):
                        return True
            return False
        items = [item for item in items if not _contains_allergen(item.item)]

    return ShoppingListResponse(
        user_name=user_profile.get("name", "User"),
        items=items,
        total_items=len(items),
        tips=SHOPPING_TIPS,
    )
