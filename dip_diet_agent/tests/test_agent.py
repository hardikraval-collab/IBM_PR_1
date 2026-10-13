"""
Unit tests for DIP Diet RAG Agent.
Run with: python -m pytest tests/ -v
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import json


class TestConfig:
    """Test configuration loading."""

    def test_config_imports(self):
        from backend.config import (
            MEDICAL_DISCLAIMER, SAFETY_KEYWORDS, DEMO_MODE,
            CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS
        )
        assert len(MEDICAL_DISCLAIMER) > 50
        assert len(SAFETY_KEYWORDS) > 0
        assert CHUNK_SIZE > 0
        assert CHUNK_OVERLAP > 0
        assert TOP_K_RESULTS > 0

    def test_demo_mode_flag(self):
        """Without credentials, demo mode should be active."""
        from backend.config import WATSONX_API_KEY, WATSONX_PROJECT_ID
        # In test environment, demo mode is expected if no credentials set
        assert isinstance(WATSONX_API_KEY, str)
        assert isinstance(WATSONX_PROJECT_ID, str)


class TestModels:
    """Test Pydantic data models."""

    def test_user_profile_minimal(self):
        from backend.models import UserProfile, UserLocation
        profile = UserProfile(
            name="Test User",
            age=25,
            location=UserLocation(city="Test City", country="India")
        )
        assert profile.name == "Test User"
        assert profile.age == 25
        assert profile.diet_preference == "vegetarian"
        assert profile.activity_level == "moderately_active"

    def test_user_profile_full(self):
        from backend.models import (
            UserProfile, UserLocation, DietPreference,
            ActivityLevel, NutritionGoal
        )
        profile = UserProfile(
            name="Priya Sharma",
            age=30,
            gender="female",
            weight_kg=65.0,
            height_cm=165.0,
            diet_preference=DietPreference.vegetarian,
            food_allergies=["peanuts"],
            medical_history=["type 2 diabetes"],
            activity_level=ActivityLevel.moderately_active,
            nutrition_goals=[NutritionGoal.weight_loss],
            location=UserLocation(city="Mumbai", country="India")
        )
        assert profile.name == "Priya Sharma"
        assert "peanuts" in profile.food_allergies
        assert "type 2 diabetes" in profile.medical_history

    def test_chat_request_model(self):
        from backend.models import ChatRequest
        req = ChatRequest(user_id="user_001", message="What should I eat?")
        assert req.user_id == "user_001"
        assert req.message == "What should I eat?"
        assert req.conversation_history == []

    def test_meal_plan_request_model(self):
        from backend.models import MealPlanRequest
        req = MealPlanRequest(user_id="user_001", plan_type="weekly")
        assert req.plan_type == "weekly"

    def test_age_validation(self):
        from backend.models import UserProfile, UserLocation
        with pytest.raises(Exception):
            UserProfile(name="Test", age=200, location=UserLocation(city="X", country="Y"))


class TestMealPlanGenerator:
    """Test meal plan generation."""

    def setup_method(self):
        self.profile_veg = {
            "name": "Test Veg User",
            "age": 28,
            "gender": "female",
            "weight_kg": 60,
            "height_cm": 162,
            "diet_preference": "vegetarian",
            "food_allergies": [],
            "medical_history": [],
            "activity_level": "moderately_active",
            "nutrition_goals": ["maintenance"],
            "location": {"city": "Mumbai", "country": "India"},
        }
        self.profile_nonveg = {**self.profile_veg, "diet_preference": "non_vegetarian", "name": "Test NV User"}
        self.profile_vegan = {**self.profile_veg, "diet_preference": "vegan", "name": "Test Vegan User"}

    def test_calculate_tdee_female(self):
        from backend.meal_plan_generator import calculate_tdee
        tdee = calculate_tdee(self.profile_veg)
        assert 1400 <= tdee <= 3500

    def test_calculate_tdee_fallback(self):
        from backend.meal_plan_generator import calculate_tdee
        tdee = calculate_tdee({})
        assert tdee >= 1200

    def test_macro_targets_weight_loss(self):
        from backend.meal_plan_generator import calculate_tdee, get_macro_targets
        profile = {**self.profile_veg, "nutrition_goals": ["weight_loss"]}
        tdee = calculate_tdee(profile)
        macros = get_macro_targets(profile, tdee)
        assert macros["target_calories"] < tdee
        assert macros["protein_g"] > 0
        assert macros["carbs_g"] > 0
        assert macros["fat_g"] > 0

    def test_daily_meal_plan_vegetarian(self):
        from backend.meal_plan_generator import generate_structured_meal_plan
        plan = generate_structured_meal_plan(self.profile_veg, "daily")
        assert plan.plan_type == "daily"
        assert len(plan.days) == 1
        assert len(plan.days[0].meals) >= 3
        assert plan.days[0].total_calories > 0

    def test_weekly_meal_plan_has_7_days(self):
        from backend.meal_plan_generator import generate_structured_meal_plan
        plan = generate_structured_meal_plan(self.profile_veg, "weekly")
        assert len(plan.days) == 7

    def test_meal_plan_has_disclaimer(self):
        from backend.meal_plan_generator import generate_structured_meal_plan
        plan = generate_structured_meal_plan(self.profile_veg, "daily")
        assert len(plan.disclaimer) > 10

    def test_vegan_plan_generated(self):
        from backend.meal_plan_generator import generate_structured_meal_plan
        plan = generate_structured_meal_plan(self.profile_vegan, "daily")
        assert plan is not None
        assert len(plan.days) >= 1

    def test_allergen_filter(self):
        from backend.meal_plan_generator import generate_structured_meal_plan
        profile_with_allergy = {**self.profile_veg, "food_allergies": ["peanuts", "dairy"]}
        plan = generate_structured_meal_plan(profile_with_allergy, "daily")
        assert plan is not None


class TestShoppingList:
    """Test shopping list generation."""

    def setup_method(self):
        self.profile = {
            "name": "Test User",
            "age": 30,
            "gender": "female",
            "weight_kg": 65,
            "height_cm": 165,
            "diet_preference": "vegetarian",
            "food_allergies": [],
            "medical_history": [],
            "activity_level": "moderately_active",
            "nutrition_goals": ["maintenance"],
            "location": {"city": "Mumbai", "country": "India"},
        }

    def test_shopping_list_generated(self):
        from backend.shopping_list_generator import generate_shopping_list
        result = generate_shopping_list(self.profile)
        assert result.total_items > 0
        assert len(result.items) > 0
        assert len(result.tips) > 0

    def test_shopping_items_have_category(self):
        from backend.shopping_list_generator import generate_shopping_list
        result = generate_shopping_list(self.profile)
        for item in result.items:
            assert item.category
            assert item.item
            assert item.quantity

    def test_shopping_list_excludes_allergens(self):
        from backend.shopping_list_generator import generate_shopping_list
        profile_with_allergy = {**self.profile, "food_allergies": ["peanuts"]}
        result = generate_shopping_list(profile_with_allergy)
        items_lower = [i.item.lower() for i in result.items]
        assert not any("peanut" in item for item in items_lower)


class TestRAGPipeline:
    """Test RAG pipeline components (lightweight — no full inference)."""

    def test_safety_check_safe_query(self):
        from backend.rag_pipeline import rag_pipeline
        assert rag_pipeline.is_safe_query("What should I eat for breakfast?") is True
        assert rag_pipeline.is_safe_query("Tell me about DIP Diet proteins") is True

    def test_safety_check_unsafe_query(self):
        from backend.rag_pipeline import rag_pipeline
        assert rag_pipeline.is_safe_query("Can you diagnose my diabetes?") is False
        assert rag_pipeline.is_safe_query("What prescription do I need?") is False

    def test_ingest_and_retrieve(self):
        from backend.rag_pipeline import rag_pipeline
        n = rag_pipeline.ingest_text(
            content="Brown rice is a whole grain with 111 calories per 100g cooked. "
                    "It contains 2.6g protein, 23g carbohydrates, and 0.9g fat. "
                    "Brown rice has a low glycaemic index of 50, making it ideal for diabetics.",
            title="Test Nutrition Doc",
            source_name="test_source.txt",
        )
        assert n >= 1

        # Test retrieval
        results = rag_pipeline.retrieve("brown rice nutrition", top_k=2)
        assert isinstance(results, list)

    def test_profile_context_builder(self):
        from backend.rag_pipeline import RAGPipeline
        profile = {
            "name": "Priya",
            "age": 30,
            "diet_preference": "vegetarian",
            "food_allergies": ["peanuts"],
            "activity_level": "moderately_active",
            "nutrition_goals": ["weight_loss"],
            "location": {"city": "Mumbai", "country": "India"},
        }
        ctx = RAGPipeline._build_profile_context(profile)
        assert "Priya" in ctx
        assert "vegetarian" in ctx
        assert "peanuts" in ctx


class TestLLMClient:
    """Test LLM client demo mode."""

    def test_demo_mode_response_not_empty(self):
        from backend.llm_client import GraniteLLMClient
        client = GraniteLLMClient()
        # Force demo mode for testing
        client.demo_mode = True
        response = client._demo_generate("What should I eat for breakfast?")
        assert len(response) > 50
        assert "DISCLAIMER" in response.upper() or "disclaimer" in response.lower()

    def test_demo_mode_dip_diet_response(self):
        from backend.llm_client import GraniteLLMClient
        client = GraniteLLMClient()
        client.demo_mode = True
        response = client._demo_generate("What is the DIP Diet?")
        assert "DIP" in response

    def test_demo_mode_weight_loss_response(self):
        from backend.llm_client import GraniteLLMClient
        client = GraniteLLMClient()
        client.demo_mode = True
        response = client._demo_generate("How do I lose weight?")
        assert len(response) > 30
