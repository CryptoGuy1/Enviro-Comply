"""
EnviroComply Crew
=================
CrewAI orchestration for multi-agent compliance analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from loguru import logger

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from .base_agent import AgentContext
from .regulation_monitor import RegulationMonitorAgent
from .impact_assessor import ImpactAssessorAgent
from .gap_analyzer import GapAnalyzerAgent
from .report_generator import ReportGeneratorAgent
from core.config import settings
from core.models import ReportType
from memory.weaviate_store import get_weaviate_store


class EnviroComplyCrew:
    """
    Orchestrates the multi-agent compliance analysis workflow.
    
    Workflow:
    1. Regulation Monitor Agent scans for regulatory changes
    2. Impact Assessor Agent maps regulations to facilities
    3. Gap Analyzer Agent identifies compliance gaps
    4. Report Generator Agent produces reports
    """
    
    def __init__(self):
        self.context = AgentContext()
        self.memory_store = None
        
        # Initialize agents
        self.regulation_monitor = None
        self.impact_assessor = None
        self.gap_analyzer = None
        self.report_generator = None
        
        # CrewAI components
        self.crew = None
        self.llm = None
        
    async def initialize(self):
        """Initialize the crew and all agents."""
        logger.info("Initializing EnviroComply Crew...")
        
        # Connect to memory store
        self.memory_store = await get_weaviate_store()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model,
            temperature=settings.llm.openai_temperature,
            api_key=settings.llm.openai_api_key,
        )
        
        # Initialize custom agents
        self.regulation_monitor = RegulationMonitorAgent(memory_store=self.memory_store)
        self.impact_assessor = ImpactAssessorAgent(memory_store=self.memory_store)
        self.gap_analyzer = GapAnalyzerAgent(memory_store=self.memory_store)
        self.report_generator = ReportGeneratorAgent(memory_store=self.memory_store)
        
        # Create CrewAI agents for orchestration
        self._setup_crewai_agents()
        
        logger.info("EnviroComply Crew initialized successfully")
    
    def _setup_crewai_agents(self):
        """Set up CrewAI agent wrappers."""
        
        self.crewai_monitor = Agent(
            role="Regulatory Intelligence Analyst",
            goal="Monitor and analyze EPA and state environmental regulations for Oil & Gas",
            backstory="""You are an expert regulatory analyst with 15 years of experience 
            tracking EPA Clean Air Act regulations. You have deep knowledge of NSPS OOOO/OOOOa/OOOOb, 
            NESHAP standards, and state regulations from major O&G states.""",
            llm=self.llm,
            verbose=settings.agent.verbose,
            allow_delegation=True,
        )
        
        self.crewai_assessor = Agent(
            role="Facility Compliance Engineer",
            goal="Assess regulatory impact on specific Oil & Gas facilities",
            backstory="""You are a licensed environmental engineer specializing in 
            Oil & Gas facility compliance. You've conducted hundreds of applicability 
            determinations and permit reviews for production sites, gathering systems, 
            and gas processing plants.""",
            llm=self.llm,
            verbose=settings.agent.verbose,
            allow_delegation=True,
        )
        
        self.crewai_analyzer = Agent(
            role="Compliance Audit Specialist",
            goal="Identify compliance gaps and recommend corrective actions",
            backstory="""You are a former EPA enforcement officer turned compliance 
            consultant. You know exactly what regulators look for during inspections 
            and have helped dozens of companies avoid violations through proactive 
            gap identification.""",
            llm=self.llm,
            verbose=settings.agent.verbose,
            allow_delegation=True,
        )
        
        self.crewai_reporter = Agent(
            role="Environmental Compliance Writer",
            goal="Produce clear, actionable compliance reports for various audiences",
            backstory="""You are an experienced technical writer who has authored 
            hundreds of compliance reports, Title V certifications, and executive 
            briefings. You know how to communicate complex regulatory requirements 
            to both technical staff and C-suite executives.""",
            llm=self.llm,
            verbose=settings.agent.verbose,
            allow_delegation=False,
        )
    
    async def run_full_analysis(
        self,
        facilities: List[Dict] = None,
        lookback_days: int = 30,
        report_types: List[ReportType] = None,
    ) -> Dict[str, Any]:
        """
        Run complete compliance analysis workflow.
        
        Args:
            facilities: Facilities to analyze (uses stored if not provided)
            lookback_days: Days to look back for regulatory changes
            report_types: Types of reports to generate
            
        Returns:
            Complete analysis results
        """
        start_time = datetime.utcnow()
        logger.info("Starting full compliance analysis...")
        
        results = {
            "analysis_id": f"analysis_{start_time.strftime('%Y%m%d_%H%M%S')}",
            "started_at": start_time.isoformat(),
            "facilities_analyzed": 0,
            "regulations_found": 0,
            "gaps_identified": 0,
            "reports_generated": [],
            "phases": {},
        }
        
        try:
            # Phase 1: Regulatory Monitoring
            logger.info("Phase 1: Scanning for regulatory changes...")
            reg_results = await self.regulation_monitor.run(
                context=self.context,
                lookback_days=lookback_days,
            )
            results["phases"]["regulation_monitoring"] = {
                "new_regulations": len(reg_results.get("new_regulations", [])),
                "amended_regulations": len(reg_results.get("amended_regulations", [])),
                "alerts": len(reg_results.get("alerts", [])),
            }
            results["regulations_found"] = (
                len(reg_results.get("new_regulations", [])) +
                len(reg_results.get("amended_regulations", []))
            )
            
            # Load facilities if not provided
            if not facilities:
                facilities = await self._load_facilities()
            
            # Add facilities to context
            for facility in facilities:
                self.context.add_facility(facility)
            
            results["facilities_analyzed"] = len(facilities)
            
            # Phase 2: Impact Assessment
            logger.info("Phase 2: Assessing regulatory impact on facilities...")
            impact_results = await self.impact_assessor.run(
                context=self.context,
                facilities=facilities,
                regulations=self.context.regulations,
            )
            results["phases"]["impact_assessment"] = {
                "assessments": len(impact_results.get("assessments", [])),
                "high_impact_facilities": len(impact_results.get("high_impact_facilities", [])),
                "total_estimated_cost": impact_results.get("total_estimated_cost", 0),
            }
            
            # Phase 3: Gap Analysis
            logger.info("Phase 3: Identifying compliance gaps...")
            gap_results = await self.gap_analyzer.run(
                context=self.context,
                facilities=facilities,
                impact_assessments=impact_results.get("assessments", []),
            )
            results["phases"]["gap_analysis"] = gap_results.get("gap_summary", {})
            results["gaps_identified"] = gap_results.get("gap_summary", {}).get("total", 0)
            
            # Phase 4: Report Generation
            logger.info("Phase 4: Generating reports...")
            report_types = report_types or [ReportType.GAP_ANALYSIS, ReportType.EXECUTIVE_SUMMARY]
            
            for report_type in report_types:
                report = await self.report_generator.run(
                    context=self.context,
                    report_type=report_type,
                    facilities=facilities,
                    gaps=self.context.gaps,
                )
                results["reports_generated"].append({
                    "type": report_type.value,
                    "file_path": report.get("file_path"),
                    "compliance_score": report.get("compliance_score"),
                })
            
            results["phases"]["report_generation"] = {
                "reports_count": len(results["reports_generated"]),
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            results["error"] = str(e)
        
        # Finalize
        end_time = datetime.utcnow()
        results["completed_at"] = end_time.isoformat()
        results["duration_seconds"] = (end_time - start_time).total_seconds()
        
        logger.info(f"Analysis completed in {results['duration_seconds']:.1f} seconds")
        
        return results
    
    async def run_monitoring_only(
        self,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Run regulatory monitoring without full analysis."""
        logger.info("Running regulatory monitoring...")
        
        return await self.regulation_monitor.run(
            context=self.context,
            lookback_days=lookback_days,
        )
    
    async def run_gap_analysis(
        self,
        facility_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """Run gap analysis for specific facilities."""
        logger.info("Running targeted gap analysis...")
        
        facilities = await self._load_facilities(facility_ids)
        
        # Quick impact assessment
        impact_results = await self.impact_assessor.run(
            context=self.context,
            facilities=facilities,
        )
        
        # Gap analysis
        return await self.gap_analyzer.run(
            context=self.context,
            facilities=facilities,
            impact_assessments=impact_results.get("assessments", []),
        )
    
    async def generate_report(
        self,
        report_type: ReportType,
        facility_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """Generate a specific report type."""
        logger.info(f"Generating {report_type.value} report...")
        
        facilities = await self._load_facilities(facility_ids)
        gaps = self.context.gaps if self.context.gaps else []
        
        return await self.report_generator.run(
            context=self.context,
            report_type=report_type,
            facilities=facilities,
            gaps=gaps,
        )
    
    async def _load_facilities(
        self,
        facility_ids: List[str] = None
    ) -> List[Dict]:
        """Load facilities from memory store."""
        if self.memory_store:
            try:
                all_facilities = await self.memory_store.get_all_facilities()
                
                if facility_ids:
                    return [
                        f for f in all_facilities
                        if f.get("facility_id") in facility_ids
                    ]
                return all_facilities
            except Exception as e:
                logger.warning(f"Failed to load facilities from store: {e}")
        
        # Return sample facilities if store unavailable
        return self._get_sample_facilities()
    
    def _get_sample_facilities(self) -> List[Dict]:
        """Get sample facilities for demonstration."""
        return [
            {
                "facility_id": "permian-001",
                "name": "Permian Basin Production Facility 1",
                "facility_type": "production",
                "state": "TX",
                "county": "Midland",
                "operator": "Demo Oil & Gas Co.",
                "is_major_source": False,
                "title_v_applicable": False,
                "metadata": {
                    "emission_sources": [
                        {
                            "id": "src-001",
                            "name": "Tank Battery 1",
                            "source_type": "storage",
                            "equipment_type": "crude oil storage tank",
                            "controlled": True,
                            "control_equipment": "VRU",
                        },
                        {
                            "id": "src-002",
                            "name": "Wellhead Components",
                            "source_type": "fugitive",
                            "equipment_type": "wellhead",
                            "last_inspection": "2024-09-15",
                        },
                        {
                            "id": "src-003",
                            "name": "Pneumatic Controllers",
                            "source_type": "venting",
                            "equipment_type": "high-bleed pneumatic",
                        },
                    ],
                    "permits": [
                        {
                            "permit_number": "PBR-12345",
                            "permit_type": "Permit by Rule",
                            "status": "active",
                            "expiration_date": "2025-12-31",
                        }
                    ],
                    "total_potential_emissions_tpy": {
                        "VOC": 45.5,
                        "NOx": 12.3,
                        "CO": 8.7,
                        "HAP": 3.2,
                        "CO2e": 15000,
                    },
                },
            },
            {
                "facility_id": "bakken-001",
                "name": "Bakken Gathering Station",
                "facility_type": "gathering",
                "state": "ND",
                "county": "McKenzie",
                "operator": "Demo Oil & Gas Co.",
                "is_major_source": True,
                "title_v_applicable": True,
                "metadata": {
                    "emission_sources": [
                        {
                            "id": "src-010",
                            "name": "Compressor Engine 1",
                            "source_type": "combustion",
                            "equipment_type": "natural gas compressor",
                        },
                        {
                            "id": "src-011",
                            "name": "Compressor Seals",
                            "source_type": "fugitive",
                            "equipment_type": "compressor rod packing",
                            "last_inspection": "2024-06-01",
                        },
                        {
                            "id": "src-012",
                            "name": "Dehydrator",
                            "source_type": "process",
                            "equipment_type": "glycol dehydrator",
                            "controlled": False,
                        },
                    ],
                    "permits": [
                        {
                            "permit_number": "TV-2023-001",
                            "permit_type": "Title V",
                            "status": "active",
                            "expiration_date": "2028-06-30",
                        }
                    ],
                    "total_potential_emissions_tpy": {
                        "VOC": 125.0,
                        "NOx": 85.0,
                        "CO": 45.0,
                        "HAP": 12.5,
                        "CO2e": 45000,
                    },
                },
            },
        ]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current analysis context."""
        return self.context.get_summary()
    
    async def cleanup(self):
        """Clean up resources."""
        if self.memory_store:
            await self.memory_store.disconnect()
        logger.info("EnviroComply Crew cleaned up")


# Convenience function for running analysis
async def run_compliance_analysis(
    facilities: List[Dict] = None,
    lookback_days: int = 30,
    report_types: List[ReportType] = None,
) -> Dict[str, Any]:
    """
    Convenience function to run full compliance analysis.
    
    Args:
        facilities: Facilities to analyze
        lookback_days: Days to look back for regulations
        report_types: Reports to generate
        
    Returns:
        Analysis results
    """
    crew = EnviroComplyCrew()
    
    try:
        await crew.initialize()
        results = await crew.run_full_analysis(
            facilities=facilities,
            lookback_days=lookback_days,
            report_types=report_types,
        )
        return results
    finally:
        await crew.cleanup()
