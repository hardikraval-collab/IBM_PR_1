"""
Structured meal plan generator for DIP Diet Agent.
Generates daily/weekly meal plans based on user profile with nutritional data.
"""
import logging
from typing import List, Dict, Any

from backend.models import MealPlanResponse, DayPlan, Meal
from backend.config import MEDICAL_DISCLAIMER

logger = logging.getLogger(__name__)

# ── TDEE & Macros ─────────────────────────────────────────────────────────────

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "super_active": 1.9,
}


def calculate_tdee(profile: dict) -> int:
    """
    Calculate Total Daily Energy Expenditure using Mifflin-St Jeor equation.
    Falls back to 2000 kcal if height/weight not provided.
    """
    weight = profile.get("weight_kg") or 70.0
    height = profile.get("height_cm") or 170.0
    age = profile.get("age") or 30
    gender = (profile.get("gender") or "female").lower()
    activity = profile.get("activity_level") or "moderately_active"

    # Mifflin-St Jeor BMR
    if gender in ("male", "m"):
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    multiplier = ACTIVITY_MULTIPLIERS.get(activity, 1.55)
    tdee = int(bmr * multiplier)
    return max(1200, min(tdee, 4500))  # Clamp to safe range


def get_macro_targets(profile: dict, tdee: int) -> Dict[str, Any]:
    """Calculate macro targets based on nutrition goals."""
    goals = profile.get("nutrition_goals") or ["maintenance"]
    goal = goals[0] if goals else "maintenance"

    if goal in ("weight_loss",):
        calories = tdee - 400
        protein_pct, carb_pct, fat_pct = 0.30, 0.40, 0.30
    elif goal in ("weight_gain", "muscle_gain"):
        calories = tdee + 300
        protein_pct, carb_pct, fat_pct = 0.30, 0.45, 0.25
    elif goal == "manage_diabetes":
        calories = tdee - 200
        protein_pct, carb_pct, fat_pct = 0.25, 0.35, 0.40
    elif goal == "heart_health":
        calories = tdee
        protein_pct, carb_pct, fat_pct = 0.20, 0.50, 0.30
    else:  # maintenance, energy_boost, gut_health
        calories = tdee
        protein_pct, carb_pct, fat_pct = 0.25, 0.45, 0.30

    protein_g = int(calories * protein_pct / 4)
    carbs_g = int(calories * carb_pct / 4)
    fat_g = int(calories * fat_pct / 9)

    return {
        "target_calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "primary_goal": goal,
    }


# ── Meal Templates ────────────────────────────────────────────────────────────

