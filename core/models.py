"""
EnviroComply Data Models
========================
Pydantic models for regulations, facilities, compliance records, and agent outputs.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4


# ============================================================================
# Enums
# ============================================================================

class RegulationType(str, Enum):
    """Type of environmental regulation."""
    NSPS = "nsps"                    # New Source Performance Standards
    NESHAP = "neshap"                # National Emission Standards for HAPs
    GHG_REPORTING = "ghg_reporting"  # Greenhouse Gas Reporting
    SIP = "sip"                      # State Implementation Plan
    TITLE_V = "title_v"              # Title V Operating Permits
    STATE = "state"                  # State-specific regulation
    GUIDANCE = "guidance"            # EPA Guidance documents
    OTHER = "other"


class RegulatoryStatus(str, Enum):
    """Status of a regulation."""
    PROPOSED = "proposed"
    FINAL = "final"
    EFFECTIVE = "effective"
    AMENDED = "amended"
    WITHDRAWN = "withdrawn"


class FacilityType(str, Enum):
    """Type of Oil & Gas facility."""
    PRODUCTION = "production"            # Wellsite, tank batteries
    GATHERING = "gathering"              # Gathering lines, compressor stations
    PROCESSING = "processing"            # Gas processing plants
    TRANSMISSION = "transmission"        # Pipelines, compressor stations
    STORAGE = "storage"                  # Storage terminals
    REFINERY = "refinery"                # Refineries
    DISTRIBUTION = "distribution"        # Distribution facilities


class EmissionSourceType(str, Enum):
    """Type of emission source."""
    COMBUSTION = "combustion"            # Engines, heaters, flares
    FUGITIVE = "fugitive"                # Leaks, seals, connectors
    VENTING = "venting"                  # Intentional venting
    STORAGE = "storage"                  # Tank emissions
    LOADING = "loading"                  # Loading/unloading operations
    PROCESS = "process"                  # Process vents


class GapSeverity(str, Enum):
    """Severity level of compliance gap."""
    CRITICAL = "critical"    # Immediate violation risk
    HIGH = "high"            # Non-compliance within 90 days
    MEDIUM = "medium"        # Best practice gaps
    LOW = "low"              # Optimization opportunities


class GapStatus(str, Enum):
    """Status of a compliance gap."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    CLOSED = "closed"
    DEFERRED = "deferred"


class ReportType(str, Enum):
    """Type of compliance report."""
    ANNUAL_CERTIFICATION = "annual_certification"
    EMISSIONS_INVENTORY = "emissions_inventory"
    DEVIATION_REPORT = "deviation_report"
    GAP_ANALYSIS = "gap_analysis"
    EXECUTIVE_SUMMARY = "executive_summary"
    REGULATORY_BRIEFING = "regulatory_briefing"
    AUDIT_RESPONSE = "audit_response"


# ============================================================================
# Regulation Models
# ============================================================================

class RegulationReference(BaseModel):
    """Reference to a specific regulation section."""
    cfr_title: int = Field(description="CFR Title (e.g., 40)")
    cfr_part: int = Field(description="CFR Part (e.g., 60)")
    subpart: Optional[str] = Field(default=None, description="Subpart (e.g., OOOOa)")
    section: Optional[str] = Field(default=None, description="Section number")
    paragraph: Optional[str] = Field(default=None, description="Paragraph reference")
    
    @property
    def citation(self) -> str:
        """Generate standard CFR citation."""
        cite = f"{self.cfr_title} CFR {self.cfr_part}"
        if self.subpart:
            cite += f" Subpart {self.subpart}"
        if self.section:
            cite += f".{self.section}"
        if self.paragraph:
            cite += f"({self.paragraph})"
        return cite


