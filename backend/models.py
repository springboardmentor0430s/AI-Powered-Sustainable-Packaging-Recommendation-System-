from __future__ import annotations

from sqlalchemy import (
    Column, BigInteger, Text, DateTime, ForeignKey,
    Float, Integer, SmallInteger
)
# Attempt to use PostgreSQL's JSONB type if available; otherwise fall back
# to the generic JSON type.  SQLite supports JSON natively in modern versions
# and will map this to TEXT under the hood.
try:
    from sqlalchemy.dialects.postgresql import JSONB as JSONType
except Exception:
    from sqlalchemy.types import JSON as JSONType
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    company_name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    runs = relationship("RecommendationRun", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")

    # --- Personalized model weights ---
    # These optional weights allow each company/user to tailor how material recommendations
    # are scored.  Values should sum to 1.0 (backend code will normalise if not).
    weight_co2 = Column(Float, nullable=True, default=None)  # weight for CO₂ impact in suitability
    weight_cost = Column(Float, nullable=True, default=None)  # weight for cost efficiency in suitability
    weight_risk = Column(Float, nullable=True, default=None)  # weight for risk/constraints in suitability

    # The company sustainability score is computed on demand and does not need to be persisted,
    # but we persist the last computed value for easier analytics.  This value ranges 0–100.
    last_sustainability_score = Column(Float, nullable=True)


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # inputs
    product_name = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    weight_kg = Column(Float, nullable=True)
    fragility = Column(Integer, nullable=True)
    max_budget = Column(Float, nullable=True)
    shipping_distance = Column(Float, nullable=True)
    moisture_req = Column(Integer, nullable=True)
    oxygen_sensitivity = Column(Integer, nullable=True)
    preferred_biodegradable = Column(SmallInteger, nullable=True)
    preferred_recyclable = Column(SmallInteger, nullable=True)

    # top-1 summary
    top_material_id = Column(Text, nullable=True)
    top_material_name = Column(Text, nullable=True)
    top_pred_cost = Column(Float, nullable=True)
    top_pred_co2 = Column(Float, nullable=True)
    top_score = Column(Float, nullable=True)

    # full list
    recommendations_json = Column(JSONType, nullable=False)

    user = relationship("AppUser", back_populates="runs")

    # Feedback relationship (one-to-many): a run may have multiple feedback entries for different
    # recommended materials.  Cascading ensures that deleting a run removes associated feedback.
    feedbacks = relationship("Feedback", back_populates="run", cascade="all, delete-orphan")


class Feedback(Base):
    """
    Record user feedback on recommendations.  Each feedback entry corresponds to a specific
    RecommendationRun and optionally a material from that run.  The user can rate how
    suitable the recommendation was (1–5) and provide optional comments for improvements.
    """
    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True, index=True)
    run_id = Column(BigInteger, ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False)
    material_name = Column(Text, nullable=True)
    rating = Column(Integer, nullable=False)  # 1–5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    run = relationship("RecommendationRun", back_populates="feedbacks")


class AuditLog(Base):
    """
    Lightweight audit logging table.  Records actions performed by users along with arbitrary
    JSON details (e.g. parameters used).  This is critical for compliance and traceability.
    The log can grow large over time; consider archiving or pruning in production.
    """
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(Text, nullable=False)
    details = Column(JSONType, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    role = Column(Text, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    related_run_id = Column(BigInteger, ForeignKey("recommendation_runs.id", ondelete="SET NULL"), nullable=True)

    user = relationship("AppUser", back_populates="chats")