VEG_MEAL_TEMPLATES = {
    "Monday": [
        Meal(meal_type="breakfast", name="Oats Upma with Vegetables",
             ingredients=["rolled oats", "mixed vegetables", "mustard seeds", "curry leaves", "ghee"],
             calories_approx=320, protein_g=12, carbs_g=52, fat_g=8,
             preparation_notes="Dry roast oats. Sauté vegetables with mustard seeds. Mix and cook 5 min."),
        Meal(meal_type="lunch", name="Dal Palak + Brown Rice + Salad",
             ingredients=["toor dal", "spinach", "brown rice", "cucumber", "tomato", "lemon"],
             calories_approx=480, protein_g=22, carbs_g=78, fat_g=6,
             preparation_notes="Pressure cook dal. Add blanched spinach. Serve with brown rice and fresh salad."),
        Meal(meal_type="snack", name="Apple with Almond Butter",
             ingredients=["apple", "almond butter"],
             calories_approx=200, protein_g=4, carbs_g=28, fat_g=9,
             preparation_notes="Slice apple and serve with 1 tbsp almond butter."),
        Meal(meal_type="dinner", name="Vegetable Khichdi",
             ingredients=["moong dal", "rice", "mixed vegetables", "turmeric", "ghee"],
             calories_approx=380, protein_g=16, carbs_g=60, fat_g=8,
             preparation_notes="Cook dal, rice, and vegetables together. Season with turmeric and ghee."),
    ],
    "Tuesday": [
        Meal(meal_type="breakfast", name="Whole Wheat Toast with Avocado",
             ingredients=["whole wheat bread", "avocado", "cherry tomatoes", "black pepper", "lemon"],
             calories_approx=350, protein_g=10, carbs_g=42, fat_g=16,
             preparation_notes="Toast bread. Mash avocado with lemon and pepper. Top with tomatoes."),
        Meal(meal_type="lunch", name="Chickpea Curry + Roti",
             ingredients=["chickpeas", "onion", "tomato", "whole wheat roti", "garam masala"],
             calories_approx=500, protein_g=20, carbs_g=75, fat_g=10,
             preparation_notes="Cook chickpeas with onion-tomato gravy. Serve with 2 rotis."),
        Meal(meal_type="snack", name="Mixed Nuts and Seeds",
             ingredients=["almonds", "walnuts", "pumpkin seeds", "sunflower seeds"],
             calories_approx=180, protein_g=6, carbs_g=8, fat_g=14,
             preparation_notes="Measure 30g of mixed nuts and seeds."),
        Meal(meal_type="dinner", name="Moong Dal Soup + Sautéed Greens",
             ingredients=["moong dal", "spinach", "garlic", "olive oil", "cumin"],
             calories_approx=320, protein_g=18, carbs_g=42, fat_g=7,
             preparation_notes="Light moong dal soup. Sauté spinach with garlic in olive oil."),
    ],
    "Wednesday": [
        Meal(meal_type="breakfast", name="Vegetable Poha",
             ingredients=["beaten rice", "peas", "peanuts", "onion", "mustard seeds", "turmeric"],
             calories_approx=330, protein_g=9, carbs_g=55, fat_g=7,
             preparation_notes="Soak poha. Sauté with peas and peanuts. Season with turmeric."),
        Meal(meal_type="lunch", name="Paneer Bhurji + Quinoa",
             ingredients=["paneer", "quinoa", "bell peppers", "onion", "tomato", "spices"],
             calories_approx=520, protein_g=28, carbs_g=55, fat_g=18,
             preparation_notes="Scramble paneer with vegetables. Serve with cooked quinoa."),
        Meal(meal_type="snack", name="Greek Yoghurt with Berries",
             ingredients=["greek yoghurt", "mixed berries", "honey"],
             calories_approx=150, protein_g=12, carbs_g=18, fat_g=2,
             preparation_notes="Top yoghurt with berries and a drizzle of honey."),
        Meal(meal_type="dinner", name="Lentil Vegetable Soup",
             ingredients=["red lentils", "carrots", "celery", "tomato", "thyme", "olive oil"],
             calories_approx=340, protein_g=18, carbs_g=48, fat_g=6,
             preparation_notes="Simmer lentils with vegetables and herbs until tender."),
    ],
    "Thursday": [
        Meal(meal_type="breakfast", name="Banana Smoothie Bowl",
             ingredients=["banana", "almond milk", "chia seeds", "granola", "berries"],
             calories_approx=360, protein_g=8, carbs_g=68, fat_g=6,
             preparation_notes="Blend banana with almond milk. Top with chia seeds, granola, and berries."),
        Meal(meal_type="lunch", name="Rajma Chawal",
             ingredients=["kidney beans", "brown rice", "tomato", "onion", "ginger-garlic", "spices"],
             calories_approx=520, protein_g=22, carbs_g=85, fat_g=6,
             preparation_notes="Slow cook rajma in tomato gravy. Serve with brown rice."),
        Meal(meal_type="snack", name="Hummus with Veggie Sticks",
             ingredients=["hummus", "carrots", "cucumber", "bell pepper"],
             calories_approx=160, protein_g=6, carbs_g=18, fat_g=7,
             preparation_notes="Serve 3 tbsp hummus with raw vegetable sticks."),
        Meal(meal_type="dinner", name="Palak Tofu Stir-fry",
             ingredients=["firm tofu", "spinach", "garlic", "sesame oil", "soy sauce"],
             calories_approx=300, protein_g=20, carbs_g=12, fat_g=16,
             preparation_notes="Pan-fry tofu until golden. Add spinach and garlic. Season with soy sauce."),
    ],
    "Friday": [
        Meal(meal_type="breakfast", name="Idli with Sambar",
             ingredients=["idli batter", "sambar vegetables", "tamarind", "sambar powder"],
             calories_approx=300, protein_g=10, carbs_g=56, fat_g=3,
             preparation_notes="Steam idlis. Prepare vegetable sambar with tamarind base."),
        Meal(meal_type="lunch", name="Chole Salad Bowl",
             ingredients=["chickpeas", "cucumber", "tomato", "red onion", "lemon", "cumin"],
             calories_approx=420, protein_g=18, carbs_g=58, fat_g=8,
             preparation_notes="Toss chickpeas with chopped vegetables and lemon-cumin dressing."),
        Meal(meal_type="snack", name="Roasted Chana",
             ingredients=["roasted chickpeas", "chaat masala", "lemon"],
             calories_approx=130, protein_g=7, carbs_g=18, fat_g=3,
             preparation_notes="Season roasted chana with chaat masala and lemon juice."),
        Meal(meal_type="dinner", name="Vegetable Dal Tadka + Roti",
             ingredients=["mixed dal", "whole wheat roti", "mixed vegetables", "ghee", "spices"],
             calories_approx=400, protein_g=18, carbs_g=60, fat_g=9,
             preparation_notes="Tempering with ghee, cumin, and red chilli. Serve with roti."),
    ],
    "Saturday": [
        Meal(meal_type="breakfast", name="Overnight Chia Pudding",
             ingredients=["chia seeds", "oat milk", "mango", "coconut flakes", "honey"],
             calories_approx=340, protein_g=9, carbs_g=52, fat_g=11,
             preparation_notes="Soak chia in milk overnight. Top with mango and coconut."),
        Meal(meal_type="lunch", name="Stuffed Bell Pepper with Quinoa",
             ingredients=["bell peppers", "quinoa", "black beans", "corn", "cheese", "herbs"],
             calories_approx=480, protein_g=22, carbs_g=62, fat_g=14,
             preparation_notes="Fill peppers with quinoa mixture. Bake at 180°C for 25 min."),
        Meal(meal_type="snack", name="Peanut Butter Rice Cake",
             ingredients=["rice cake", "peanut butter", "banana slices"],
             calories_approx=200, protein_g=6, carbs_g=28, fat_g=8,
             preparation_notes="Spread peanut butter on rice cakes and top with banana slices."),
        Meal(meal_type="dinner", name="Mushroom Sauté + Brown Rice",
             ingredients=["mushrooms", "brown rice", "garlic", "thyme", "olive oil", "parsley"],
             calories_approx=360, protein_g=12, carbs_g=54, fat_g=10,
             preparation_notes="Sauté mushrooms with garlic and thyme. Serve over brown rice."),
    ],
    "Sunday": [
        Meal(meal_type="breakfast", name="Masala Omelette (Egg / Tofu Scramble)",
             ingredients=["eggs or tofu", "onion", "tomato", "green chilli", "coriander", "oil"],
             calories_approx=320, protein_g=18, carbs_g=10, fat_g=22,
             preparation_notes="Whisk eggs (or mash tofu). Cook with vegetables. Season with herbs."),
        Meal(meal_type="lunch", name="Sunday Thali — Dal + Sabzi + Roti + Rice",
             ingredients=["dal", "seasonal vegetable", "whole wheat roti", "brown rice", "raita"],
             calories_approx=600, protein_g=24, carbs_g=90, fat_g=12,
             preparation_notes="Balanced thali with dal, one vegetable sabzi, roti, rice, and curd."),
        Meal(meal_type="snack", name="Fresh Fruit Salad",
             ingredients=["watermelon", "papaya", "pomegranate", "kiwi", "chaat masala"],
             calories_approx=120, protein_g=2, carbs_g=28, fat_g=0.5,
             preparation_notes="Dice seasonal fruits. Sprinkle chaat masala and lemon."),
        Meal(meal_type="dinner", name="Light Moong Dal Chilla",
             ingredients=["moong dal", "ginger", "green chilli", "coriander", "oil"],
             calories_approx=280, protein_g=14, carbs_g=38, fat_g=6,
             preparation_notes="Grind soaked moong dal to batter. Cook like thin pancakes."),
    ],
}

