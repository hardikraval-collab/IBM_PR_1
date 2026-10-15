"""
IBM Granite LLM client with WatsonX integration and demo fallback.
"""
import logging
from typing import Optional
from backend.config import (
    WATSONX_API_KEY,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
    GRANITE_MODEL_ID,
    LLM_MAX_NEW_TOKENS,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_REPETITION_PENALTY,
    DEMO_MODE,
    MEDICAL_DISCLAIMER,
)

logger = logging.getLogger(__name__)


class GraniteLLMClient:
    """
    Client for IBM Granite LLM via WatsonX.ai.
    Falls back to a rule-based demo response when credentials are absent.
    """

    def __init__(self):
        self.demo_mode = DEMO_MODE
        self.model = None

        if not self.demo_mode:
            self._init_watsonx()
        else:
            logger.warning(
                "WatsonX credentials not found. Running in DEMO mode. "
                "Set WATSONX_API_KEY and WATSONX_PROJECT_ID in .env to enable IBM Granite."
            )

    def _init_watsonx(self):
        """Initialize IBM WatsonX client."""
        try:
            from ibm_watsonx_ai.foundation_models import ModelInference
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

            self.model = ModelInference(
                model_id=GRANITE_MODEL_ID,
                credentials={
                    "apikey": WATSONX_API_KEY,
                    "url": WATSONX_URL,
                },
                project_id=WATSONX_PROJECT_ID,
                params={
                    GenParams.MAX_NEW_TOKENS: LLM_MAX_NEW_TOKENS,
                    GenParams.TEMPERATURE: LLM_TEMPERATURE,
                    GenParams.TOP_P: LLM_TOP_P,
                    GenParams.REPETITION_PENALTY: LLM_REPETITION_PENALTY,
                    GenParams.STOP_SEQUENCES: ["<|endoftext|>", "Human:", "User:"],
                },
            )
            logger.info(f"IBM Granite LLM initialized: {GRANITE_MODEL_ID}")
        except ImportError:
            logger.error(
                "ibm-watsonx-ai package not installed. "
                "Run: pip install ibm-watsonx-ai"
            )
            self.demo_mode = True
        except Exception as exc:
            # Treat any init failure (bad key, network, timeout) as demo mode
            # so startup is never blocked by credential errors.
            logger.warning(
                f"WatsonX init failed — falling back to DEMO mode. "
                f"Reason: {exc}"
            )
            self.model = None
            self.demo_mode = True

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from IBM Granite LLM.

        Args:
            prompt: The user query prompt with retrieved context.
            system_prompt: Optional system-level instruction.

        Returns:
            Generated text response.
        """
        if self.demo_mode:
            return self._demo_generate(prompt)

        full_prompt = self._build_prompt(prompt, system_prompt)
        try:
            response = self.model.generate_text(prompt=full_prompt)
            return response.strip()
        except Exception as exc:
            logger.error(f"LLM generation error: {exc}")
            return self._demo_generate(prompt)

    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Construct the full prompt in Granite instruction format."""
        system = system_prompt or self._default_system_prompt()
        return (
            f"<|system|>\n{system}\n"
            f"<|user|>\n{prompt}\n"
            f"<|assistant|>\n"
        )

    @staticmethod
    def _default_system_prompt() -> str:
        return (
            "You are a knowledgeable and compassionate DIP Diet nutrition assistant. "
            "You provide evidence-based dietary guidance based on the DIP (Discipline Intermittent Protocol) Diet framework. "
            "Always be helpful, respectful, and culturally sensitive. "
            "When citing information, reference the source documents provided in context. "
            "Always include a medical disclaimer when discussing health-related topics. "
            "Do NOT provide medical diagnoses, prescriptions, or treatment plans. "
            "Encourage users to consult registered dietitians or healthcare professionals for personalized medical advice."
        )

    def _demo_generate(self, prompt: str) -> str:
        """
        Rule-based demo response when WatsonX credentials are unavailable.
        Provides helpful DIP Diet guidance without LLM inference.
        """
        prompt_lower = prompt.lower()

        # Meal plan questions
        if any(w in prompt_lower for w in ["breakfast", "morning meal", "what to eat for breakfast"]):
            return (
                "**DIP Diet Breakfast Suggestions:**\n\n"
                "• **Option 1 (Vegetarian):** Overnight oats with chia seeds, fresh berries, and a drizzle of honey — "
                "approx. 350 kcal, 12g protein.\n"
                "• **Option 2:** Whole-grain toast with avocado, poached egg (if non-veg), and cherry tomatoes — "
                "approx. 380 kcal, 18g protein.\n"
                "• **Option 3 (Vegan):** Smoothie bowl with banana, spinach, almond milk, topped with granola and seeds — "
                "approx. 320 kcal, 10g protein.\n\n"
                "💡 *DIP Diet Tip:* Break your fast with a protein-rich meal to stabilise blood sugar and sustain energy.\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )

        if any(w in prompt_lower for w in ["lunch", "midday", "afternoon"]):
            return (
                "**DIP Diet Lunch Suggestions:**\n\n"
                "• **Veg Dal + Brown Rice:** High-protein lentil curry with fibre-rich brown rice — "
                "approx. 480 kcal, 22g protein.\n"
                "• **Quinoa Salad:** Quinoa with roasted vegetables, chickpeas, lemon-tahini dressing — "
                "approx. 420 kcal, 18g protein.\n"
                "• **Grilled Chicken Wrap (Non-Veg):** Whole-wheat wrap with grilled chicken, greens, and yoghurt sauce — "
                "approx. 520 kcal, 35g protein.\n\n"
                "💡 *DIP Diet Tip:* Include at least two servings of vegetables at lunch for micronutrient density.\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )

        if any(w in prompt_lower for w in ["dinner", "evening meal", "supper"]):
            return (
                "**DIP Diet Dinner Suggestions:**\n\n"
                "• **Light Dal Soup + Roti:** Easy on digestion, high in plant protein.\n"
                "• **Stir-fried Tofu + Vegetables:** Rich in calcium and iron.\n"
                "• **Grilled Fish + Steamed Vegetables (Non-Veg):** Omega-3 rich, low-calorie.\n\n"
                "💡 *DIP Diet Tip:* Keep dinner light and eat at least 2–3 hours before bedtime for optimal digestion.\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )

        if any(w in prompt_lower for w in ["snack", "between meals", "hunger"]):
            return (
                "**DIP Diet Healthy Snack Options:**\n\n"
                "• Handful of mixed nuts (almonds, walnuts, cashews) — 150–180 kcal\n"
                "• Apple or banana with peanut butter — 200 kcal\n"
                "• Greek yoghurt with berries — 120 kcal\n"
                "• Hummus with carrot sticks — 130 kcal\n"
                "• Roasted chana (chickpeas) — 120 kcal\n\n"
                "💡 *DIP Diet Tip:* Snack mindfully. Choose whole foods over processed alternatives.\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )

        if any(w in prompt_lower for w in ["protein", "protein sources", "high protein"]):
            return (
                "**High-Protein DIP Diet Foods:**\n\n"
                "**Plant-Based:** Lentils (dal), chickpeas, rajma, tofu, tempeh, edamame, quinoa, hemp seeds.\n"
                "**Dairy:** Greek yoghurt, paneer, cottage cheese, milk.\n"
                "**Non-Veg:** Eggs, chicken breast, fish (salmon, tuna), turkey.\n\n"
                "**Recommended Daily Intake:** 0.8–1.2g protein per kg body weight for maintenance; "
                "1.6–2.2g/kg for muscle gain.\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )

        if any(w in prompt_lower for w in ["weight loss", "lose weight", "fat loss"]):
            return (
                "**DIP Diet Weight Loss Strategy:**\n\n"
                "1. **Caloric Deficit:** Reduce daily intake by 300–500 kcal below your TDEE.\n"
                "2. **Intermittent Fasting:** 16:8 window (eat within 8 hours, fast 16 hours).\n"
                "3. **Prioritise Protein:** 1.2–1.6g/kg body weight to preserve muscle.\n"
                "4. **Whole Foods Only:** Avoid ultra-processed foods, refined sugars, trans fats.\n"
                "5. **Hydration:** Drink 2.5–3L of water daily.\n"
                "6. **Activity:** 150 min moderate exercise per week minimum.\n\n"
                "💡 Aim for 0.5–1kg loss per week for sustainable results.\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )

        if any(w in prompt_lower for w in ["dip diet", "what is dip", "about dip"]):
            return (
                "**What is the DIP Diet?**\n\n"
                "DIP stands for **Discipline Intermittent Protocol** — a holistic nutrition framework combining:\n\n"
                "• **Disciplined eating patterns** with structured meal timing\n"
                "• **Intermittent fasting** aligned with your body's circadian rhythm\n"
                "• **Whole-food, plant-forward nutrition** with quality proteins\n"
                "• **Personalised macros** based on your unique goals and activity level\n\n"
                "**Core Principles:**\n"
                "1. Eat real, minimally processed foods\n"
                "2. Respect your hunger and fullness cues\n"
                "3. Maintain a consistent eating window\n"
                "4. Prioritise sleep, stress management, and hydration\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )

        # Default response
        return (
            "Thank you for your question! As your DIP Diet nutrition assistant, I can help you with:\n\n"
            "• 🥗 **Meal suggestions** — breakfast, lunch, dinner, and snacks\n"
            "• 📅 **Meal planning** — daily and weekly structured plans\n"
            "• 🛒 **Shopping lists** — based on your personalised meal plan\n"
            "• 🔄 **Food substitutions** — for allergies, preferences, or availability\n"
            "• 💪 **Nutrition guidance** — protein, carbs, fats, vitamins, and minerals\n"
            "• 🧘 **DIP Diet principles** — intermittent fasting, meal timing, lifestyle\n\n"
            "Please ask me a specific nutrition question to get started!\n\n"
            f"_{MEDICAL_DISCLAIMER}_"
        )


# Singleton instance
llm_client = GraniteLLMClient()
