"""
API Schemas
===========
Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# Common Responses
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime
    components: Optional[Dict[str, bool]] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Facility Schemas
# ============================================================================

class FacilityCreate(BaseModel):
    """Request to create a new facility."""
    name: str
    facility_type: str = Field(description="production, gathering, processing, etc.")
    state: str = Field(description="Two-letter state code")
    county: str
    operator: str
    description: Optional[str] = None
    is_major_source: bool = False
    title_v_applicable: bool = False


class FacilityResponse(BaseModel):
    """Facility response."""
    facility_id: str
    name: str
    facility_type: str
    state: str
    county: str
    operator: str
    description: Optional[str] = None
    is_major_source: bool = False
    title_v_applicable: bool = False
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Compliance Analysis Schemas
# ============================================================================

class ComplianceAnalysisRequest(BaseModel):
    """Request to run compliance analysis."""
    facility_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific facilities to analyze. If empty, analyzes all."
    )
    lookback_days: Optional[int] = Field(
        default=30,
        description="Days to look back for regulatory changes"
    )
    report_types: Optional[List[str]] = Field(
        default=["gap_analysis"],
        description="Types of reports to generate"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "facility_ids": ["permian-001", "bakken-001"],
                "lookback_days": 30,
                "report_types": ["gap_analysis", "executive_summary"]
            }
        }


class ComplianceAnalysisResponse(BaseModel):
    """Response from compliance analysis."""
    analysis_id: str
    status: str
    facilities_analyzed: int
    regulations_found: int
    gaps_identified: int
    phases: Dict[str, Any]
    reports_generated: List[Dict[str, Any]]
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None


# ============================================================================
# Gap Analysis Schemas
# ============================================================================

class GapResponse(BaseModel):
    """Individual compliance gap."""
    id: str
    facility_id: str
    title: str
    description: str
    severity: str
    status: str
    regulation_id: Optional[str] = None
    risk_score: Optional[float] = None
    recommended_action: Optional[str] = None
    estimated_cost: Optional[float] = None
    regulatory_deadline: Optional[str] = None
    identified_at: str


class GapAnalysisResponse(BaseModel):
    """Gap analysis results."""
    gaps: List[Dict[str, Any]]
    summary: Dict[str, int]
    total_remediation_cost: float


# ============================================================================
# Report Schemas
# ============================================================================

class ReportRequest(BaseModel):
    """Request to generate a report."""
    report_type: str = Field(
        description="gap_analysis, executive_summary, regulatory_briefing, annual_certification"
    )
    facility_ids: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "gap_analysis",
                "facility_ids": ["permian-001"]
            }
        }


class ReportResponse(BaseModel):
    """Report generation response."""
    report_id: Optional[str] = None
    report_type: str
    title: str
    file_path: Optional[str] = None
    compliance_score: Optional[float] = None
    generated_at: str


# ============================================================================
# Regulation Schemas
# ============================================================================

class RegulationResponse(BaseModel):
    """Regulation response."""
    id: Optional[str] = None
    regulation_id: Optional[str] = None
    title: str
    citation: str
    regulation_type: str
    status: Optional[str] = None
    description: Optional[str] = None
    effective_date: Optional[str] = None
    compliance_deadline: Optional[str] = None
    applicable_facility_types: Optional[List[str]] = None
    key_requirements: Optional[List[str]] = None


# ============================================================================
# Dashboard Schemas
# ============================================================================

class DashboardResponse(BaseModel):
    """Dashboard summary response."""
    compliance_score: float
    facilities_count: int
    regulations_count: int
    gaps_summary: Dict[str, int]
    alerts_count: int
    recent_alerts: List[Dict[str, Any]]
    last_analysis: Optional[str] = None


# ============================================================================
# Monitoring Schemas
# ============================================================================

class RegulatoryAlert(BaseModel):
    """Regulatory alert."""
    type: str
    regulation: str
    message: str
    deadline: Optional[str] = None
    days_until: Optional[int] = None
    severity: str = "info"


class MonitoringScanResponse(BaseModel):
    """Response from regulatory scan."""
    status: str
    new_regulations: int
    amended_regulations: int
    alerts: List[RegulatoryAlert]
    upcoming_deadlines: List[Dict[str, Any]]
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