NON_VEG_OVERRIDES = {
    "Monday": {
        "lunch": Meal(meal_type="lunch", name="Chicken Dal Rice Bowl",
                      ingredients=["chicken breast", "dal", "brown rice", "vegetables", "spices"],
                      calories_approx=520, protein_g=38, carbs_g=55, fat_g=10,
                      preparation_notes="Grilled chicken served with dal and brown rice."),
    },
    "Wednesday": {
        "dinner": Meal(meal_type="dinner", name="Grilled Fish with Steamed Vegetables",
                       ingredients=["fish fillet", "broccoli", "carrots", "lemon", "olive oil"],
                       calories_approx=350, protein_g=30, carbs_g=18, fat_g=14,
                       preparation_notes="Marinate fish with lemon and spices. Grill 8 min. Serve with steamed veg."),
    },
}

VEGAN_OVERRIDES = {
    "Wednesday": {
        "lunch": Meal(meal_type="lunch", name="Tofu Bhurji + Quinoa",
                      ingredients=["firm tofu", "quinoa", "bell peppers", "onion", "nutritional yeast"],
                      calories_approx=490, protein_g=26, carbs_g=55, fat_g=14,
                      preparation_notes="Crumble tofu. Sauté with vegetables. Season with nutritional yeast."),
    },
    "Sunday": {
        "breakfast": Meal(meal_type="breakfast", name="Tofu Scramble",
                          ingredients=["firm tofu", "turmeric", "nutritional yeast", "spinach", "mushroom"],
                          calories_approx=280, protein_g=18, carbs_g=12, fat_g=16,
                          preparation_notes="Crumble tofu. Cook with vegetables and turmeric. Season."),
    },
}


