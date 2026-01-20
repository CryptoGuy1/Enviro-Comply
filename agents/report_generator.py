"""
Report Generator Agent
======================
Produces submission-ready compliance documents and internal reports.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path
import json
from loguru import logger

from .base_agent import BaseAgent, AgentContext
from core.config import settings
from core.models import ComplianceReport, ReportSection, ReportType, ComplianceScore


class ReportGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating compliance reports and
    documentation for various stakeholders.
    
    Output Types:
    - EPA Title V Annual Compliance Certifications
    - Emissions Inventory Reports
    - Deviation Reports
    - Compliance Status Dashboards
    - Board/Executive Summaries
    - Regulatory Change Briefings
    """
    
    @property
    def agent_type(self) -> str:
        return "report_generator"
    
    @property
    def description(self) -> str:
        return "Generates compliance reports and documentation"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert environmental compliance report writer specializing in 
Oil & Gas regulatory documentation. Your role is to:

1. Generate clear, accurate compliance reports for various audiences
2. Summarize complex regulatory information for executives
3. Create submission-ready regulatory documents
4. Produce actionable compliance status reports
5. Document gap analyses with clear remediation paths

Report Types You Generate:
- Title V Annual Compliance Certifications
- Emissions Inventory Reports
- Deviation/Exceedance Reports
- Gap Analysis Reports
- Executive Compliance Summaries
- Regulatory Change Briefings
- Audit Preparation Documents

Writing Guidelines:
- Use clear, professional language
- Be specific with citations and deadlines
- Include actionable recommendations
- Use tables and structured formats for data
- Tailor content to the audience (technical vs executive)
- Always include dates, references, and responsible parties

For regulatory submissions:
- Follow agency-specific formatting requirements
- Include all required certifications and signatures
- Reference applicable permit numbers and regulations
- Maintain audit trail of changes

