"""
Agent Tests
===========
Unit tests for EnviroComply agents.
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from core.models import (
    Regulation, Facility, ComplianceGap,
    RegulationType, RegulatoryStatus, FacilityType, GapSeverity
)
from core.config import settings


class TestModels:
    """Test data models."""
    
    def test_regulation_model(self):
        """Test Regulation model creation."""
        reg = Regulation(
            title="Test Regulation",
            description="A test regulation",
            citation="40 CFR 60.1",
            regulation_type=RegulationType.NSPS,
            status=RegulatoryStatus.EFFECTIVE,
        )
        
        assert reg.title == "Test Regulation"
        assert reg.regulation_type == RegulationType.NSPS
        assert reg.status == RegulatoryStatus.EFFECTIVE
        assert reg.id is not None
    
    def test_facility_model(self):
        """Test Facility model creation."""
        facility = Facility(
            name="Test Facility",
            facility_type=FacilityType.PRODUCTION,
            county="Test County",
            state="TX",
            operator="Test Operator",
        )
        
        assert facility.name == "Test Facility"
        assert facility.facility_type == FacilityType.PRODUCTION
        assert facility.state == "TX"
        assert facility.id is not None
    
    def test_compliance_gap_model(self):
        """Test ComplianceGap model creation."""
        gap = ComplianceGap(
            facility_id="test-facility",
            regulation_id="test-regulation",
            title="Test Gap",
            description="A test compliance gap",
            severity=GapSeverity.HIGH,
            recommended_action="Fix the issue",
            risk_score=0.75,
        )
        
        assert gap.title == "Test Gap"
        assert gap.severity == GapSeverity.HIGH
        assert gap.risk_score == 0.75
        assert gap.identified_at is not None


class TestConfig:
    """Test configuration."""
    
    def test_settings_load(self):
        """Test that settings load correctly."""
        assert settings.app_name == "EnviroComply"
        assert settings.llm is not None
        assert settings.weaviate is not None
    
    def test_epa_settings(self):
        """Test EPA settings."""
        assert settings.epa.check_interval_hours > 0
        assert settings.epa.lookback_days > 0
        assert len(settings.epa.monitored_cfr_parts) > 0
    
    def test_agent_settings(self):
        """Test agent settings."""
        assert settings.agent.max_iterations > 0
        assert 0 <= settings.agent.critical_risk_threshold <= 1
        assert settings.agent.critical_deadline_days > 0


class TestDataLoaders:
    """Test data loading utilities."""
    
    def test_load_sample_facilities(self):
        """Test loading sample facilities."""
        from data.loaders import load_sample_facilities
        
        facilities = load_sample_facilities()
        assert isinstance(facilities, list)
        assert len(facilities) > 0
        
        # Check structure
        facility = facilities[0]
        assert "facility_id" in facility
        assert "name" in facility
        assert "facility_type" in facility
    
    def test_load_sample_regulations(self):
        """Test loading sample regulations."""
        from data.loaders import load_sample_regulations
        
        regulations = load_sample_regulations()
        assert isinstance(regulations, list)
        assert len(regulations) > 0
        
        # Check structure
        reg = regulations[0]
        assert "citation" in reg
        assert "title" in reg


class TestAgentContext:
    """Test agent context."""
    
    def test_context_creation(self):
        """Test AgentContext creation."""
        from agents.base_agent import AgentContext
        
        context = AgentContext()
        assert context.regulations == []
        assert context.facilities == []
        assert context.gaps == []
    
    def test_context_add_items(self):
        """Test adding items to context."""
        from agents.base_agent import AgentContext
        
        context = AgentContext()
        
        context.add_regulation({"id": "reg-1", "title": "Test"})
        assert len(context.regulations) == 1
        
        context.add_facility({"id": "fac-1", "name": "Test"})
        assert len(context.facilities) == 1
        
        context.add_gap({"id": "gap-1", "severity": "high"})
        assert len(context.gaps) == 1
    
    def test_context_summary(self):
        """Test context summary."""
        from agents.base_agent import AgentContext
        
        context = AgentContext()
        context.add_regulation({"id": "reg-1"})
        context.add_facility({"id": "fac-1"})
        context.add_gap({"id": "gap-1", "severity": "critical"})
        
        summary = context.get_summary()
        assert summary["regulations_count"] == 1
        assert summary["facilities_count"] == 1
        assert summary["gaps_count"] == 1
        assert summary["critical_gaps"] == 1


@pytest.mark.asyncio
class TestGapAnalyzer:
    """Test GapAnalyzerAgent."""
    
    async def test_risk_score_calculation(self):
        """Test risk score calculation."""
        from agents.gap_analyzer import GapAnalyzerAgent
        
        agent = GapAnalyzerAgent()
        
        # Test critical gap
        critical_gap = {"severity": "critical"}
        score = agent._calculate_risk_score(critical_gap)
        assert score >= 0.9
        
        # Test low gap
        low_gap = {"severity": "low"}
        score = agent._calculate_risk_score(low_gap)
        assert score <= 0.3


@pytest.mark.asyncio 
class TestRegulationMonitor:
    """Test RegulationMonitorAgent."""
    
    async def test_agent_properties(self):
        """Test agent properties."""
        from agents.regulation_monitor import RegulationMonitorAgent
        
        agent = RegulationMonitorAgent()
        
        assert agent.agent_type == "regulation_monitor"
        assert "EPA" in agent.system_prompt
        assert agent.agent_id is not None


@pytest.mark.asyncio
class TestImpactAssessor:
    """Test ImpactAssessorAgent."""
    
    async def test_agent_properties(self):
        """Test agent properties."""
        from agents.impact_assessor import ImpactAssessorAgent
        
        agent = ImpactAssessorAgent()
        
        assert agent.agent_type == "impact_assessor"
        assert agent.agent_id is not None


@pytest.mark.asyncio
class TestReportGenerator:
    """Test ReportGeneratorAgent."""
    
    async def test_agent_properties(self):
        """Test agent properties."""
        from agents.report_generator import ReportGeneratorAgent
        
        agent = ReportGeneratorAgent()
        
        assert agent.agent_type == "report_generator"
        assert agent.agent_id is not None


class TestAPISchemas:
    """Test API schemas."""
    
    def test_health_response(self):
        """Test HealthResponse schema."""
        from api.schemas import HealthResponse
        
        response = HealthResponse(
            status="healthy",
            service="EnviroComply",
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )
        
        assert response.status == "healthy"
        assert response.service == "EnviroComply"
    
    def test_facility_create(self):
        """Test FacilityCreate schema."""
        from api.schemas import FacilityCreate
        
        facility = FacilityCreate(
            name="Test Facility",
            facility_type="production",
            state="TX",
            county="Test County",
            operator="Test Operator",
        )
        
        assert facility.name == "Test Facility"
        assert facility.state == "TX"
    
    def test_compliance_analysis_request(self):
        """Test ComplianceAnalysisRequest schema."""
        from api.schemas import ComplianceAnalysisRequest
        
        request = ComplianceAnalysisRequest(
            facility_ids=["fac-1", "fac-2"],
            lookback_days=30,
            report_types=["gap_analysis"],
        )
        
        assert len(request.facility_ids) == 2
        assert request.lookback_days == 30
