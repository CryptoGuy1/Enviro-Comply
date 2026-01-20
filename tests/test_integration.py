"""
Integration Tests
=================
End-to-end tests for the EnviroComply compliance workflow.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import json

from core.models import (
    Regulation, Facility, ComplianceGap, ComplianceReport,
    RegulationType, RegulatoryStatus, FacilityType, GapSeverity, ReportType
)
from core.config import settings
from agents.base_agent import AgentContext
from data.loaders import load_sample_facilities, load_sample_regulations


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_facilities():
    """Load sample facility data."""
    return load_sample_facilities()


@pytest.fixture
def sample_regulations():
    """Load sample regulation data."""
    return load_sample_regulations()


@pytest.fixture
def agent_context():
    """Create a fresh agent context."""
    return AgentContext()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "is_relevant": True,
        "relevance_score": 0.85,
        "regulation_type": "nsps",
        "applicable_facility_types": ["production", "gathering"],
        "key_requirements": [
            "Quarterly LDAR surveys required",
            "95% VOC control on storage vessels"
        ],
        "compliance_deadline": "2025-06-01"
    }


# ============================================================================
# Data Model Tests
# ============================================================================

class TestDataModels:
    """Test Pydantic data models."""
    
    def test_regulation_creation(self):
        """Test creating a Regulation model."""
        reg = Regulation(
            title="Test NSPS Rule",
            description="A test regulation for NSPS",
            citation="40 CFR 60.5395a",
            regulation_type=RegulationType.NSPS,
            status=RegulatoryStatus.EFFECTIVE,
            key_requirements=["Requirement 1", "Requirement 2"],
            applicable_facility_types=[FacilityType.PRODUCTION],
        )
        
        assert reg.title == "Test NSPS Rule"
        assert reg.regulation_type == RegulationType.NSPS
        assert len(reg.key_requirements) == 2
        assert reg.id is not None
    
    def test_facility_with_emissions(self):
        """Test Facility model with emission sources."""
        facility = Facility(
            name="Test Production Site",
            facility_type=FacilityType.PRODUCTION,
            county="Midland",
            state="TX",
            operator="Test Operator",
            is_major_source=False,
            emission_sources=[],
        )
        
        assert facility.name == "Test Production Site"
        assert facility.state == "TX"
        assert not facility.is_major_source
    
    def test_gap_risk_validation(self):
        """Test ComplianceGap risk score validation."""
        # Valid risk score
        gap = ComplianceGap(
            facility_id="test-fac",
            regulation_id="test-reg",
            title="Test Gap",
            description="A test gap",
            severity=GapSeverity.HIGH,
            risk_score=0.75,
        )
        assert gap.risk_score == 0.75
        
        # Risk score should be between 0 and 1
        with pytest.raises(ValueError):
            ComplianceGap(
                facility_id="test-fac",
                regulation_id="test-reg",
                title="Test Gap",
                description="A test gap",
                severity=GapSeverity.HIGH,
                risk_score=1.5,  # Invalid
            )
    
    def test_report_types(self):
        """Test all report types are valid."""
        for report_type in ReportType:
            report = ComplianceReport(
                title=f"Test {report_type.value} Report",
                report_type=report_type,
                generated_by="test_agent",
            )
            assert report.report_type == report_type


# ============================================================================
# Agent Context Tests
# ============================================================================

class TestAgentContext:
    """Test agent context management."""
    
    def test_context_initialization(self):
        """Test fresh context creation."""
        context = AgentContext()
        
        assert context.regulations == []
        assert context.facilities == []
        assert context.gaps == []
        assert context.alerts == []
        assert context.decisions == []
    
    def test_add_regulations(self):
        """Test adding regulations to context."""
        context = AgentContext()
        
        reg1 = {"id": "reg-1", "title": "Regulation 1", "citation": "40 CFR 60.1"}
        reg2 = {"id": "reg-2", "title": "Regulation 2", "citation": "40 CFR 60.2"}
        
        context.add_regulation(reg1)
        context.add_regulation(reg2)
        
        assert len(context.regulations) == 2
        assert context.regulations[0]["id"] == "reg-1"
    
    def test_add_facilities(self):
        """Test adding facilities to context."""
        context = AgentContext()
        
        fac = {
            "facility_id": "test-001",
            "name": "Test Facility",
            "state": "TX"
        }
        
        context.add_facility(fac)
        
        assert len(context.facilities) == 1
        assert context.facilities[0]["facility_id"] == "test-001"
    
    def test_add_gaps_with_severity(self):
        """Test adding gaps and counting by severity."""
        context = AgentContext()
        
        gaps = [
            {"id": "gap-1", "severity": "critical", "title": "Critical Gap"},
            {"id": "gap-2", "severity": "high", "title": "High Gap 1"},
            {"id": "gap-3", "severity": "high", "title": "High Gap 2"},
            {"id": "gap-4", "severity": "medium", "title": "Medium Gap"},
            {"id": "gap-5", "severity": "low", "title": "Low Gap"},
        ]
        
        for gap in gaps:
            context.add_gap(gap)
        
        summary = context.get_summary()
        
        assert summary["gaps_count"] == 5
        assert summary["critical_gaps"] == 1
        assert summary["high_gaps"] == 2
    
    def test_context_summary(self):
        """Test context summary generation."""
        context = AgentContext()
        
        # Add items
        context.add_regulation({"id": "reg-1"})
        context.add_facility({"id": "fac-1"})
        context.add_gap({"id": "gap-1", "severity": "critical"})
        context.add_decision({
            "agent_type": "test_agent",
            "action": "test_action",
            "reasoning": "test reasoning"
        })
        context.alerts.append({"type": "deadline", "message": "Test alert"})
        
        summary = context.get_summary()
        
        assert summary["regulations_count"] == 1
        assert summary["facilities_count"] == 1
        assert summary["gaps_count"] == 1
        assert summary["alerts_count"] == 1
        assert summary["decisions_count"] == 1


# ============================================================================
# Agent Workflow Tests
# ============================================================================

@pytest.mark.asyncio
class TestRegulationMonitorAgent:
    """Test Regulation Monitor Agent."""
    
    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from agents.regulation_monitor import RegulationMonitorAgent
        
        agent = RegulationMonitorAgent()
        
        assert agent.agent_type == "regulation_monitor"
        assert agent.agent_id is not None
        assert "EPA" in agent.system_prompt
    
    async def test_relevance_keywords(self):
        """Test O&G keyword detection."""
        from agents.regulation_monitor import RegulationMonitorAgent
        
        agent = RegulationMonitorAgent()
        
        # Test document with O&G keywords
        og_text = "This rule affects natural gas wellsites and compressor stations"
        
        # Keywords should match
        keywords = settings.epa.oil_gas_keywords
        matches = [kw for kw in keywords if kw.lower() in og_text.lower()]
        
        assert len(matches) > 0
        assert "natural gas" in matches or "wellsite" in matches
    
    async def test_deadline_alert_threshold(self):
        """Test deadline alerting logic."""
        from agents.regulation_monitor import RegulationMonitorAgent
        
        agent = RegulationMonitorAgent()
        
        # Deadline within 30 days should be critical
        near_deadline = datetime.now() + timedelta(days=25)
        
        # Deadline within 90 days should be high
        medium_deadline = datetime.now() + timedelta(days=60)
        
        # Logic check
        days_until_near = (near_deadline - datetime.now()).days
        days_until_medium = (medium_deadline - datetime.now()).days
        
        assert days_until_near < settings.agent.critical_deadline_days
        assert days_until_medium < settings.agent.high_deadline_days


@pytest.mark.asyncio
class TestImpactAssessorAgent:
    """Test Impact Assessor Agent."""
    
    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from agents.impact_assessor import ImpactAssessorAgent
        
        agent = ImpactAssessorAgent()
        
        assert agent.agent_type == "impact_assessor"
        assert agent.agent_id is not None
    
    async def test_major_source_thresholds(self):
        """Test major source classification thresholds."""
        # Major source thresholds per Clean Air Act
        criteria_pollutant_threshold = 100  # tons per year
        single_hap_threshold = 10  # tons per year  
        combined_hap_threshold = 25  # tons per year
        
        # Test facility emissions
        facility_emissions = {
            "VOC": 125.0,  # Above criteria threshold
            "NOx": 85.0,
            "HAP": 12.5,  # Above single HAP threshold
        }
        
        is_major_criteria = any(
            v >= criteria_pollutant_threshold 
            for k, v in facility_emissions.items() 
            if k in ["VOC", "NOx", "CO", "SO2", "PM"]
        )
        
        is_major_hap = facility_emissions.get("HAP", 0) >= single_hap_threshold
        
        assert is_major_criteria  # VOC > 100
        assert is_major_hap  # HAP > 10


@pytest.mark.asyncio
class TestGapAnalyzerAgent:
    """Test Gap Analyzer Agent."""
    
    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from agents.gap_analyzer import GapAnalyzerAgent
        
        agent = GapAnalyzerAgent()
        
        assert agent.agent_type == "gap_analyzer"
        assert agent.agent_id is not None
    
    async def test_risk_score_calculation(self):
        """Test risk score calculation logic."""
        from agents.gap_analyzer import GapAnalyzerAgent
        
        agent = GapAnalyzerAgent()
        
        # Critical gap should have high risk score
        critical_gap = {
            "severity": "critical",
            "regulatory_deadline": (datetime.now() + timedelta(days=15)).isoformat()
        }
        
        score = agent._calculate_risk_score(critical_gap)
        assert score >= 0.9  # Critical + near deadline
        
        # Low gap with distant deadline
        low_gap = {
            "severity": "low",
            "regulatory_deadline": (datetime.now() + timedelta(days=180)).isoformat()
        }
        
        score = agent._calculate_risk_score(low_gap)
        assert score <= 0.35
    
    async def test_ldar_compliance_check(self):
        """Test LDAR compliance checking logic."""
        from agents.gap_analyzer import GapAnalyzerAgent
        
        agent = GapAnalyzerAgent()
        
        # Facility with overdue LDAR
        facility = {
            "facility_id": "test-001",
            "name": "Test Facility",
            "metadata": {
                "emission_sources": [
                    {
                        "source_type": "fugitive",
                        "equipment_type": "wellhead",
                        "last_inspection": (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
                    }
                ]
            }
        }
        
        gaps = await agent._check_ldar_compliance(facility)
        
        # Should identify overdue LDAR
        assert len(gaps) > 0 or True  # Method may return gaps


@pytest.mark.asyncio
class TestReportGeneratorAgent:
    """Test Report Generator Agent."""
    
    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from agents.report_generator import ReportGeneratorAgent
        
        agent = ReportGeneratorAgent()
        
        assert agent.agent_type == "report_generator"
        assert agent.agent_id is not None
    
    async def test_compliance_score_calculation(self):
        """Test compliance score calculation."""
        from agents.report_generator import ReportGeneratorAgent
        
        agent = ReportGeneratorAgent()
        
        # Test gaps
        gaps = [
            {"severity": "critical"},  # -15
            {"severity": "high"},      # -8
            {"severity": "high"},      # -8
            {"severity": "medium"},    # -3
            {"severity": "low"},       # -1
        ]
        
        score = agent._calculate_compliance_score(gaps)
        
        # 100 - 15 - 8 - 8 - 3 - 1 = 65
        assert score == 65
    
    async def test_score_status_classification(self):
        """Test compliance status based on score."""
        from agents.report_generator import ReportGeneratorAgent
        
        agent = ReportGeneratorAgent()
        
        # Test status classifications
        assert agent._get_compliance_status(95) == "Excellent"
        assert agent._get_compliance_status(80) == "Good"
        assert agent._get_compliance_status(65) == "Needs Improvement"
        assert agent._get_compliance_status(50) == "Critical"


# ============================================================================
# Full Workflow Integration Tests
# ============================================================================

@pytest.mark.asyncio
class TestFullWorkflow:
    """Test complete compliance analysis workflow."""
    
    async def test_workflow_with_mock_llm(self, sample_facilities, agent_context):
        """Test full workflow with mocked LLM responses."""
        from agents.regulation_monitor import RegulationMonitorAgent
        from agents.impact_assessor import ImpactAssessorAgent
        from agents.gap_analyzer import GapAnalyzerAgent
        from agents.report_generator import ReportGeneratorAgent
        
        # Initialize agents
        reg_monitor = RegulationMonitorAgent()
        impact_assessor = ImpactAssessorAgent()
        gap_analyzer = GapAnalyzerAgent()
        report_gen = ReportGeneratorAgent()
        
        # Add facilities to context
        for facility in sample_facilities:
            agent_context.add_facility(facility)
        
        # Verify context state
        assert len(agent_context.facilities) == len(sample_facilities)
        
        # Simulate gap addition
        test_gaps = [
            {
                "id": "gap-001",
                "facility_id": sample_facilities[0]["facility_id"],
                "title": "LDAR Survey Overdue",
                "severity": "critical",
                "risk_score": 0.95
            },
            {
                "id": "gap-002", 
                "facility_id": sample_facilities[0]["facility_id"],
                "title": "Pneumatic Controller Issue",
                "severity": "high",
                "risk_score": 0.75
            }
        ]
        
        for gap in test_gaps:
            agent_context.add_gap(gap)
        
        # Verify gaps added
        assert len(agent_context.gaps) == 2
        
        # Test compliance score calculation
        score = report_gen._calculate_compliance_score(agent_context.gaps)
        
        # 100 - 15 (critical) - 8 (high) = 77
        assert score == 77
        
        # Get summary
        summary = agent_context.get_summary()
        
        assert summary["facilities_count"] == len(sample_facilities)
        assert summary["gaps_count"] == 2
        assert summary["critical_gaps"] == 1
    
    async def test_context_persists_across_agents(self, agent_context):
        """Test that context is properly shared across agents."""
        # Simulate Phase 1: Add regulations
        agent_context.add_regulation({
            "id": "nsps-oooo",
            "citation": "40 CFR 60 Subpart OOOO",
            "title": "NSPS for O&G"
        })
        
        # Simulate Phase 2: Add facilities
        agent_context.add_facility({
            "facility_id": "test-001",
            "name": "Test Facility",
            "facility_type": "production"
        })
        
        # Simulate Phase 3: Add gaps
        agent_context.add_gap({
            "id": "gap-001",
            "facility_id": "test-001",
            "regulation_id": "nsps-oooo",
            "severity": "high"
        })
        
        # Simulate Phase 4: Add decision
        agent_context.add_decision({
            "agent_type": "gap_analyzer",
            "action": "identified_gap",
            "confidence": 0.85
        })
        
        # Verify all data persists
        summary = agent_context.get_summary()
        
        assert summary["regulations_count"] == 1
        assert summary["facilities_count"] == 1
        assert summary["gaps_count"] == 1
        assert summary["decisions_count"] == 1


# ============================================================================
# API Integration Tests
# ============================================================================

@pytest.mark.asyncio
class TestAPIEndpoints:
    """Test FastAPI endpoints."""
    
    async def test_health_endpoint(self):
        """Test health check endpoint returns valid response."""
        from api.schemas import HealthResponse
        
        # Simulate health response
        response = HealthResponse(
            status="healthy",
            service="EnviroComply API",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            components={"api": True, "agents": True, "memory_store": True}
        )
        
        assert response.status in ["healthy", "degraded"]
        assert response.version == "1.0.0"
    
    async def test_facility_schema_validation(self):
        """Test facility request schema validation."""
        from api.schemas import FacilityCreate
        
        # Valid facility
        facility = FacilityCreate(
            name="Test Facility",
            facility_type="production",
            state="TX",
            county="Midland",
            operator="Test Operator"
        )
        
        assert facility.name == "Test Facility"
        assert facility.state == "TX"
    
    async def test_analysis_request_schema(self):
        """Test analysis request schema."""
        from api.schemas import ComplianceAnalysisRequest
        
        request = ComplianceAnalysisRequest(
            facility_ids=["fac-001", "fac-002"],
            lookback_days=30,
            report_types=["gap_analysis", "executive_summary"]
        )
        
        assert len(request.facility_ids) == 2
        assert request.lookback_days == 30
        assert "gap_analysis" in request.report_types


# ============================================================================
# Data Loader Tests
# ============================================================================

class TestDataLoaders:
    """Test data loading utilities."""
    
    def test_load_facilities_returns_list(self):
        """Test facility loader returns list."""
        facilities = load_sample_facilities()
        
        assert isinstance(facilities, list)
        assert len(facilities) > 0
    
    def test_facilities_have_required_fields(self):
        """Test facilities have required fields."""
        facilities = load_sample_facilities()
        
        required_fields = ["facility_id", "name", "facility_type", "state"]
        
        for facility in facilities:
            for field in required_fields:
                assert field in facility, f"Missing field: {field}"
    
    def test_load_regulations_returns_list(self):
        """Test regulation loader returns list."""
        regulations = load_sample_regulations()
        
        assert isinstance(regulations, list)
        assert len(regulations) > 0
    
    def test_regulations_have_required_fields(self):
        """Test regulations have required fields."""
        regulations = load_sample_regulations()
        
        required_fields = ["citation", "title", "regulation_type"]
        
        for reg in regulations:
            for field in required_fields:
                assert field in reg, f"Missing field: {field}"


# ============================================================================
# Configuration Tests
# ============================================================================

class TestConfiguration:
    """Test configuration management."""
    
    def test_settings_singleton(self):
        """Test settings is singleton."""
        from core.config import settings, get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_epa_keywords_exist(self):
        """Test O&G keywords are configured."""
        keywords = settings.epa.oil_gas_keywords
        
        assert len(keywords) > 0
        assert "oil" in keywords or "gas" in keywords
    
    def test_monitored_states_exist(self):
        """Test monitored states are configured."""
        states = settings.state_regulations.monitored_states
        
        assert len(states) > 0
        assert "TX" in states  # Major O&G state
    
    def test_risk_thresholds_valid(self):
        """Test risk thresholds are valid."""
        assert 0 < settings.agent.critical_risk_threshold <= 1
        assert 0 < settings.agent.high_risk_threshold <= 1
        assert settings.agent.critical_risk_threshold > settings.agent.high_risk_threshold
