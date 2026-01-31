"""SQLAlchemy ORM models for Roost (SQLite)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Onboarding
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    past_avg_rent: Mapped[float] = mapped_column(Float, default=0.0)  # monthly CAD
    savings_rate_cad: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # CAD/month
    savings_rate_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    commute_tolerance_mins: Mapped[int] = mapped_column(Integer, default=30)
    preferred_household_size: Mapped[int] = mapped_column(Integer, default=2)  # 2 or 3
    budget_min: Mapped[float] = mapped_column(Float, default=0.0)
    budget_max: Mapped[float] = mapped_column(Float, default=3000.0)

    # Lifestyle (simple toggles)
    quiet_hours: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    pets_ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    smoking_ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    guests_ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Contact (blurred until match)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contact_social: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Optional: work/school address for commute (stored hashed or just area for MVP)
    commute_destination: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    neighborhood_preference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Computed/cached for display (optional)
    monthly_savings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # derived from rent + savings_rate

    # Relationships
    swipes_given: Mapped[list] = relationship("Swipe", foreign_keys="Swipe.viewer_profile_id", back_populates="viewer")
    swipes_received: Mapped[list] = relationship("Swipe", foreign_keys="Swipe.target_profile_id", back_populates="target")
    matches_as_1: Mapped[list] = relationship("Match", foreign_keys="Match.profile_id_1", back_populates="profile_1")
    matches_as_2: Mapped[list] = relationship("Match", foreign_keys="Match.profile_id_2", back_populates="profile_2")


class Swipe(Base):
    __tablename__ = "swipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    viewer_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id"), nullable=False)
    target_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # 'like' | 'pass'

    viewer: Mapped["Profile"] = relationship("Profile", foreign_keys=[viewer_profile_id], back_populates="swipes_given")
    target: Mapped["Profile"] = relationship("Profile", foreign_keys=[target_profile_id], back_populates="swipes_received")

    __table_args__ = (UniqueConstraint("viewer_profile_id", "target_profile_id", name="uq_swipe_pair"),)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile_id_1: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id"), nullable=False)
    profile_id_2: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id"), nullable=False)
    # Optional: attached listing (JSON or external URL)
    attached_listing_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    profile_1: Mapped["Profile"] = relationship("Profile", foreign_keys=[profile_id_1], back_populates="matches_as_1")
    profile_2: Mapped["Profile"] = relationship("Profile", foreign_keys=[profile_id_2], back_populates="matches_as_2")

    __table_args__ = (UniqueConstraint("profile_id_1", "profile_id_2", name="uq_match_pair"),)
