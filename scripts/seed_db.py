"""
Инициализация БД и первичное наполнение:
- Создаёт таблицы
- Загружает unit_conversions, category_density, food_seed

Запуск:
    python -m scripts.seed_db
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import engine, SessionLocal
from core.models import Base, UnitConversion, FoodDictionary

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

DEFAULT_UNITS = [
    {"unit": "г", "grams_per_unit": 1, "notes": "грамм"},
    {"unit": "гр", "grams_per_unit": 1, "notes": "грамм"},
    {"unit": "кг", "grams_per_unit": 1000, "notes": "килограмм"},
    {"unit": "мл", "grams_per_unit": 1, "notes": "мл≈г (вода/молочка)"},
    {"unit": "л", "grams_per_unit": 1000, "notes": "литр"},
    {"unit": "шт", "grams_per_unit": 30, "notes": "по умолчанию 30 г/шт (хлеб/печенье), настраиваемо"},
    {"unit": "ч.л.", "grams_per_unit": 5, "notes": "чайная ложка ≈5 г"},
    {"unit": "ст.л.", "grams_per_unit": 20, "notes": "столовая ложка ≈20 г"},
    {"unit": "стакан", "grams_per_unit": 250, "notes": "стакан ≈250 г/мл"},
    {"unit": "ломтик", "grams_per_unit": 25, "notes": "ломтик хлеба ≈25 г"},
]

DEFAULT_FOODS = [
    {
        "food_key": "гречка_сухая",
        "title_ru": "Гречка (сухая)",
        "category": "крупы",
        "per_100g_kcal": 313,
        "per_100g_p": 12.6,
        "per_100g_f": 3.3,
        "per_100g_c": 62.1,
        "density_g_per_ml": None,
        "source": "seed",
    },
    {
        "food_key": "куриная_грудка",
        "title_ru": "Куриная грудка (сырая/без кожи)",
        "category": "мясо",
        "per_100g_kcal": 120,
        "per_100g_p": 23,
        "per_100g_f": 2.6,
        "per_100g_c": 0,
        "density_g_per_ml": None,
        "source": "seed",
    },
    {
        "food_key": "творог_5",
        "title_ru": "Творог 5%",
        "category": "молочка",
        "per_100g_kcal": 121,
        "per_100g_p": 17,
        "per_100g_f": 5,
        "per_100g_c": 3,
        "density_g_per_ml": 1.05,
        "source": "seed",
    },
    {
        "food_key": "йогурт_натуральный",
        "title_ru": "Йогурт натуральный без сахара",
        "category": "молочка",
        "per_100g_kcal": 60,
        "per_100g_p": 4.5,
        "per_100g_f": 3.2,
        "per_100g_c": 4.7,
        "density_g_per_ml": 1.02,
        "source": "seed",
    },
]

async def seed_units(session: AsyncSession):
    for u in DEFAULT_UNITS:
        if not await session.get(UnitConversion, u["unit"]):
            session.add(UnitConversion(**u))
    await session.commit()

async def seed_foods(session: AsyncSession):
    for f in DEFAULT_FOODS:
        exists = await session.execute(
            text("SELECT 1 FROM food_dictionary WHERE food_key = :k"), {"k": f["food_key"]}
        )
        if not exists.first():
            session.add(FoodDictionary(**f))
    await session.commit()

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await seed_units(session)
        await seed_foods(session)

if __name__ == "__main__":
    asyncio.run(main())