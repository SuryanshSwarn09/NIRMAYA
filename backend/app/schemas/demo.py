from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioCategoryEnum(str, Enum):
    """Categorization for interactive guided demonstration scenarios."""
    CLINICAL_WORKFLOW = "CLINICAL_WORKFLOW"
    EMERGENCY_SECURITY = "EMERGENCY_SECURITY"
    EDGE_OFFLINE_SYNC = "EDGE_OFFLINE_SYNC"
    LEGACY_FEDERATION = "LEGACY_FEDERATION"
    PUBLIC_HEALTH_GOVERNANCE = "PUBLIC_HEALTH_GOVERNANCE"


class ScenarioExecutionStatus(str, Enum):
    """Execution state of an interactive demonstration scenario."""
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ScenarioStep(BaseModel):
    """Discrete atomic stage within an interactive demonstration scenario."""
    step_number: int = Field(..., ge=1, description="Sequential step index")
    title: str = Field(..., description="Short name of demonstration step")
    description: str = Field(..., description="Detailed clinical and technical actions performed")
    subsystem: str = Field(..., description="Target architectural subsystem executed")
    expected_duration_ms: float = Field(..., description="Target latency threshold in milliseconds")
    telemetry_output: Dict[str, Any] = Field(default_factory=dict, description="Step execution output data")


class DemoScenario(BaseModel):
    """Complete specification of a guided interactive sandbox scenario."""
    scenario_id: str = Field(..., description="Unique scenario identifier (e.g., SCEN-01-CONSULTATION)")
    title: str = Field(..., description="Primary scenario title")
    subtitle: str = Field(..., description="Clinical context and architectural theme")
    category: ScenarioCategoryEnum
    prerequisites: List[str] = Field(default_factory=list, description="Initial system state requirements")
    steps: List[ScenarioStep] = Field(default_factory=list, description="Ordered execution steps")
    sla_target_ms: float = Field(..., description="Total permissible end-to-end scenario duration in ms")
    status: ScenarioExecutionStatus = Field(default=ScenarioExecutionStatus.READY)


class ScenarioExecutionResult(BaseModel):
    """Detailed telemetry and verification results from a live scenario run."""
    execution_id: str = Field(..., description="Unique scenario execution instance ID")
    scenario_id: str = Field(..., description="Identifier of executed scenario")
    status: ScenarioExecutionStatus = Field(default=ScenarioExecutionStatus.SUCCESS)
    elapsed_ms: float = Field(..., description="Total wall-clock duration in milliseconds")
    steps_completed: int = Field(..., description="Number of steps executed successfully")
    total_steps: int = Field(..., description="Total steps in scenario definition")
    assertions_verified: List[str] = Field(default_factory=list, description="Clinical and security checks passed")
    cryptographic_proofs: List[str] = Field(default_factory=list, description="Cryptographic artifacts verified")
    live_telemetry: Dict[str, Any] = Field(default_factory=dict, description="Live execution telemetry data")
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SlideItem(BaseModel):
    """Structured content for a technical defense slide."""
    slide_number: int = Field(..., ge=1, le=12, description="Sequential slide index")
    title: str = Field(..., description="Slide headline")
    subtitle: str = Field(..., description="Sub-heading or thematic category")
    bullets: List[str] = Field(default_factory=list, description="Key conceptual bullets")
    diagram_ascii: Optional[str] = Field(None, description="ASCII or structured architecture schematic")
    key_metrics: Dict[str, str] = Field(default_factory=dict, description="Empirical scorecard metrics")


class SlideDeckMetadata(BaseModel):
    """Metadata and complete slide collection for the capstone defense deck."""
    title: str = Field(default="NIRMAYA: Sovereign National Health Information Network")
    subtitle: str = Field(default="Capstone Engineering Defense & Architecture Walkthrough")
    author: str = Field(default="Suryansh Swarn")
    institution: str = Field(default="Department of Computer Science & Engineering")
    version: str = Field(default="1.0.0")
    total_slides: int = Field(default=12)
    slides: List[SlideItem] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
