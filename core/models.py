from __future__ import annotations
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    CheckConstraint, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String,
    UniqueConstraint, Boolean, Index, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base

# Базовые перечисления
SexEnum = Enum("male", "female", name="sex_enum")
GoalEnum = Enum("lose", "maintain", "gain", name="goal_enum")
SourceEnum = Enum("manual", "db", "api", "custom", name="source_enum")
PaymentStatusEnum = Enum("pending", "succeeded", "canceled", "failed", name="payment_status_enum")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    sex: Mapped[Optional[str]] = mapped_column(SexEnum, nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    goal: Mapped[Optional[str]] = mapped_column(GoalEnum, nullable=True)
    pal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    tz: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Moscow")
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    entries: Mapped[list[Entry]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list[Payment]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("age IS NULL OR (age >= 10 AND age <= 100)", name="chk_users_age_range"),
        CheckConstraint("height_cm IS NULL OR height_cm BETWEEN 100 AND 250", name="chk_users_height"),
        CheckConstraint("weight_kg IS NULL OR weight_kg BETWEEN 30 AND 400", name="chk_users_weight"),
        Index("ix_users_is_admin", "is_admin"),
    )

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)  # Храним UTC-день

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_value: Mapped[float] = mapped_column(Float, nullable=False)
    amount_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_grams: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    is_calories_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(SourceEnum, default="manual", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates="entries")

    __table_args__ = (
        CheckConstraint("amount_value > 0", name="chk_entries_amount_positive"),
        CheckConstraint("amount_grams IS NULL OR amount_grams > 0", name="chk_entries_amount_grams_positive"),
        CheckConstraint("kcal IS NULL OR kcal >= 0", name="chk_entries_kcal_nonneg"),
        CheckConstraint("protein IS NULL OR protein >= 0", name="chk_entries_p_nonneg"),
        CheckConstraint("fat IS NULL OR fat >= 0", name="chk_entries_f_nonneg"),
        CheckConstraint("carbs IS NULL OR carbs >= 0", name="chk_entries_c_nonneg"),
        Index("ix_entries_user_date", "user_id", "date"),
    )

class FoodDictionary(Base):
    __tablename__ = "food_dictionary"

    id: Mapped[int] = mapped_column(primary_key=True)
    food_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    title_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    per_100g_kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_100g_p: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_100g_f: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_100g_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    density_g_per_ml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(Enum("seed", "api", "user", name="dict_source_enum"), default="seed", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("per_100g_kcal IS NULL OR per_100g_kcal >= 0", name="chk_dict_kcal_nonneg"),
    )

class UserCustomFood(Base):
    __tablename__ = "user_custom_foods"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    per_100g_kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_100g_p: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_100g_f: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_100g_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    default_unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "title", name="uq_user_custom_title"),
    )

class FoodCache(Base):
    __tablename__ = "food_cache"

    food_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    json_payload: Mapped[str] = mapped_column(Text, nullable=False)
    ttl_until: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True, nullable=False)

class UnitConversion(Base):
    __tablename__ = "unit_conversions"

    unit: Mapped[str] = mapped_column(String(32), primary_key=True)
    grams_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("grams_per_unit > 0", name="chk_units_positive"),
    )

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="yookassa")
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RUB")
    status: Mapped[str] = mapped_column(PaymentStatusEnum, nullable=False, default="pending")
    payment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payment_amount_nonneg"),
        Index("ix_payments_user_created", "user_id", "created_at"),
    )