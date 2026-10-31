"""SQLAlchemy relational models for Public Health Command Center, Disease Surveillance, and Telemetry."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.administrative_hierarchy import LTreePath


class DiseaseOutbreakRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Syndromic and laboratory-confirmed disease outbreak cluster record."""

    __tablename__ = "disease_outbreak_records"

    disease_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    disease_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    jurisdiction_path: Mapped[str] = mapped_column(
        LTreePath(),
        nullable=False,
        index=True,
    )
    territory_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    incident_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    seven_day_growth_rate_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    effective_reproduction_rate_rt: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
        index=True,
    )
    cluster_centroid_lat: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    cluster_centroid_lng: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    radius_meters: Mapped[int] = mapped_column(
        Integer,
        default=500,
        nullable=False,
    )
    first_case_reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_case_reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_contained: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_outbreak_path_severity", "jurisdiction_path", "severity"),
        Index("idx_outbreak_path_contained", "jurisdiction_path", "is_contained"),
    )


class FacilityResourceTelemetryModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Hospital and healthcare facility critical care bed capacity and ventilator telemetry."""

    __tablename__ = "facility_resource_telemetry"

    facility_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    facility_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    jurisdiction_path: Mapped[str] = mapped_column(
        LTreePath(),
        nullable=False,
        index=True,
    )
    total_icu_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    occupied_icu_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    available_icu_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    icu_occupancy_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_ventilator_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    available_ventilators: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    oxygen_supported_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    available_oxygen_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    pediatric_icu_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    available_picu_beds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_diverting_admissions: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_facility_telemetry_path_diverting", "jurisdiction_path", "is_diverting_admissions"),
        Index("idx_facility_telemetry_occupancy", "icu_occupancy_pct"),
    )


class PublicHealthDirectiveModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Sovereign containment orders and emergency public health directives."""

    __tablename__ = "public_health_directives"

    issuing_officer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issuing_officer_designation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    jurisdiction_path: Mapped[str] = mapped_column(
        LTreePath(),
        nullable=False,
        index=True,
    )
    territory_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    directive_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    headline: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    details: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )
    affected_population_estimate: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_directive_path_active", "jurisdiction_path", "is_active"),
    )