class Regulation(BaseModel):
    """Environmental regulation record."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Basic information
    title: str = Field(description="Regulation title")
    description: str = Field(description="Plain-language description")
    regulation_type: RegulationType
    status: RegulatoryStatus
    
    # Citations
    citation: str = Field(description="Primary CFR citation")
    references: List[RegulationReference] = Field(default_factory=list)
    federal_register_citation: Optional[str] = Field(default=None)
    
    # Dates
    publication_date: Optional[date] = None
    effective_date: Optional[date] = None
    compliance_deadline: Optional[date] = None
    
    # Applicability
    applicable_facility_types: List[FacilityType] = Field(default_factory=list)
    applicable_emission_sources: List[EmissionSourceType] = Field(default_factory=list)
    applicability_thresholds: Dict[str, Any] = Field(default_factory=dict)
    
    # Content
    key_requirements: List[str] = Field(default_factory=list)
    monitoring_requirements: List[str] = Field(default_factory=list)
    recordkeeping_requirements: List[str] = Field(default_factory=list)
    reporting_requirements: List[str] = Field(default_factory=list)
    
    # Metadata
    source_url: Optional[str] = None
    full_text: Optional[str] = None
    summary: Optional[str] = None
    
    # Oil & Gas specific
    applies_to_oil_gas: bool = True
    sector_segments: List[str] = Field(default_factory=list)  # upstream, midstream, downstream
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None


class RegulatoryChange(BaseModel):
    """Record of a regulatory change or update."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    regulation_id: str
    
    change_type: str = Field(description="Type: new, amendment, correction, withdrawal")
    change_date: date
    
    summary: str = Field(description="Summary of changes")
    impact_assessment: Optional[str] = Field(default=None)
    
    previous_text: Optional[str] = None
    new_text: Optional[str] = None
    
    federal_register_doc: Optional[str] = None
    source_url: Optional[str] = None
    
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


# ============================================================================
# Facility Models
# ============================================================================

class GeoLocation(BaseModel):
    """Geographic location."""
    latitude: float
    longitude: float
    elevation_ft: Optional[float] = None


class EmissionSource(BaseModel):
    """Individual emission source within a facility."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    source_type: EmissionSourceType
    description: Optional[str] = None
    
    # Equipment details
    equipment_type: str  # e.g., "compressor", "storage tank", "flare"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity: Optional[str] = None
    installation_date: Optional[date] = None
    
    # Emissions
    potential_emissions_tpy: Dict[str, float] = Field(default_factory=dict)  # pollutant -> tons/year
    controlled: bool = False
    control_equipment: Optional[str] = None
    control_efficiency: Optional[float] = None
    
    # Regulatory
    permit_conditions: List[str] = Field(default_factory=list)
    applicable_regulations: List[str] = Field(default_factory=list)
    
    # Monitoring
    monitoring_method: Optional[str] = None
    last_inspection: Optional[date] = None
    next_inspection_due: Optional[date] = None


class Permit(BaseModel):
    """Environmental permit."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    permit_number: str
    permit_type: str  # Title V, PBR, NSR, etc.
    
    issuing_agency: str
    issue_date: date
    expiration_date: Optional[date] = None
    
    status: str = "active"  # active, expired, pending_renewal
    
    conditions: List[str] = Field(default_factory=list)
    emission_limits: Dict[str, Any] = Field(default_factory=dict)
    
    document_url: Optional[str] = None


class Facility(BaseModel):
    """Oil & Gas facility profile."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Basic information
    name: str
    facility_type: FacilityType
    description: Optional[str] = None
    
    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    county: str
    state: str
    zip_code: Optional[str] = None
    location: Optional[GeoLocation] = None
    
    # Regulatory IDs
    epa_id: Optional[str] = None
    state_id: Optional[str] = None
    frs_id: Optional[str] = None  # EPA Facility Registry Service
    
    # Classification
    sic_code: Optional[str] = None
    naics_code: Optional[str] = None
    
    # Operations
    operator: str
    start_date: Optional[date] = None
    operational_status: str = "active"  # active, inactive, shut_in, decommissioned
    
    # Emission sources
    emission_sources: List[EmissionSource] = Field(default_factory=list)
    
    # Permits
    permits: List[Permit] = Field(default_factory=list)
    
    # Emissions summary
    total_potential_emissions_tpy: Dict[str, float] = Field(default_factory=dict)
    is_major_source: bool = False
    title_v_applicable: bool = False
    
    # Compliance history
    inspection_history: List[Dict[str, Any]] = Field(default_factory=list)
    violation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_compliance_review: Optional[datetime] = None


# ============================================================================
# Compliance Models
# ============================================================================

class ComplianceRequirement(BaseModel):
    """Specific compliance requirement mapped to a facility."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    regulation_id: str
    facility_id: str
    emission_source_id: Optional[str] = None
    
    requirement_text: str
    requirement_type: str  # monitoring, recordkeeping, reporting, operational
    
    frequency: Optional[str] = None  # daily, weekly, monthly, quarterly, annual
    deadline: Optional[date] = None
    
    is_applicable: bool = True
    applicability_notes: Optional[str] = None
    
    current_status: str = "pending"  # compliant, non_compliant, pending, not_applicable


