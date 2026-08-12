import enum


class BiologicalSex(enum.StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class ActivityLevel(enum.StrEnum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class NutritionGoal(enum.StrEnum):
    LOSE_WEIGHT = "lose_weight"
    MAINTAIN_WEIGHT = "maintain_weight"
    GAIN_WEIGHT = "gain_weight"
    GAIN_MUSCLE = "gain_muscle"


class DietaryPreference(enum.StrEnum):
    NO_PREFERENCE = "no_preference"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    EGGETARIAN = "eggetarian"


class FitnessGoal(enum.StrEnum):
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MAINTAIN_WEIGHT = "maintain_weight"
    MUSCLE_GAIN = "muscle_gain"
    FAT_LOSS = "fat_loss"
    CUSTOM = "custom"
    GENERAL_FITNESS = "general_fitness"


class GoalType(enum.StrEnum):
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MAINTAIN_WEIGHT = "maintain_weight"
    MUSCLE_GAIN = "muscle_gain"
    FAT_LOSS = "fat_loss"
    CUSTOM = "custom"


class GoalStatus(enum.StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskCategory(enum.StrEnum):
    DAILY_HABIT = "daily_habit"
    EXERCISE = "exercise"
    WATER = "water"
    SLEEP = "sleep"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    CUSTOM = "custom"


class TaskRecurrence(enum.StrEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"


class FoodSource(enum.StrEnum):
    USDA = "usda"
    OPEN_FOOD_FACTS = "open_food_facts"
    USER_CREATED = "user_created"
    AI_DETECTED = "ai_detected"


class MealType(enum.StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class ChatRole(enum.StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
