"""
Regulation Monitor Agent
========================
Monitors EPA and state regulatory sources for changes relevant to Oil & Gas operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import asyncio
from loguru import logger

from .base_agent import BaseAgent, AgentContext
from core.config import settings
from core.models import (
    Regulation, RegulatoryChange, RegulationType, RegulatoryStatus,
    FacilityType, EmissionSourceType
)


class RegulationMonitorAgent(BaseAgent):
    """
    Agent responsible for monitoring regulatory sources and
    identifying changes relevant to Oil & Gas operations.
    
    Capabilities:
    - Monitor EPA Federal Register for Clean Air Act updates
    - Track state environmental agency announcements
    - Classify regulations by Oil & Gas applicability
    - Extract compliance deadlines and effective dates
    """
    
    @property
    def agent_type(self) -> str:
        return "regulation_monitor"
    
    @property
    def description(self) -> str:
        return "Monitors EPA and state regulations for Oil & Gas compliance changes"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert environmental regulatory analyst specializing in 
EPA Clean Air Act regulations for the Oil & Gas industry. Your role is to:

1. Analyze regulatory documents and identify key requirements
2. Determine applicability to Oil & Gas facilities (upstream, midstream, downstream)
3. Extract compliance deadlines, effective dates, and phase-in schedules
4. Identify which types of equipment and emission sources are affected
5. Summarize complex regulations in plain language

You have deep knowledge of:
- 40 CFR Part 60 (NSPS) - especially Subparts OOOO, OOOOa, OOOOb
- 40 CFR Part 63 (NESHAP) - especially Subpart HH, ZZZZ
- 40 CFR Part 98 (Greenhouse Gas Reporting)
- State regulations from Texas (TCEQ), Oklahoma (ODEQ), Wyoming (WDEQ)

When analyzing regulations, always consider:
- Applicability thresholds (production rates, emission levels, equipment counts)
- Existing source vs. new source requirements
- Monitoring, recordkeeping, and reporting obligations
- Compliance timelines and any extensions granted

Provide accurate, actionable analysis that environmental compliance professionals can use."""

    async def run(
        self,
        context: AgentContext = None,
        lookback_days: int = None,
        specific_citations: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the regulation monitoring process.
        
        Args:
            context: Shared agent context
            lookback_days: Days to look back for changes
            specific_citations: Specific CFR citations to check
            
        Returns:
            Dictionary with found regulations and changes
        """
        lookback_days = lookback_days or settings.epa.lookback_days
        start_date = date.today() - timedelta(days=lookback_days)
        
        logger.info(f"Scanning for regulatory changes since {start_date}")
        
        results = {
            "new_regulations": [],
            "amended_regulations": [],
            "upcoming_deadlines": [],
            "alerts": [],
            "scan_date": datetime.utcnow().isoformat(),
        }
        
        # Step 1: Fetch recent Federal Register documents
        fed_reg_docs = await self._fetch_federal_register(start_date)
        
        # Step 2: Analyze each document for Oil & Gas relevance
        for doc in fed_reg_docs:
            analysis = await self._analyze_regulation(doc)
            
            if analysis.get("is_relevant"):
                regulation = self._create_regulation_record(doc, analysis)
                
                if analysis.get("is_new"):
                    results["new_regulations"].append(regulation)
                else:
                    results["amended_regulations"].append(regulation)
                
                # Add to context if provided
                if context:
                    context.add_regulation(regulation)
                
                # Check for urgent deadlines
                if regulation.get("compliance_deadline"):
                    deadline = datetime.fromisoformat(regulation["compliance_deadline"])
                    days_until = (deadline.date() - date.today()).days
                    
                    if days_until <= settings.agent.critical_deadline_days:
                        alert = {
                            "type": "urgent_deadline",
                            "regulation": regulation["citation"],
                            "deadline": regulation["compliance_deadline"],
                            "days_until": days_until,
                            "message": f"Compliance deadline in {days_until} days for {regulation['title']}"
                        }
                        results["alerts"].append(alert)
                        if context:
                            context.add_alert(alert)
        
        # Step 3: Check for upcoming deadlines in existing regulations
        upcoming = await self._check_upcoming_deadlines()
        results["upcoming_deadlines"] = upcoming
        
        # Log decision
        await self.log_decision(
            decision_type="regulatory_scan",
            action_taken=f"Scanned Federal Register for {lookback_days} days",
            reasoning=f"Found {len(results['new_regulations'])} new and {len(results['amended_regulations'])} amended regulations",
            confidence=0.9,
            input_data={"lookback_days": lookback_days, "start_date": start_date.isoformat()},
            output_data={
                "new_count": len(results["new_regulations"]),
                "amended_count": len(results["amended_regulations"]),
                "alert_count": len(results["alerts"]),
            }
        )
        
        return results
    
    async def _fetch_federal_register(self, start_date: date) -> List[Dict]:
        """
        Fetch recent Federal Register documents related to EPA air regulations.
        
        In production, this would make actual API calls. For now, we return
        curated sample data representing real regulations.
        """
        # Simulated Federal Register API response
        # In production: Use requests to call https://www.federalregister.gov/api/v1/documents
        
        sample_documents = [
            {
                "document_number": "2024-12345",
                "title": "Oil and Natural Gas Sector: Emission Standards for New, Reconstructed, and Modified Sources Review",
                "type": "Rule",
                "abstract": "The Environmental Protection Agency is finalizing amendments to the new source performance standards for the oil and natural gas sector to reduce emissions of greenhouse gases and volatile organic compounds.",
                "agencies": [{"name": "Environmental Protection Agency"}],
                "cfr_references": [{"title": 40, "part": 60}],
                "publication_date": (date.today() - timedelta(days=5)).isoformat(),
                "effective_on": (date.today() + timedelta(days=60)).isoformat(),
                "html_url": "https://www.federalregister.gov/documents/2024/12345",
                "full_text_xml_url": "https://www.federalregister.gov/documents/full_text/xml/2024/12345.xml",
            },
            {
                "document_number": "2024-12346",
                "title": "National Emission Standards for Hazardous Air Pollutants: Oil and Natural Gas Production Facilities",
                "type": "Proposed Rule",
                "abstract": "EPA is proposing amendments to the national emission standards for hazardous air pollutants for oil and natural gas production facilities.",
                "agencies": [{"name": "Environmental Protection Agency"}],
                "cfr_references": [{"title": 40, "part": 63}],
                "publication_date": (date.today() - timedelta(days=10)).isoformat(),
                "comments_close_on": (date.today() + timedelta(days=50)).isoformat(),
                "html_url": "https://www.federalregister.gov/documents/2024/12346",
            },
        ]
        
        # Filter by date
        return [
            doc for doc in sample_documents
            if datetime.fromisoformat(doc["publication_date"]).date() >= start_date
        ]
    
    async def _analyze_regulation(self, document: Dict) -> Dict[str, Any]:
        """
        Use LLM to analyze a Federal Register document for Oil & Gas relevance.
        """
        prompt = f"""Analyze this Federal Register document for relevance to Oil & Gas industry compliance:

Title: {document.get('title')}
Type: {document.get('type')}
Abstract: {document.get('abstract')}
CFR References: {document.get('cfr_references')}

Please analyze and respond with:
1. Is this regulation relevant to Oil & Gas operations? (yes/no)
2. Is this a new regulation or an amendment to existing regulation?
3. What types of Oil & Gas facilities does it apply to? (production, gathering, processing, transmission, storage)
4. What emission sources are affected? (combustion, fugitive, venting, storage, loading)
5. What are the key compliance requirements?
6. What are the critical deadlines?
7. Summary in 2-3 sentences for compliance professionals."""

        analysis = await self.think_structured(
            prompt=prompt,
            output_schema={
                "is_relevant": "boolean - true if relevant to Oil & Gas",
                "is_new": "boolean - true if new regulation, false if amendment",
                "applicable_facility_types": ["list of: production, gathering, processing, transmission, storage"],
                "applicable_emission_sources": ["list of: combustion, fugitive, venting, storage, loading"],
                "key_requirements": ["list of key compliance requirements"],
                "deadlines": ["list of important dates and deadlines"],
                "summary": "2-3 sentence summary for compliance professionals",
                "confidence": "0-1 confidence score"
            },
            context={"oil_gas_keywords": settings.epa.oil_gas_keywords}
        )
        
        return analysis
    
    def _create_regulation_record(self, document: Dict, analysis: Dict) -> Dict:
        """Create a regulation record from Federal Register document and analysis."""
        
        # Map facility types
        facility_type_map = {
            "production": FacilityType.PRODUCTION,
            "gathering": FacilityType.GATHERING,
            "processing": FacilityType.PROCESSING,
            "transmission": FacilityType.TRANSMISSION,
            "storage": FacilityType.STORAGE,
        }
        
        # Map emission sources
        source_type_map = {
            "combustion": EmissionSourceType.COMBUSTION,
            "fugitive": EmissionSourceType.FUGITIVE,
            "venting": EmissionSourceType.VENTING,
            "storage": EmissionSourceType.STORAGE,
            "loading": EmissionSourceType.LOADING,
        }
        
        # Determine regulation type from CFR reference
        cfr_refs = document.get("cfr_references", [])
        reg_type = RegulationType.OTHER
        if any(ref.get("part") == 60 for ref in cfr_refs):
            reg_type = RegulationType.NSPS
        elif any(ref.get("part") == 63 for ref in cfr_refs):
            reg_type = RegulationType.NESHAP
        elif any(ref.get("part") == 98 for ref in cfr_refs):
            reg_type = RegulationType.GHG_REPORTING
        
        # Determine status
        doc_type = document.get("type", "").lower()
        if "proposed" in doc_type:
            status = RegulatoryStatus.PROPOSED
        elif "final" in doc_type or doc_type == "rule":
            status = RegulatoryStatus.FINAL
        else:
            status = RegulatoryStatus.EFFECTIVE
        
        # Build citation
        citation = ""
        if cfr_refs:
            ref = cfr_refs[0]
            citation = f"{ref.get('title', 40)} CFR {ref.get('part', '')}"
        
        return {
            "id": document.get("document_number"),
            "title": document.get("title"),
            "description": analysis.get("summary", document.get("abstract")),
            "regulation_type": reg_type.value,
            "status": status.value,
            "citation": citation,
            "federal_register_citation": document.get("document_number"),
            "publication_date": document.get("publication_date"),
            "effective_date": document.get("effective_on"),
            "compliance_deadline": document.get("effective_on"),  # Simplified
            "applicable_facility_types": analysis.get("applicable_facility_types", []),
            "applicable_emission_sources": analysis.get("applicable_emission_sources", []),
            "key_requirements": analysis.get("key_requirements", []),
            "source_url": document.get("html_url"),
            "analysis_confidence": analysis.get("confidence", 0.8),
        }
    
    async def _check_upcoming_deadlines(self) -> List[Dict]:
        """Check for upcoming compliance deadlines in stored regulations."""
        # In production, this would query the database/Weaviate
        # For now, return sample upcoming deadlines
        
        return [
            {
                "regulation": "40 CFR 60 Subpart OOOOb",
                "requirement": "Initial LDAR survey for affected facilities",
                "deadline": (date.today() + timedelta(days=45)).isoformat(),
                "days_until": 45,
                "applies_to": ["production", "gathering"],
            },
            {
                "regulation": "40 CFR 98 Subpart W",
                "requirement": "Annual GHG emissions report submission",
                "deadline": (date.today() + timedelta(days=90)).isoformat(),
                "days_until": 90,
                "applies_to": ["all facilities > 25,000 MT CO2e"],
            },
        ]
    
    async def analyze_specific_regulation(self, citation: str, full_text: str = None) -> Dict:
        """
        Perform deep analysis of a specific regulation.
        
        Args:
            citation: CFR citation (e.g., "40 CFR 60.5360")
            full_text: Optional full regulation text
            
        Returns:
            Detailed analysis of the regulation
        """
        prompt = f"""Perform a detailed analysis of this EPA regulation for Oil & Gas compliance:

Citation: {citation}
{f"Full Text: {full_text[:5000]}" if full_text else ""}

Provide a comprehensive analysis including:
1. Applicability determination criteria
2. Specific equipment/sources covered
3. Emission limits and standards
4. Monitoring requirements (methods, frequency)
5. Recordkeeping requirements
6. Reporting requirements (forms, deadlines)
7. Testing requirements
8. Common compliance pitfalls
9. Cost implications for typical facilities
10. Recent enforcement trends"""

        return await self.think_structured(
            prompt=prompt,
            output_schema={
                "applicability_criteria": ["list of criteria that determine if regulation applies"],
                "covered_equipment": ["list of equipment types covered"],
                "emission_standards": {"pollutant": "standard value and units"},
                "monitoring_requirements": [{"method": "", "frequency": "", "records": ""}],
                "recordkeeping_requirements": ["list of required records"],
                "reporting_requirements": [{"report": "", "frequency": "", "deadline": ""}],
                "testing_requirements": ["list of required tests"],
                "common_pitfalls": ["list of common compliance mistakes"],
                "estimated_compliance_cost": {"low": 0, "high": 0, "notes": ""},
                "enforcement_notes": "recent enforcement trends and priorities",
            }
        )
