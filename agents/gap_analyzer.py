"""
Gap Analyzer Agent
==================
Identifies compliance gaps between current operations and regulatory requirements.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from loguru import logger

from .base_agent import BaseAgent, AgentContext
from core.config import settings
from core.models import ComplianceGap, GapSeverity, GapStatus


class GapAnalyzerAgent(BaseAgent):
    """
    Agent responsible for identifying compliance gaps and
    generating prioritized remediation recommendations.
    
    Capabilities:
    - Compare facility status against applicable regulations
    - Identify missing permits, outdated equipment, procedural gaps
    - Calculate risk scores for each compliance gap
    - Track gap closure progress over time
    - Generate prioritized remediation recommendations
    """
    
    @property
    def agent_type(self) -> str:
        return "gap_analyzer"
    
    @property
    def description(self) -> str:
        return "Identifies compliance gaps and recommends remediation actions"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert environmental compliance auditor specializing in 
Oil & Gas regulatory compliance. Your role is to:

1. Identify gaps between current facility operations and regulatory requirements
2. Assess the severity and risk of each gap
3. Recommend specific remediation actions
4. Prioritize gaps by regulatory deadline and enforcement risk
5. Estimate costs and timelines for gap closure

Gap Severity Classifications:
- CRITICAL: Immediate violation risk, enforcement action likely, public health concern
- HIGH: Non-compliance within 90 days if unaddressed, significant penalties possible
- MEDIUM: Best practice gaps, potential future requirements, minor violations
- LOW: Optimization opportunities, efficiency improvements

When analyzing gaps, consider:
- Current EPA and state enforcement priorities
- Recent consent decrees and settlement patterns
- Penalty calculation methodologies
- Self-disclosure benefits
- Upcoming regulatory changes

For each gap identified:
1. Cite the specific regulatory requirement
2. Describe the current facility status
3. Explain the gap clearly
4. Assess risk (likelihood and consequence)
5. Recommend specific corrective actions
6. Estimate timeline and cost
7. Identify responsible parties

Be thorough but practical - focus on actionable gaps that can be addressed."""

    async def run(
        self,
        context: AgentContext = None,
        facilities: List[Dict] = None,
        impact_assessments: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Run gap analysis for facilities.
        
        Args:
            context: Shared agent context
            facilities: Facility profiles to analyze
            impact_assessments: Results from Impact Assessor
            
        Returns:
            Dictionary with identified gaps and recommendations
        """
        # Use context if available
        if context:
            facilities = facilities or context.facilities
            if not impact_assessments:
                impact_assessments = [
                    context.metadata.get(f"impact_{f.get('facility_id')}")
                    for f in facilities
                    if context.metadata.get(f"impact_{f.get('facility_id')}")
                ]
        
        if not facilities:
            logger.warning("No facilities provided for gap analysis")
            return {"gaps": [], "summary": "No facilities to analyze"}
        
        results = {
            "gaps": [],
            "gap_summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "total": 0,
            },
            "priority_actions": [],
            "estimated_total_remediation_cost": 0,
            "analysis_date": datetime.utcnow().isoformat(),
        }
        
        for facility in facilities:
            facility_id = facility.get("facility_id")
            logger.info(f"Analyzing gaps for facility: {facility.get('name')}")
            
            # Find corresponding impact assessment
            impact = next(
                (a for a in (impact_assessments or []) if a.get("facility_id") == facility_id),
                None
            )
            
            # Perform gap analysis
            facility_gaps = await self._analyze_facility_gaps(facility, impact)
            
            for gap in facility_gaps:
                results["gaps"].append(gap)
                results["gap_summary"][gap.get("severity", "medium")] += 1
                results["gap_summary"]["total"] += 1
                results["estimated_total_remediation_cost"] += gap.get("estimated_cost", 0)
                
                # Add to context
                if context:
                    context.add_gap(gap)
                
                # Track priority actions
                if gap.get("severity") in ["critical", "high"]:
                    results["priority_actions"].append({
                        "facility": facility.get("name"),
                        "gap": gap.get("title"),
                        "severity": gap.get("severity"),
                        "deadline": gap.get("regulatory_deadline"),
                        "action": gap.get("recommended_action"),
                    })
        
        # Sort priority actions
        results["priority_actions"] = sorted(
            results["priority_actions"],
            key=lambda x: (
                0 if x.get("severity") == "critical" else 1,
                x.get("deadline") or "9999-99-99"
            )
        )
        
        # Log decision
        await self.log_decision(
            decision_type="gap_analysis",
            action_taken=f"Analyzed {len(facilities)} facilities",
            reasoning=f"Identified {results['gap_summary']['total']} gaps: "
                     f"{results['gap_summary']['critical']} critical, "
                     f"{results['gap_summary']['high']} high",
            confidence=0.88,
            input_data={"facility_count": len(facilities)},
            output_data=results["gap_summary"],
            facility_ids=[f.get("facility_id") for f in facilities],
        )
        
        return results
    
    async def _analyze_facility_gaps(
        self,
        facility: Dict,
        impact_assessment: Dict = None
    ) -> List[Dict]:
        """Analyze gaps for a single facility."""
        
        gaps = []
        
        # 1. Analyze regulatory compliance gaps
        regulatory_gaps = await self._check_regulatory_compliance(facility, impact_assessment)
        gaps.extend(regulatory_gaps)
        
        # 2. Analyze permit gaps
        permit_gaps = await self._check_permit_compliance(facility)
        gaps.extend(permit_gaps)
        
        # 3. Analyze monitoring/recordkeeping gaps
        monitoring_gaps = await self._check_monitoring_compliance(facility)
        gaps.extend(monitoring_gaps)
        
        # 4. Analyze equipment/operational gaps
        equipment_gaps = await self._check_equipment_compliance(facility)
        gaps.extend(equipment_gaps)
        
        # Calculate risk scores for all gaps
        for gap in gaps:
            gap["risk_score"] = self._calculate_risk_score(gap)
            gap["facility_id"] = facility.get("facility_id")
        
        return gaps
    
    async def _check_regulatory_compliance(
        self,
        facility: Dict,
        impact_assessment: Dict = None
    ) -> List[Dict]:
        """Check compliance against applicable regulations."""
        
        gaps = []
        
        # Use impact assessment if available
        if impact_assessment:
            for reg_impact in impact_assessment.get("regulation_impacts", []):
                if reg_impact.get("impact_level") in ["critical", "high"]:
                    # Generate gap from identified issues
                    gap = await self._create_gap_from_impact(facility, reg_impact)
                    if gap:
                        gaps.append(gap)
        
        # Also check standard regulatory areas
        standard_gaps = await self._check_standard_requirements(facility)
        gaps.extend(standard_gaps)
        
        return gaps
    
    async def _create_gap_from_impact(
        self,
        facility: Dict,
        reg_impact: Dict
    ) -> Optional[Dict]:
        """Create a gap record from a regulation impact assessment."""
        
        prompt = f"""Based on this regulatory impact, identify if there is a compliance gap:

Facility: {facility.get('name')} ({facility.get('facility_type')})
Regulation: {reg_impact.get('regulation_citation')}
Impact Level: {reg_impact.get('impact_level')}
Primary Concern: {reg_impact.get('primary_concern')}
Required Actions: {reg_impact.get('required_actions', [])}

If there is a gap, provide:
1. Clear title for the gap
2. Detailed description
3. Severity (critical/high/medium/low)
4. Recommended corrective action
5. Estimated cost to remediate
6. Timeline to address

If no gap exists (facility is compliant), respond with NULL."""

        result = await self.think_structured(
            prompt=prompt,
            output_schema={
                "has_gap": "boolean",
                "title": "short descriptive title",
                "description": "detailed description of the gap",
                "severity": "critical/high/medium/low",
                "recommended_action": "specific corrective action",
                "estimated_cost": 0,
                "timeline_days": 0,
                "regulatory_deadline": "YYYY-MM-DD or null",
                "evidence": ["supporting evidence points"],
                "enforcement_risk": "description of enforcement risk",
            }
        )
        
        if not result.get("has_gap"):
            return None
        
        return {
            "id": f"gap_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{facility.get('facility_id')[:8]}",
            "title": result.get("title"),
            "description": result.get("description"),
            "severity": result.get("severity", "medium"),
            "status": "open",
            "regulation_id": reg_impact.get("regulation_citation"),
            "recommended_action": result.get("recommended_action"),
            "estimated_cost": result.get("estimated_cost", 0),
            "timeline_days": result.get("timeline_days", 90),
            "regulatory_deadline": result.get("regulatory_deadline"),
            "evidence": result.get("evidence", []),
            "enforcement_risk": result.get("enforcement_risk"),
            "identified_at": datetime.utcnow().isoformat(),
        }
    
    async def _check_standard_requirements(self, facility: Dict) -> List[Dict]:
        """Check against standard O&G compliance requirements."""
        
        gaps = []
        metadata = facility.get("metadata", {})
        sources = metadata.get("emission_sources", [])
        permits = metadata.get("permits", [])
        
        # Check LDAR requirements
        fugitive_sources = [s for s in sources if s.get("source_type") == "fugitive"]
        if fugitive_sources:
            ldar_gap = await self._check_ldar_compliance(facility, fugitive_sources)
            if ldar_gap:
                gaps.append(ldar_gap)
        
        # Check storage vessel requirements
        storage_sources = [s for s in sources if s.get("source_type") == "storage"]
        if storage_sources:
            storage_gap = await self._check_storage_compliance(facility, storage_sources)
            if storage_gap:
                gaps.append(storage_gap)
        
        # Check pneumatic controller requirements
        pneumatic_equipment = [s for s in sources if "pneumatic" in s.get("equipment_type", "").lower()]
        if pneumatic_equipment:
            pneumatic_gap = await self._check_pneumatic_compliance(facility, pneumatic_equipment)
            if pneumatic_gap:
                gaps.append(pneumatic_gap)
        
        return gaps
    
    async def _check_ldar_compliance(
        self,
        facility: Dict,
        fugitive_sources: List[Dict]
    ) -> Optional[Dict]:
        """Check LDAR (Leak Detection and Repair) compliance."""
        
        # Check last inspection dates
        last_inspections = [
            s.get("last_inspection") for s in fugitive_sources
            if s.get("last_inspection")
        ]
        
        if not last_inspections:
            return {
                "id": f"gap_ldar_{facility.get('facility_id')[:8]}",
                "title": "LDAR Program Not Documented",
                "description": "No LDAR inspection records found for fugitive emission sources. "
                              "NSPS OOOOa requires quarterly surveys using OGI or Method 21.",
                "severity": "critical",
                "status": "open",
                "regulation_id": "40 CFR 60.5397a",
                "recommended_action": "Implement LDAR program immediately. Conduct initial survey "
                                     "using OGI camera or EPA Method 21. Establish quarterly "
                                     "survey schedule and repair tracking system.",
                "estimated_cost": 25000,
                "timeline_days": 30,
                "evidence": ["No inspection records in facility profile"],
                "enforcement_risk": "High - LDAR is a top EPA enforcement priority",
                "identified_at": datetime.utcnow().isoformat(),
            }
        
        # Check if surveys are current (within 90 days for quarterly requirement)
        oldest_inspection = min(last_inspections)
        days_since = (date.today() - date.fromisoformat(str(oldest_inspection))).days
        
        if days_since > 90:
            return {
                "id": f"gap_ldar_overdue_{facility.get('facility_id')[:8]}",
                "title": "LDAR Survey Overdue",
                "description": f"Last LDAR survey was {days_since} days ago. Quarterly surveys "
                              "required under NSPS OOOOa for wellhead and compressor components.",
                "severity": "high",
                "status": "open",
                "regulation_id": "40 CFR 60.5397a",
                "recommended_action": f"Conduct LDAR survey within {max(0, 90 - days_since)} days. "
                                     "Schedule remaining quarterly surveys for the year.",
                "estimated_cost": 5000,
                "timeline_days": 14,
                "evidence": [f"Last survey: {oldest_inspection}", f"Days overdue: {days_since - 90}"],
                "identified_at": datetime.utcnow().isoformat(),
            }
        
        return None
    
    async def _check_storage_compliance(
        self,
        facility: Dict,
        storage_sources: List[Dict]
    ) -> Optional[Dict]:
        """Check storage vessel compliance."""
        
        # Check for uncontrolled storage vessels
        uncontrolled = [
            s for s in storage_sources
            if not s.get("controlled", False)
        ]
        
        if uncontrolled:
            return {
                "id": f"gap_storage_{facility.get('facility_id')[:8]}",
                "title": "Uncontrolled Storage Vessels",
                "description": f"Found {len(uncontrolled)} storage vessels without emission controls. "
                              "NSPS OOOOa requires 95% control efficiency for vessels with PTE ≥6 tpy VOC.",
                "severity": "high",
                "status": "open",
                "regulation_id": "40 CFR 60.5395a",
                "recommended_action": "Evaluate PTE for each vessel. Install VRU or combust emissions "
                                     "for vessels exceeding threshold. Document low-production exemptions.",
                "estimated_cost": 50000 * len(uncontrolled),
                "timeline_days": 180,
                "evidence": [f"{len(uncontrolled)} uncontrolled vessels identified"],
                "identified_at": datetime.utcnow().isoformat(),
            }
        
        return None
    
    async def _check_pneumatic_compliance(
        self,
        facility: Dict,
        pneumatic_equipment: List[Dict]
    ) -> Optional[Dict]:
        """Check pneumatic controller compliance."""
        
        # Check for high-bleed controllers
        high_bleed = [
            p for p in pneumatic_equipment
            if "high" in p.get("equipment_type", "").lower() or
               p.get("bleed_rate", 0) > 6  # scfh threshold
        ]
        
        if high_bleed:
            return {
                "id": f"gap_pneumatic_{facility.get('facility_id')[:8]}",
                "title": "High-Bleed Pneumatic Controllers",
                "description": f"Found {len(high_bleed)} high-bleed pneumatic controllers. "
                              "NSPS OOOOb requires low-bleed or zero-emission controllers at wellsites.",
                "severity": "medium",
                "status": "open",
                "regulation_id": "40 CFR 60.5390a",
                "recommended_action": "Replace high-bleed controllers with low-bleed (<6 scfh) or "
                                     "zero-emission alternatives. Document functional need exemptions.",
                "estimated_cost": 2500 * len(high_bleed),
                "timeline_days": 365,
                "evidence": [f"{len(high_bleed)} high-bleed controllers identified"],
                "identified_at": datetime.utcnow().isoformat(),
            }
        
        return None
    
    async def _check_permit_compliance(self, facility: Dict) -> List[Dict]:
        """Check permit-related compliance gaps."""
        
        gaps = []
        metadata = facility.get("metadata", {})
        permits = metadata.get("permits", [])
        
        # Check for expired permits
        for permit in permits:
            if permit.get("expiration_date"):
                exp_date = date.fromisoformat(str(permit.get("expiration_date")))
                days_until = (exp_date - date.today()).days
                
                if days_until < 0:
                    gaps.append({
                        "id": f"gap_permit_expired_{permit.get('permit_number', '')[:10]}",
                        "title": f"Expired Permit: {permit.get('permit_number')}",
                        "description": f"Permit {permit.get('permit_number')} ({permit.get('permit_type')}) "
                                      f"expired {abs(days_until)} days ago.",
                        "severity": "critical",
                        "status": "open",
                        "regulation_id": "State permit regulations",
                        "recommended_action": "Submit renewal application immediately. Contact agency "
                                             "about operating under expired permit provisions.",
                        "estimated_cost": 15000,
                        "timeline_days": 30,
                        "evidence": [f"Permit expired: {permit.get('expiration_date')}"],
                        "identified_at": datetime.utcnow().isoformat(),
                    })
                elif days_until < 180:
                    gaps.append({
                        "id": f"gap_permit_expiring_{permit.get('permit_number', '')[:10]}",
                        "title": f"Permit Expiring Soon: {permit.get('permit_number')}",
                        "description": f"Permit {permit.get('permit_number')} expires in {days_until} days. "
                                      "Most agencies require 6+ months notice for renewal.",
                        "severity": "high" if days_until < 90 else "medium",
                        "status": "open",
                        "regulation_id": "State permit regulations",
                        "recommended_action": "Initiate permit renewal process. Gather emissions data "
                                             "and prepare renewal application.",
                        "estimated_cost": 10000,
                        "timeline_days": 60,
                        "evidence": [f"Permit expires: {permit.get('expiration_date')}"],
                        "identified_at": datetime.utcnow().isoformat(),
                    })
        
        # Check if Title V required but not present
        if facility.get("title_v_applicable") or facility.get("is_major_source"):
            has_title_v = any(
                p.get("permit_type", "").lower() == "title v" or "title v" in p.get("permit_type", "").lower()
                for p in permits
            )
            
            if not has_title_v:
                gaps.append({
                    "id": f"gap_title_v_{facility.get('facility_id')[:8]}",
                    "title": "Missing Title V Operating Permit",
                    "description": "Facility appears to be a major source but no Title V permit on file. "
                                  "Major sources must obtain Title V permits.",
                    "severity": "critical",
                    "status": "open",
                    "regulation_id": "40 CFR Part 70",
                    "recommended_action": "Verify major source status. If confirmed, submit Title V "
                                         "application to state agency immediately.",
                    "estimated_cost": 75000,
                    "timeline_days": 365,
                    "evidence": ["Facility classified as major source", "No Title V permit found"],
                    "identified_at": datetime.utcnow().isoformat(),
                })
        
        return gaps
    
    async def _check_monitoring_compliance(self, facility: Dict) -> List[Dict]:
        """Check monitoring and recordkeeping compliance."""
        # Placeholder for detailed monitoring analysis
        return []
    
    async def _check_equipment_compliance(self, facility: Dict) -> List[Dict]:
        """Check equipment-specific compliance."""
        # Placeholder for detailed equipment analysis
        return []
    
    def _calculate_risk_score(self, gap: Dict) -> float:
        """
        Calculate risk score for a gap (0-1 scale).
        
        Risk = Likelihood of Enforcement × Consequence Severity
        """
        severity_scores = {
            "critical": 0.95,
            "high": 0.75,
            "medium": 0.50,
            "low": 0.25,
        }
        
        base_score = severity_scores.get(gap.get("severity", "medium"), 0.5)
        
        # Adjust for deadline proximity
        deadline = gap.get("regulatory_deadline")
        if deadline:
            try:
                days_until = (date.fromisoformat(str(deadline)) - date.today()).days
                if days_until < 30:
                    base_score = min(1.0, base_score + 0.2)
                elif days_until < 90:
                    base_score = min(1.0, base_score + 0.1)
            except:
                pass
        
        # Adjust for enforcement risk description
        enforcement_risk = gap.get("enforcement_risk", "").lower()
        if "high" in enforcement_risk or "priority" in enforcement_risk:
            base_score = min(1.0, base_score + 0.1)
        
        return round(base_score, 2)