Your reports should enable informed decision-making and demonstrate due diligence."""

    async def run(
        self,
        context: AgentContext = None,
        report_type: ReportType = ReportType.GAP_ANALYSIS,
        facilities: List[Dict] = None,
        gaps: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a compliance report.
        
        Args:
            context: Shared agent context
            report_type: Type of report to generate
            facilities: Facilities to include
            gaps: Compliance gaps to include
            
        Returns:
            Dictionary with report content and file path
        """
        # Use context if available
        if context:
            facilities = facilities or context.facilities
            gaps = gaps or context.gaps
        
        logger.info(f"Generating {report_type.value} report")
        
        # Generate report based on type
        if report_type == ReportType.GAP_ANALYSIS:
            report = await self._generate_gap_analysis_report(facilities, gaps)
        elif report_type == ReportType.EXECUTIVE_SUMMARY:
            report = await self._generate_executive_summary(context, facilities, gaps)
        elif report_type == ReportType.REGULATORY_BRIEFING:
            regulations = context.regulations if context else []
            report = await self._generate_regulatory_briefing(regulations)
        elif report_type == ReportType.ANNUAL_CERTIFICATION:
            facility_id = kwargs.get("facility_id")
            report = await self._generate_annual_certification(facilities, facility_id)
        elif report_type == ReportType.EMISSIONS_INVENTORY:
            report = await self._generate_emissions_inventory(facilities)
        else:
            report = await self._generate_generic_report(report_type, context)
        
        # Save report to file
        file_path = await self._save_report(report)
        report["file_path"] = file_path
        
        # Log decision
        await self.log_decision(
            decision_type="report_generation",
            action_taken=f"Generated {report_type.value} report",
            reasoning=f"Report covers {len(facilities or [])} facilities, {len(gaps or [])} gaps",
            confidence=0.92,
            input_data={
                "report_type": report_type.value,
                "facility_count": len(facilities or []),
                "gap_count": len(gaps or []),
            },
            output_data={"file_path": file_path},
            facility_ids=[f.get("facility_id") for f in (facilities or [])],
        )
        
        return report
    
    async def _generate_gap_analysis_report(
        self,
        facilities: List[Dict],
        gaps: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a comprehensive gap analysis report."""
        
        # Group gaps by severity
        gaps_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }
        
        for gap in (gaps or []):
            severity = gap.get("severity", "medium")
            gaps_by_severity[severity].append(gap)
        
        # Group gaps by facility
        gaps_by_facility = {}
        for gap in (gaps or []):
            fac_id = gap.get("facility_id", "unknown")
            if fac_id not in gaps_by_facility:
                gaps_by_facility[fac_id] = []
            gaps_by_facility[fac_id].append(gap)
        
        # Calculate overall compliance score
        total_gaps = len(gaps or [])
        critical_count = len(gaps_by_severity["critical"])
        high_count = len(gaps_by_severity["high"])
        
        # Simple scoring: Start at 100, deduct for gaps
        score = max(0, 100 - (critical_count * 15) - (high_count * 8) - 
                   (len(gaps_by_severity["medium"]) * 3) - (len(gaps_by_severity["low"]) * 1))
        
        # Generate executive summary with LLM
        exec_summary = await self._generate_executive_summary_text(
            facilities, gaps, score, gaps_by_severity
        )
        
        # Build report sections
        sections = []
        
        # Section 1: Executive Summary
        sections.append({
            "title": "Executive Summary",
            "content": exec_summary,
            "order": 1,
        })
        
        # Section 2: Compliance Score
        sections.append({
            "title": "Overall Compliance Score",
            "content": self._format_compliance_score_section(score, gaps_by_severity),
            "order": 2,
        })
        
        # Section 3: Critical Gaps
        if gaps_by_severity["critical"]:
            sections.append({
                "title": "Critical Compliance Gaps",
                "content": self._format_gaps_section(gaps_by_severity["critical"]),
                "order": 3,
            })
        
        # Section 4: High Priority Gaps
        if gaps_by_severity["high"]:
            sections.append({
                "title": "High Priority Gaps",
                "content": self._format_gaps_section(gaps_by_severity["high"]),
                "order": 4,
            })
        
        # Section 5: Medium/Low Gaps
        other_gaps = gaps_by_severity["medium"] + gaps_by_severity["low"]
        if other_gaps:
            sections.append({
                "title": "Other Compliance Gaps",
                "content": self._format_gaps_section(other_gaps),
                "order": 5,
            })
        
        # Section 6: Facility-by-Facility Summary
        sections.append({
            "title": "Facility Summary",
            "content": self._format_facility_summary(facilities, gaps_by_facility),
            "order": 6,
        })
        
        # Section 7: Recommended Actions
        sections.append({
            "title": "Recommended Action Plan",
            "content": await self._generate_action_plan(gaps_by_severity),
            "order": 7,
        })
        
        # Section 8: Cost Estimate
        total_cost = sum(g.get("estimated_cost", 0) for g in (gaps or []))
        sections.append({
            "title": "Remediation Cost Estimate",
            "content": self._format_cost_estimate(gaps_by_severity, total_cost),
            "order": 8,
        })
        
        return {
            "report_type": ReportType.GAP_ANALYSIS.value,
            "title": f"Compliance Gap Analysis Report - {date.today().strftime('%B %Y')}",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": exec_summary,
            "compliance_score": score,
            "gap_summary": {
                "critical": critical_count,
                "high": high_count,
                "medium": len(gaps_by_severity["medium"]),
                "low": len(gaps_by_severity["low"]),
                "total": total_gaps,
            },
            "total_remediation_cost": total_cost,
            "sections": sections,
            "facilities_covered": [f.get("name") for f in (facilities or [])],
        }
    
    async def _generate_executive_summary_text(
        self,
        facilities: List[Dict],
        gaps: List[Dict],
        score: float,
        gaps_by_severity: Dict
    ) -> str:
        """Generate executive summary text using LLM."""
        
        prompt = f"""Write a concise executive summary for a compliance gap analysis report.

Data:
- Facilities analyzed: {len(facilities or [])}
- Overall compliance score: {score}/100
- Critical gaps: {len(gaps_by_severity['critical'])}
- High priority gaps: {len(gaps_by_severity['high'])}
- Medium gaps: {len(gaps_by_severity['medium'])}
- Low gaps: {len(gaps_by_severity['low'])}

Top Critical Issues:
{self._summarize_top_gaps(gaps_by_severity['critical'][:3])}

Write 2-3 paragraphs suitable for executive leadership covering:
1. Overall compliance posture
2. Key risks and their potential impact
3. Recommended immediate actions"""

        return await self.think(prompt)
    
    def _summarize_top_gaps(self, gaps: List[Dict]) -> str:
        """Summarize top gaps for prompt context."""
        if not gaps:
            return "No critical gaps identified."
        
        summaries = []
        for gap in gaps:
            summaries.append(f"- {gap.get('title')}: {gap.get('description', '')[:100]}...")
        return "\n".join(summaries)
    
    def _format_compliance_score_section(
        self,
        score: float,
        gaps_by_severity: Dict
    ) -> str:
        """Format the compliance score section."""
        
        if score >= 90:
            status = "Excellent"
            color = "green"
        elif score >= 75:
            status = "Good"
            color = "yellow"
        elif score >= 60:
            status = "Needs Improvement"
            color = "orange"
        else:
            status = "Critical Attention Required"
            color = "red"
        
        return f"""
## Compliance Score: {score}/100 ({status})

### Gap Distribution:
| Severity | Count | Impact |
|----------|-------|--------|
| Critical | {len(gaps_by_severity['critical'])} | Immediate enforcement risk |
| High | {len(gaps_by_severity['high'])} | Non-compliance within 90 days |
| Medium | {len(gaps_by_severity['medium'])} | Best practice deviations |
| Low | {len(gaps_by_severity['low'])} | Optimization opportunities |

### Score Trend:
Baseline assessment - trend tracking will begin with subsequent reviews.
"""
    
    def _format_gaps_section(self, gaps: List[Dict]) -> str:
        """Format a section of gaps."""
        
        lines = []
        for i, gap in enumerate(gaps, 1):
            lines.append(f"""
### {i}. {gap.get('title')}

**Severity:** {gap.get('severity', 'Unknown').upper()}
**Regulation:** {gap.get('regulation_id', 'N/A')}
**Deadline:** {gap.get('regulatory_deadline', 'Not specified')}
**Risk Score:** {gap.get('risk_score', 0):.2f}

**Description:**
{gap.get('description', 'No description provided.')}

**Recommended Action:**
{gap.get('recommended_action', 'No action specified.')}

**Estimated Cost:** ${gap.get('estimated_cost', 0):,.0f}
**Timeline:** {gap.get('timeline_days', 'TBD')} days

---
""")
        
        return "\n".join(lines)
    
    def _format_facility_summary(
        self,
        facilities: List[Dict],
        gaps_by_facility: Dict
    ) -> str:
        """Format facility-by-facility summary."""
        
        lines = ["| Facility | Type | State | Gaps | Critical | Score |",
                 "|----------|------|-------|------|----------|-------|"]
        
        for facility in (facilities or []):
            fac_id = facility.get("facility_id", "")
            fac_gaps = gaps_by_facility.get(fac_id, [])
            critical_count = len([g for g in fac_gaps if g.get("severity") == "critical"])
            
            # Calculate facility score
            fac_score = max(0, 100 - (critical_count * 15) - 
                          (len([g for g in fac_gaps if g.get("severity") == "high"]) * 8))
            
            lines.append(
                f"| {facility.get('name', 'Unknown')} | "
                f"{facility.get('facility_type', 'N/A')} | "
                f"{facility.get('state', 'N/A')} | "
                f"{len(fac_gaps)} | "
                f"{critical_count} | "
                f"{fac_score}/100 |"
            )
        
        return "\n".join(lines)
    
    async def _generate_action_plan(self, gaps_by_severity: Dict) -> str:
        """Generate recommended action plan."""
        
        prompt = f"""Create a prioritized action plan based on these compliance gaps:

Critical ({len(gaps_by_severity['critical'])} items):
{self._summarize_top_gaps(gaps_by_severity['critical'])}

High Priority ({len(gaps_by_severity['high'])} items):
{self._summarize_top_gaps(gaps_by_severity['high'][:5])}

Provide:
1. Immediate actions (next 30 days)
2. Short-term actions (30-90 days)
3. Medium-term actions (90-180 days)
4. Ongoing compliance activities

Format as a clear action plan with responsible parties and milestones."""

        return await self.think(prompt)
    
    def _format_cost_estimate(
        self,
        gaps_by_severity: Dict,
        total_cost: float
    ) -> str:
        """Format cost estimate section."""
        
        cost_by_severity = {}
        for severity, gaps in gaps_by_severity.items():
            cost_by_severity[severity] = sum(g.get("estimated_cost", 0) for g in gaps)
        
        return f"""
## Total Estimated Remediation Cost: ${total_cost:,.0f}

### Cost Breakdown by Priority:
| Priority | Gap Count | Estimated Cost |
|----------|-----------|----------------|
| Critical | {len(gaps_by_severity['critical'])} | ${cost_by_severity['critical']:,.0f} |
| High | {len(gaps_by_severity['high'])} | ${cost_by_severity['high']:,.0f} |
| Medium | {len(gaps_by_severity['medium'])} | ${cost_by_severity['medium']:,.0f} |
| Low | {len(gaps_by_severity['low'])} | ${cost_by_severity['low']:,.0f} |

*Note: Costs are estimates based on industry averages and may vary based on 
specific facility conditions, contractor availability, and regulatory requirements.*

### Potential Non-Compliance Costs:
Failure to address identified gaps could result in:
- EPA penalties up to $64,618 per day per violation (2024 rates)
- State penalties (varies by jurisdiction)
- Consent decree requirements
- Supplemental environmental projects
- Reputational damage
"""
    
    async def _generate_executive_summary(
        self,
        context: AgentContext,
        facilities: List[Dict],
        gaps: List[Dict]
    ) -> Dict[str, Any]:
        """Generate executive-level summary report."""
        
        summary_data = context.get_summary() if context else {}
        
        prompt = f"""Create a one-page executive summary of environmental compliance status:

Analysis Period: {date.today().strftime('%B %Y')}
Facilities: {len(facilities or [])}
Regulations Reviewed: {summary_data.get('regulations_count', 'N/A')}
Total Gaps Identified: {len(gaps or [])}
Critical Gaps: {len([g for g in (gaps or []) if g.get('severity') == 'critical'])}

Write for C-suite executives. Include:
1. Compliance posture summary (2 sentences)
2. Key risks (bullet points)
3. Financial exposure estimate
4. Recommended board actions"""

        content = await self.think(prompt)
        
        return {
            "report_type": ReportType.EXECUTIVE_SUMMARY.value,
            "title": f"Environmental Compliance Executive Summary - {date.today().strftime('%B %Y')}",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": content,
            "sections": [{"title": "Executive Summary", "content": content, "order": 1}],
        }
    
    async def _generate_regulatory_briefing(
        self,
        regulations: List[Dict]
    ) -> Dict[str, Any]:
        """Generate regulatory change briefing."""
        
        new_regs = [r for r in regulations if r.get("status") in ["proposed", "final"]]
        
        prompt = f"""Create a regulatory briefing document for Oil & Gas compliance team:

New/Changed Regulations ({len(new_regs)}):
{json.dumps(new_regs[:5], indent=2, default=str)}

For each regulation, provide:
1. What changed
2. Who is affected
3. Key compliance dates
4. Action items"""

        content = await self.think(prompt)
        
        return {
            "report_type": ReportType.REGULATORY_BRIEFING.value,
            "title": f"Regulatory Update Briefing - {date.today().strftime('%B %d, %Y')}",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": f"Summary of {len(new_regs)} regulatory changes affecting Oil & Gas operations.",
            "sections": [{"title": "Regulatory Changes", "content": content, "order": 1}],
            "regulations_covered": [r.get("citation") for r in new_regs],
        }
    
    async def _generate_annual_certification(
        self,
        facilities: List[Dict],
        facility_id: str = None
    ) -> Dict[str, Any]:
        """Generate Title V annual compliance certification."""
        
        # Find specific facility or use first
        facility = None
        if facility_id:
            facility = next((f for f in (facilities or []) if f.get("facility_id") == facility_id), None)
        if not facility and facilities:
            facility = facilities[0]
        
        if not facility:
            return {"error": "No facility specified for certification"}
        
        prompt = f"""Draft a Title V Annual Compliance Certification for:

Facility: {facility.get('name')}
Location: {facility.get('county')}, {facility.get('state')}
Permit Number: {facility.get('metadata', {}).get('permits', [{}])[0].get('permit_number', 'TBD')}

Include standard certification language for:
1. Compliance status with permit conditions
2. Monitoring and recordkeeping compliance
3. Reporting compliance
4. Deviations and corrective actions
5. Responsible official certification statement

Use formal regulatory language appropriate for EPA submission."""

        content = await self.think(prompt)
        
        return {
            "report_type": ReportType.ANNUAL_CERTIFICATION.value,
            "title": f"Title V Annual Compliance Certification - {facility.get('name')}",
            "generated_at": datetime.utcnow().isoformat(),
            "facility_id": facility.get("facility_id"),
            "executive_summary": f"Annual compliance certification for {facility.get('name')}",
            "sections": [{"title": "Certification", "content": content, "order": 1}],
        }
    
    async def _generate_emissions_inventory(
        self,
        facilities: List[Dict]
    ) -> Dict[str, Any]:
        """Generate emissions inventory report."""
        
        # Aggregate emissions across facilities
        total_emissions = {}
        for facility in (facilities or []):
            fac_emissions = facility.get("metadata", {}).get("total_potential_emissions_tpy", {})
            for pollutant, amount in fac_emissions.items():
                total_emissions[pollutant] = total_emissions.get(pollutant, 0) + amount
        
        return {
            "report_type": ReportType.EMISSIONS_INVENTORY.value,
            "title": f"Emissions Inventory Report - {date.today().year}",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": f"Emissions inventory for {len(facilities or [])} facilities.",
            "total_emissions": total_emissions,
            "sections": [
                {
                    "title": "Emissions Summary",
                    "content": self._format_emissions_table(facilities, total_emissions),
                    "order": 1
                }
            ],
        }
    
    def _format_emissions_table(
        self,
        facilities: List[Dict],
        total_emissions: Dict
    ) -> str:
        """Format emissions inventory table."""
        
        lines = ["## Facility Emissions (tons per year)\n"]
        lines.append("| Facility | VOC | NOx | CO | HAP | GHG (CO2e) |")
        lines.append("|----------|-----|-----|----|----|------------|")
        
        for facility in (facilities or []):
            emissions = facility.get("metadata", {}).get("total_potential_emissions_tpy", {})
            lines.append(
                f"| {facility.get('name', 'Unknown')} | "
                f"{emissions.get('VOC', 0):.1f} | "
                f"{emissions.get('NOx', 0):.1f} | "
                f"{emissions.get('CO', 0):.1f} | "
                f"{emissions.get('HAP', 0):.1f} | "
                f"{emissions.get('CO2e', 0):.0f} |"
            )
        
        lines.append("")
        lines.append("### Total Emissions")
        for pollutant, amount in total_emissions.items():
            lines.append(f"- **{pollutant}:** {amount:.1f} tpy")
        
        return "\n".join(lines)
    
    async def _generate_generic_report(
        self,
        report_type: ReportType,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Generate a generic report type."""
        
        return {
            "report_type": report_type.value,
            "title": f"{report_type.value.replace('_', ' ').title()} Report",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": f"Report type {report_type.value} generated.",
            "sections": [],
        }
    
    async def _save_report(self, report: Dict) -> str:
        """Save report to file."""
        
        output_dir = Path(settings.agent.report_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_type = report.get("report_type", "report")
        filename = f"{report_type}_{timestamp}.json"
        
        file_path = output_dir / filename
        
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Saved report to {file_path}")
        
        # Also save markdown version
        md_path = output_dir / filename.replace(".json", ".md")
        await self._save_markdown(report, md_path)
        
        return str(file_path)
    
    async def _save_markdown(self, report: Dict, path: Path):
        """Save report as markdown."""
        
        lines = [
            f"# {report.get('title', 'Compliance Report')}",
            f"\n*Generated: {report.get('generated_at', datetime.utcnow().isoformat())}*\n",
            "---\n",
        ]
        
        if report.get("executive_summary"):
            lines.append("## Executive Summary\n")
            lines.append(report["executive_summary"])
            lines.append("\n---\n")
        
        for section in report.get("sections", []):
            lines.append(f"## {section.get('title', 'Section')}\n")
            lines.append(section.get("content", ""))
            lines.append("\n")
        
        with open(path, "w") as f:
            f.write("\n".join(lines))
        
        logger.info(f"Saved markdown report to {path}")