# ── Main Generator ─────────────────────────────────────────────────────────────

def generate_structured_meal_plan(user_profile: dict, plan_type: str = "weekly") -> MealPlanResponse:
    """
    Generate a structured meal plan for the user based on their profile.
    """
    diet_pref = user_profile.get("diet_preference", "vegetarian").lower()
    tdee = calculate_tdee(user_profile)
    macros = get_macro_targets(user_profile, tdee)

    # Determine days to generate
    if plan_type == "daily":
        day_names = ["Monday"]
    else:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    days: List[DayPlan] = []
    for day_name in day_names:
        base_meals = list(VEG_MEAL_TEMPLATES.get(day_name, VEG_MEAL_TEMPLATES["Monday"]))

        # Apply diet-specific overrides
        overrides = {}
        if diet_pref in ("non_vegetarian", "non-vegetarian"):
            overrides = NON_VEG_OVERRIDES.get(day_name, {})
        elif diet_pref == "vegan":
            overrides = VEGAN_OVERRIDES.get(day_name, {})

        final_meals = []
        for meal in base_meals:
            override = overrides.get(meal.meal_type)
            final_meals.append(override if override else meal)

        # Filter allergens
        allergies = [a.lower() for a in (user_profile.get("food_allergies") or [])]
        filtered_meals = _filter_allergens(final_meals, allergies)

        total_cal = sum(m.calories_approx for m in filtered_meals)
        total_prot = sum(m.protein_g for m in filtered_meals)
        total_carbs = sum(m.carbs_g for m in filtered_meals)
        total_fat = sum(m.fat_g for m in filtered_meals)

        days.append(DayPlan(
            day=day_name,
            meals=filtered_meals,
            total_calories=total_cal,
            total_protein_g=total_prot,
            total_carbs_g=total_carbs,
            total_fat_g=total_fat,
            hydration_tip="Drink 8–10 glasses of water. Start your morning with warm lemon water.",
        ))

    return MealPlanResponse(
        user_name=user_profile.get("name", "User"),
        plan_type=plan_type,
        days=days,
        disclaimer=MEDICAL_DISCLAIMER,
        nutrition_summary={
            "tdee_kcal": tdee,
            "target_calories": macros["target_calories"],
            "protein_g": macros["protein_g"],
            "carbs_g": macros["carbs_g"],
            "fat_g": macros["fat_g"],
            "primary_goal": macros["primary_goal"],
        },
    )


def _filter_allergens(meals: List[Meal], allergies: List[str]) -> List[Meal]:
    """Remove or flag meals containing allergens."""
    if not allergies:
        return meals
    filtered = []
    for meal in meals:
        ingredients_lower = [i.lower() for i in meal.ingredients]
        contains_allergen = any(
            any(allergen in ingredient for ingredient in ingredients_lower)
            for allergen in allergies
        )
        if not contains_allergen:
            filtered.append(meal)
        else:
            # Keep meal but add a note
            from copy import deepcopy
            safe_meal = deepcopy(meal)
            safe_meal.preparation_notes = (
                (safe_meal.preparation_notes or "") +
                " ⚠️ Contains potential allergens — substitute as needed."
            )
            filtered.append(safe_meal)
    return filtered
