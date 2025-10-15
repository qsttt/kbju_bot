from __future__ import annotations
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum, Float, ForeignKey, Integer, String,
    Boolean, Index, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base

# -------------------- ENUMS --------------------

SexEnum = Enum("male", "female", name="sex_enum")
GoalEnum = Enum("lose", "maintain", "gain", name="goal_enum")
SourceEnum = Enum("manual", "api", "preset", name="source_enum")
PaymentStatusEnum = Enum("pending", "succeeded", "canceled", "failed", name="payment_status_enum")

# -------------------- MODELS --------------------

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
        CheckConstraint("height_cm IS NULL OR height_cm BETWEEN 10 AND 300", name="chk_users_height_range"),
        CheckConstraint("weight_kg IS NULL OR weight_kg BETWEEN 20 AND 500", name="chk_users_weight_range"),
    )


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    amount_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount_unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    amount_grams: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    is_calories_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(SourceEnum, nullable=False, default="manual")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="entries")

    __table_args__ = (
        Index("ix_entries_user_date", "user_id", "date"),
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


class FoodCache(Base):
    __tablename__ = "food_cache"

    food_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    json_payload: Mapped[str] = mapped_column(Text, nullable=False)
    ttl_until: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)


class FoodDictionary(Base):
    __tablename__ = "food_dictionary"

    id: Mapped[int] = mapped_column(primary_key=True)
    food_key: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
