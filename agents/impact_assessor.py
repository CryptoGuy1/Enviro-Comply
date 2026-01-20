"""
Impact Assessor Agent
=====================
Maps regulatory requirements to specific facility operations and equipment.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from loguru import logger

from .base_agent import BaseAgent, AgentContext
from core.config import settings
from core.models import Facility, Regulation, ComplianceRequirement


class ImpactAssessorAgent(BaseAgent):
    """
    Agent responsible for assessing the impact of regulations
    on specific Oil & Gas facilities and operations.
    
    Capabilities:
    - Maintain facility profiles with equipment and emission sources
    - Determine which regulations apply to each facility
    - Calculate potential compliance burden
    - Identify equipment or processes affected by new rules
    - Prioritize impacts by severity and deadline
    """
    
    @property
    def agent_type(self) -> str:
        return "impact_assessor"
    
    @property
    def description(self) -> str:
        return "Assesses regulatory impact on specific facilities and operations"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert environmental compliance engineer specializing in 
Oil & Gas facility assessments. Your role is to:

1. Analyze facility profiles to understand operations, equipment, and emission sources
2. Determine regulatory applicability based on facility characteristics
3. Assess compliance burden including costs, timeline, and resources needed
4. Identify which specific equipment or processes are affected
5. Prioritize impacts by regulatory deadline and potential consequences

You have expertise in:
- Oil & Gas facility types: production sites, gathering systems, gas plants, compressor stations
- Emission source categories: combustion, fugitive, venting, storage, loading
- Applicability determinations for NSPS OOOO/OOOOa/OOOOb, NESHAP HH, Title V
- Emission calculations and potential-to-emit (PTE) analysis
- Compliance cost estimation

When assessing impact, always consider:
- Facility's potential to emit (PTE) vs actual emissions
- Major source vs area source classification
- Existing permits and their conditions
- Equipment age and modification history
- State-specific requirements in addition to federal

Provide specific, actionable assessments that help facilities understand exactly 
what they need to do to comply."""

    async def run(
        self,
        context: AgentContext = None,
        facilities: List[Dict] = None,
        regulations: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Run impact assessment for facilities against regulations.
        
        Args:
            context: Shared agent context
            facilities: List of facility profiles to assess
            regulations: List of regulations to check against
            
        Returns:
            Dictionary with impact assessments by facility
        """
        # Use context if no direct inputs
        if context:
            facilities = facilities or context.facilities
            regulations = regulations or context.regulations
        
        if not facilities:
            logger.warning("No facilities provided for impact assessment")
            return {"assessments": [], "summary": "No facilities to assess"}
        
        if not regulations:
            logger.info("No specific regulations provided, will assess against all applicable")
            regulations = await self._get_applicable_regulations()
        
        results = {
            "assessments": [],
            "high_impact_facilities": [],
            "total_estimated_cost": 0,
            "critical_actions": [],
            "assessment_date": datetime.utcnow().isoformat(),
        }
        
        for facility in facilities:
            logger.info(f"Assessing impact for facility: {facility.get('name')}")
            
            assessment = await self._assess_facility(facility, regulations)
            results["assessments"].append(assessment)
            
            # Track high-impact facilities
            if assessment.get("overall_impact_score", 0) >= 70:
                results["high_impact_facilities"].append({
                    "facility_id": facility.get("facility_id"),
                    "facility_name": facility.get("name"),
                    "impact_score": assessment.get("overall_impact_score"),
                    "top_issues": assessment.get("top_issues", [])[:3],
                })
            
            # Accumulate costs
            results["total_estimated_cost"] += assessment.get("estimated_total_cost", 0)
            
            # Collect critical actions
            for action in assessment.get("required_actions", []):
                if action.get("priority") == "critical":
                    results["critical_actions"].append({
                        "facility": facility.get("name"),
                        "action": action.get("description"),
                        "deadline": action.get("deadline"),
                    })
            
            # Add to context if provided
            if context:
                context.metadata[f"impact_{facility.get('facility_id')}"] = assessment
        
        # Log decision
        await self.log_decision(
            decision_type="impact_assessment",
            action_taken=f"Assessed {len(facilities)} facilities against {len(regulations)} regulations",
            reasoning=f"Identified {len(results['high_impact_facilities'])} high-impact facilities, {len(results['critical_actions'])} critical actions",
            confidence=0.85,
            input_data={
                "facility_count": len(facilities),
                "regulation_count": len(regulations),
            },
            output_data={
                "high_impact_count": len(results["high_impact_facilities"]),
                "critical_actions_count": len(results["critical_actions"]),
                "total_estimated_cost": results["total_estimated_cost"],
            },
            facility_ids=[f.get("facility_id") for f in facilities],
            regulation_ids=[r.get("id") for r in regulations],
        )
        
        return results
    
    async def _assess_facility(
        self,
        facility: Dict,
        regulations: List[Dict]
    ) -> Dict[str, Any]:
        """Assess a single facility against regulations."""
        
        # Build facility context for LLM
        facility_context = self._build_facility_context(facility)
        
        # Determine applicable regulations
        applicable_regs = await self._determine_applicability(facility, regulations)
        
        # Assess impact of each applicable regulation
        impacts = []
        total_cost = 0
        required_actions = []
        
        for reg in applicable_regs:
            impact = await self._assess_regulation_impact(facility, reg)
            impacts.append(impact)
            total_cost += impact.get("estimated_cost", 0)
            required_actions.extend(impact.get("required_actions", []))
        
        # Calculate overall impact score
        impact_score = self._calculate_impact_score(impacts)
        
        # Prioritize actions
        required_actions = sorted(
            required_actions,
            key=lambda x: (
                0 if x.get("priority") == "critical" else
                1 if x.get("priority") == "high" else
                2 if x.get("priority") == "medium" else 3,
                x.get("deadline", "9999-99-99")
            )
        )
        
        # Identify top issues
        top_issues = [
            {
                "regulation": imp.get("regulation_citation"),
                "issue": imp.get("primary_concern"),
                "impact_level": imp.get("impact_level"),
            }
            for imp in sorted(impacts, key=lambda x: x.get("impact_score", 0), reverse=True)[:5]
        ]
        
        return {
            "facility_id": facility.get("facility_id"),
            "facility_name": facility.get("name"),
            "assessment_date": datetime.utcnow().isoformat(),
            "applicable_regulations": [r.get("citation") for r in applicable_regs],
            "regulation_impacts": impacts,
            "overall_impact_score": impact_score,
            "estimated_total_cost": total_cost,
            "required_actions": required_actions,
            "top_issues": top_issues,
            "facility_classification": await self._classify_facility(facility),
        }
    
    def _build_facility_context(self, facility: Dict) -> str:
        """Build a text description of the facility for LLM context."""
        metadata = facility.get("metadata", {})
        
        lines = [
            f"Facility: {facility.get('name')}",
            f"Type: {facility.get('facility_type')}",
            f"Location: {facility.get('county')}, {facility.get('state')}",
            f"Operator: {facility.get('operator')}",
            f"Major Source: {facility.get('is_major_source', False)}",
            f"Title V: {facility.get('title_v_applicable', False)}",
        ]
        
        # Add emission sources
        sources = metadata.get("emission_sources", [])
        if sources:
            lines.append("\nEmission Sources:")
            for source in sources[:10]:
                lines.append(f"  - {source.get('name')}: {source.get('source_type')} ({source.get('equipment_type')})")
        
        # Add permits
        permits = metadata.get("permits", [])
        if permits:
            lines.append("\nPermits:")
            for permit in permits:
                lines.append(f"  - {permit.get('permit_number')}: {permit.get('permit_type')}")
        
        # Add emissions summary
        emissions = metadata.get("total_potential_emissions_tpy", {})
        if emissions:
            lines.append("\nPotential Emissions (tpy):")
            for pollutant, amount in emissions.items():
                lines.append(f"  - {pollutant}: {amount}")
        
        return "\n".join(lines)
    
    async def _determine_applicability(
        self,
        facility: Dict,
        regulations: List[Dict]
    ) -> List[Dict]:
        """Determine which regulations apply to a facility."""
        
        applicable = []
        facility_type = facility.get("facility_type", "").lower()
        is_major = facility.get("is_major_source", False)
        
        for reg in regulations:
            # Check facility type match
            reg_facility_types = [ft.lower() for ft in reg.get("applicable_facility_types", [])]
            
            if not reg_facility_types or facility_type in reg_facility_types or "all" in reg_facility_types:
                # Further analysis with LLM for edge cases
                if await self._check_detailed_applicability(facility, reg):
                    applicable.append(reg)
        
        return applicable
    
    async def _check_detailed_applicability(self, facility: Dict, regulation: Dict) -> bool:
        """Use LLM to check detailed applicability criteria."""
        
        prompt = f"""Determine if this regulation applies to this Oil & Gas facility.

Regulation: {regulation.get('citation')} - {regulation.get('title')}
Regulation Type: {regulation.get('regulation_type')}
Applicability Criteria from Regulation: {regulation.get('key_requirements', [])}

Facility Profile:
{self._build_facility_context(facility)}

Does this regulation apply to this facility? Consider:
1. Facility type and operations
2. Emission sources present
3. Emission thresholds (if specified)
4. Construction/modification dates
5. State location

Respond with YES or NO, followed by a brief explanation."""

        response = await self.think(prompt)
        return response.strip().upper().startswith("YES")
    
    async def _assess_regulation_impact(
        self,
        facility: Dict,
        regulation: Dict
    ) -> Dict[str, Any]:
        """Assess the impact of a specific regulation on a facility."""
        
        prompt = f"""Assess the compliance impact of this regulation on this facility:

Regulation: {regulation.get('citation')} - {regulation.get('title')}
Key Requirements: {regulation.get('key_requirements', [])}
Compliance Deadline: {regulation.get('compliance_deadline', 'Not specified')}

Facility: {facility.get('name')}
{self._build_facility_context(facility)}

Analyze:
1. What specific equipment/sources are affected?
2. What new monitoring/testing is required?
3. What recordkeeping changes are needed?
4. What capital expenditures might be required?
5. What operational changes are needed?
6. What is the estimated compliance cost?
7. What is the timeline to achieve compliance?
8. What are the risks of non-compliance?"""

        impact = await self.think_structured(
            prompt=prompt,
            output_schema={
                "regulation_citation": regulation.get("citation"),
                "affected_equipment": ["list of affected equipment/sources"],
                "monitoring_requirements": ["new monitoring requirements"],
                "recordkeeping_changes": ["recordkeeping changes needed"],
                "capital_requirements": ["capital expenditures needed"],
                "operational_changes": ["operational changes required"],
                "estimated_cost": 0,  # USD
                "compliance_timeline_days": 0,
                "impact_level": "critical/high/medium/low",
                "impact_score": 0,  # 0-100
                "primary_concern": "main compliance challenge",
                "non_compliance_risk": "description of enforcement risk",
                "required_actions": [
                    {
                        "description": "action needed",
                        "priority": "critical/high/medium/low",
                        "deadline": "YYYY-MM-DD or None",
                        "estimated_cost": 0,
                        "responsible_party": "who should do this",
                    }
                ],
            },
            context={"facility_type": facility.get("facility_type")}
        )
        
        return impact
    
    def _calculate_impact_score(self, impacts: List[Dict]) -> float:
        """Calculate overall impact score from individual regulation impacts."""
        if not impacts:
            return 0.0
        
        # Weight by impact level
        level_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2,
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for impact in impacts:
            level = impact.get("impact_level", "medium").lower()
            weight = level_weights.get(level, 0.4)
            score = impact.get("impact_score", 50)
            
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return round(weighted_sum / total_weight, 1)
    
    async def _classify_facility(self, facility: Dict) -> Dict[str, Any]:
        """Classify facility for regulatory purposes."""
        
        metadata = facility.get("metadata", {})
        emissions = metadata.get("total_potential_emissions_tpy", {})
        
        # Determine major source status
        # Major source thresholds (simplified):
        # - 100 tpy for criteria pollutants in attainment areas
        # - 10 tpy for single HAP, 25 tpy for combined HAPs
        
        voc_pte = emissions.get("VOC", 0)
        nox_pte = emissions.get("NOx", 0)
        hap_pte = emissions.get("HAP", 0)
        
        is_major_criteria = voc_pte >= 100 or nox_pte >= 100
        is_major_hap = hap_pte >= 10
        
        return {
            "is_major_source_criteria": is_major_criteria,
            "is_major_source_hap": is_major_hap,
            "title_v_required": is_major_criteria or is_major_hap,
            "nsps_applicable": True,  # Almost always applies to O&G
            "neshap_applicable": is_major_hap or facility.get("facility_type") in ["processing", "production"],
            "ghg_reporting_required": emissions.get("CO2e", 0) >= 25000,
            "pte_summary": {
                "VOC_tpy": voc_pte,
                "NOx_tpy": nox_pte,
                "HAP_tpy": hap_pte,
                "CO2e_tpy": emissions.get("CO2e", 0),
            }
        }
    
    async def _get_applicable_regulations(self) -> List[Dict]:
        """Get all potentially applicable regulations for O&G facilities."""
        # In production, this would query Weaviate
        # Return core O&G regulations
        
        return [
            {
                "id": "nsps-ooooa",
                "citation": "40 CFR 60 Subpart OOOOa",
                "title": "Standards of Performance for Crude Oil and Natural Gas Facilities",
                "regulation_type": "nsps",
                "applicable_facility_types": ["production", "gathering", "processing", "transmission"],
                "key_requirements": [
                    "Fugitive emissions monitoring (LDAR)",
                    "Storage vessel controls",
                    "Pneumatic controller standards",
                    "Compressor requirements",
                ],
            },
            {
                "id": "neshap-hh",
                "citation": "40 CFR 63 Subpart HH",
                "title": "National Emission Standards for Hazardous Air Pollutants from Oil and Natural Gas Production Facilities",
                "regulation_type": "neshap",
                "applicable_facility_types": ["production", "processing"],
                "key_requirements": [
                    "HAP emission controls",
                    "Glycol dehydrator requirements",
                    "Storage vessel controls",
                ],
            },
            {
                "id": "ghg-subpart-w",
                "citation": "40 CFR 98 Subpart W",
                "title": "Petroleum and Natural Gas Systems GHG Reporting",
                "regulation_type": "ghg_reporting",
                "applicable_facility_types": ["production", "gathering", "processing", "transmission"],
                "key_requirements": [
                    "Annual GHG emissions reporting",
                    "Emissions calculation methodologies",
                    "Data verification requirements",
                ],
            },
        ]