class ComplianceGap(BaseModel):
    """Identified compliance gap."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    facility_id: str
    regulation_id: str
    requirement_id: Optional[str] = None
    emission_source_id: Optional[str] = None
    
    # Gap details
    title: str
    description: str
    severity: GapSeverity
    status: GapStatus = GapStatus.OPEN
    
    # Risk assessment
    risk_score: float = Field(ge=0, le=1, description="0-1 risk score")
    potential_fine: Optional[float] = None
    enforcement_likelihood: Optional[float] = None
    
    # Deadlines
    regulatory_deadline: Optional[date] = None
    internal_deadline: Optional[date] = None
    days_until_deadline: Optional[int] = None
    
    # Remediation
    recommended_action: str
    estimated_cost: Optional[float] = None
    estimated_effort_hours: Optional[float] = None
    responsible_party: Optional[str] = None
    
    # Evidence
    evidence: List[str] = Field(default_factory=list)
    supporting_documents: List[str] = Field(default_factory=list)
    
    # Resolution
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # Tracking
    identified_at: datetime = Field(default_factory=datetime.utcnow)
    identified_by: str = "gap_analyzer_agent"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ComplianceScore(BaseModel):
    """Overall compliance score for a facility."""
    
    facility_id: str
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    
    overall_score: float = Field(ge=0, le=100)
    
    # Breakdown by category
    category_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Gap counts
    critical_gaps: int = 0
    high_gaps: int = 0
    medium_gaps: int = 0
    low_gaps: int = 0
    
    # Trend
    score_change_30d: Optional[float] = None
    score_change_90d: Optional[float] = None
    
    # Details
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# Report Models
# ============================================================================

class ReportSection(BaseModel):
    """Section within a compliance report."""
    
    title: str
    content: str
    order: int = 0
    include_in_toc: bool = True


class ComplianceReport(BaseModel):
    """Generated compliance report."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    report_type: ReportType
    title: str
    
    facility_id: Optional[str] = None
    facility_ids: List[str] = Field(default_factory=list)  # For multi-facility reports
    
    # Content
    executive_summary: str
    sections: List[ReportSection] = Field(default_factory=list)
    
    # Data
    compliance_score: Optional[ComplianceScore] = None
    gaps_included: List[str] = Field(default_factory=list)  # Gap IDs
    regulations_covered: List[str] = Field(default_factory=list)  # Regulation IDs
    
    # Metadata
    reporting_period_start: Optional[date] = None
    reporting_period_end: Optional[date] = None
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = "report_generator_agent"
    
    # Output
    format: str = "pdf"  # pdf, docx, html
    file_path: Optional[str] = None


# ============================================================================
# Agent Models
# ============================================================================

class AgentDecision(BaseModel):
    """Record of an agent decision."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    agent_id: str
    agent_type: str
    
    decision_type: str
    action_taken: str
    reasoning: str
    
    confidence: float = Field(ge=0, le=1)
    
    # Context
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Related entities
    facility_ids: List[str] = Field(default_factory=list)
    regulation_ids: List[str] = Field(default_factory=list)
    gap_ids: List[str] = Field(default_factory=list)
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: Optional[float] = None
    
    # Status
    success: bool = True
    error_message: Optional[str] = None


class AgentTask(BaseModel):
    """Task assigned to an agent."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    task_type: str
    description: str
    priority: int = Field(default=5, ge=1, le=10)
    
    assigned_agent: str
    
    # Parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    status: str = "pending"  # pending, running, completed, failed
    progress: float = Field(default=0, ge=0, le=100)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
