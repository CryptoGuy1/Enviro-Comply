"""
EnviroComply Core
=================
Core configuration, models, and utilities.
"""

from .config import settings, get_settings
from .models import (
    Regulation,
    RegulatoryChange,
    RegulationType,
    RegulatoryStatus,
    Facility,
    FacilityType,
    EmissionSource,
    EmissionSourceType,
    Permit,
    ComplianceGap,
    ComplianceScore,
    ComplianceRequirement,
    ComplianceReport,
    ReportType,
    GapSeverity,
    GapStatus,
    AgentDecision,
    AgentTask,
)
from .exceptions import (
    EnviroComplyError,
    ConfigurationError,
    DataError,
    AgentError,
    ComplianceError,
)

__all__ = [
    # Config
    "settings",
    "get_settings",
    # Models
    "Regulation",
    "RegulatoryChange",
    "RegulationType",
    "RegulatoryStatus",
    "Facility",
    "FacilityType",
    "EmissionSource",
    "EmissionSourceType",
    "Permit",
    "ComplianceGap",
    "ComplianceScore",
    "ComplianceRequirement",
    "ComplianceReport",
    "ReportType",
    "GapSeverity",
    "GapStatus",
    "AgentDecision",
    "AgentTask",
    # Exceptions
    "EnviroComplyError",
    "ConfigurationError",
    "DataError",
    "AgentError",
    "ComplianceError",
]
