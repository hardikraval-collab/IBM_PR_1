"""
Pydantic data models for the DIP Diet RAG Agent API.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DietPreference(str, Enum):
    vegetarian = "vegetarian"
    non_vegetarian = "non_vegetarian"
    vegan = "vegan"
    pescatarian = "pescatarian"
    flexitarian = "flexitarian"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    super_active = "super_active"


class NutritionGoal(str, Enum):
    weight_loss = "weight_loss"
    weight_gain = "weight_gain"
    muscle_gain = "muscle_gain"
    maintenance = "maintenance"
    energy_boost = "energy_boost"
    manage_diabetes = "manage_diabetes"
    heart_health = "heart_health"
    gut_health = "gut_health"


class UserLocation(BaseModel):
    city: str = Field(...)
    country: str = Field(...)


class UserProfile(BaseModel):
    user_id: Optional[str] = None
    name: str = Field(...)
    age: int = Field(..., ge=5, le=120)
    gender: Optional[str] = Field(None)
    weight_kg: Optional[float] = Field(None, ge=10, le=500)
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    diet_preference: DietPreference = DietPreference.vegetarian
    food_allergies: List[str] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)
    activity_level: ActivityLevel = ActivityLevel.moderately_active
    nutrition_goals: List[NutritionGoal] = Field(
        default_factory=lambda: [NutritionGoal.maintenance]
    )
    location: UserLocation = Field(
        default_factory=lambda: UserLocation(city="Unknown", country="Unknown")
    )
    additional_notes: Optional[str] = None


class ChatMessage(BaseModel):
    role: str = Field(...)  # "user" or "assistant"
    content: str = Field(...)


class ChatRequest(BaseModel):
    user_id: str = Field(...)
    message: str = Field(...)
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class SourceCitation(BaseModel):
    source: str
    excerpt: str
    relevance_score: float


class ChatResponse(BaseModel):
    response: str
    sources: List[SourceCitation] = Field(default_factory=list)
    disclaimer: str
    is_safe: bool = True


class MealPlanRequest(BaseModel):
    user_id: str
    plan_type: str = Field(default="weekly")  # "daily" or "weekly"


class Meal(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    name: str
    ingredients: List[str]
    calories_approx: int
    protein_g: float
    carbs_g: float
    fat_g: float
    preparation_notes: Optional[str] = None


class DayPlan(BaseModel):
    day: str
    meals: List[Meal]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    hydration_tip: Optional[str] = None


class MealPlanResponse(BaseModel):
    user_name: str
    plan_type: str
    days: List[DayPlan]
    disclaimer: str
    nutrition_summary: Dict[str, Any] = Field(default_factory=dict)


class ShoppingItem(BaseModel):
    item: str
    quantity: str
    category: str  # vegetables, fruits, grains, proteins, dairy, spices, etc.


class ShoppingListResponse(BaseModel):
    user_name: str
    items: List[ShoppingItem]
    total_items: int
    tips: List[str] = Field(default_factory=list)


class SubstitutionRequest(BaseModel):
    user_id: str
    food_item: str = Field(...)
    reason: Optional[str] = Field(None)


class SubstitutionResponse(BaseModel):
    original_food: str
    substitutions: List[Dict[str, str]]
    explanation: str
    disclaimer: str


class IngestRequest(BaseModel):
    source_type: str = Field(default="text")  # "text", "url", "file"
    content: str = Field(...)
    title: str = Field(...)
    source_name: str = Field(...)
