#!/usr/bin/env python3
"""
EnviroComply Demo Script
========================
Interactive demonstration of the AI-powered environmental compliance system.

This script walks through all major features:
1. Regulatory monitoring and change detection
2. Facility impact assessment
3. Compliance gap identification
4. Report generation
5. Agent decision reasoning

Usage:
    python demo.py              # Run full interactive demo
    python demo.py --quick      # Quick demo (skip waits)
    python demo.py --section 2  # Run specific section only
"""

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import sys

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for enhanced output: pip install rich")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


class DemoRunner:
    """Interactive demo runner for EnviroComply."""
    
    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
        self.console = Console() if RICH_AVAILABLE else None
        
    def print_header(self, title: str):
        """Print a section header."""
        if self.console:
            self.console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))
        else:
            print(f"\n{'='*60}")
            print(f"  {title}")
            print(f"{'='*60}\n")
    
    def print_step(self, step: str, description: str):
        """Print a step description."""
        if self.console:
            self.console.print(f"\n[bold green]► {step}[/bold green]")
            self.console.print(f"  [dim]{description}[/dim]\n")
        else:
            print(f"\n► {step}")
            print(f"  {description}\n")
    
    def print_result(self, data: dict, title: str = "Result"):
        """Print formatted result data."""
        if self.console:
            table = Table(title=title, show_header=True)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)[:100] + "..."
                table.add_row(str(key), str(value))
            
            self.console.print(table)
        else:
            print(f"\n{title}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
    
    def print_gap(self, gap: dict):
        """Print a compliance gap with severity coloring."""
        severity_colors = {
            "critical": "red",
            "high": "yellow", 
            "medium": "blue",
            "low": "green"
        }
        
        severity = gap.get("severity", "medium")
        color = severity_colors.get(severity, "white")
        
        if self.console:
            self.console.print(Panel(
                f"[bold]{gap.get('title', 'Unnamed Gap')}[/bold]\n\n"
                f"[dim]Facility:[/dim] {gap.get('facility_name', 'N/A')}\n"
                f"[dim]Regulation:[/dim] {gap.get('regulation_id', 'N/A')}\n"
                f"[dim]Description:[/dim] {gap.get('description', 'N/A')[:200]}...\n\n"
                f"[dim]Recommended Action:[/dim] {gap.get('recommended_action', 'N/A')}\n"
                f"[dim]Estimated Cost:[/dim] ${gap.get('estimated_cost', 0):,}",
                title=f"[{color}]{severity.upper()}[/{color}] Gap",
                border_style=color
            ))
        else:
            print(f"\n[{severity.upper()}] {gap.get('title', 'Unnamed Gap')}")
            print(f"  Facility: {gap.get('facility_name', 'N/A')}")
            print(f"  Description: {gap.get('description', 'N/A')[:100]}...")
    
    def wait(self, seconds: float = 1.5):
        """Wait for effect (skipped in quick mode)."""
        if not self.quick_mode:
            import time
            time.sleep(seconds)
    
    async def run_section_1(self):
        """Section 1: Regulatory Monitoring."""
        self.print_header("Section 1: Regulatory Monitoring")
        
        self.print_step(
            "Initialize Regulation Monitor Agent",
            "The agent monitors EPA Federal Register and state regulatory sources"
        )
        
        # Show agent configuration
        agent_config = {
            "agent_type": "regulation_monitor",
            "monitored_sources": ["EPA Federal Register", "TCEQ", "ODEQ", "WDEQ"],
            "cfr_parts": ["40 CFR 60 (NSPS)", "40 CFR 63 (NESHAP)", "40 CFR 98 (GHG)"],
            "keywords": ["oil", "gas", "methane", "VOC", "wellsite", "compressor"],
            "lookback_days": 30
        }
        self.print_result(agent_config, "Agent Configuration")
        self.wait()
        
        self.print_step(
            "Scanning Federal Register",
            "Searching for Oil & Gas related regulatory changes..."
        )
        
        # Simulate scanning with progress
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Scanning Federal Register...", total=None)
                await asyncio.sleep(2 if not self.quick_mode else 0.5)
                progress.update(task, description="Analyzing document relevance...")
                await asyncio.sleep(1.5 if not self.quick_mode else 0.3)
                progress.update(task, description="Extracting requirements...")
                await asyncio.sleep(1 if not self.quick_mode else 0.2)
        
        # Show discovered regulations
        new_regulations = [
            {
                "citation": "40 CFR 60 Subpart OOOOb",
                "title": "NSPS for Crude Oil and Natural Gas - GHG/VOC Standards",
                "effective_date": "2024-05-07",
                "key_change": "Zero-emission pneumatics required at new wellsites",
                "deadline": "2025-05-07",
                "applicability": "All new/modified O&G facilities"
            },
            {
                "citation": "40 CFR 60.5397a Amendment",
                "title": "Enhanced LDAR Requirements",
                "effective_date": "2024-12-01",
                "key_change": "Quarterly OGI surveys now required for all affected facilities",
                "deadline": "2025-03-01",
                "applicability": "Wellsites and compressor stations"
            }
        ]
        
        if self.console:
            table = Table(title="Discovered Regulatory Changes", show_header=True)
            table.add_column("Citation", style="cyan")
            table.add_column("Key Change", style="white")
            table.add_column("Deadline", style="yellow")
            
            for reg in new_regulations:
                table.add_row(
                    reg["citation"],
                    reg["key_change"][:50] + "...",
                    reg["deadline"]
                )
            self.console.print(table)
        else:
            for reg in new_regulations:
                print(f"\n{reg['citation']}: {reg['title']}")
                print(f"  Key Change: {reg['key_change']}")
        
        self.wait()
        
        # Show agent reasoning
        self.print_step(
            "Agent Reasoning",
            "The agent explains why these regulations are relevant"
        )
        
        reasoning = """
**Regulation Monitor Agent Analysis**

I identified 40 CFR 60 Subpart OOOOb as highly relevant because:

1. **Keyword Match**: Document contains "natural gas", "wellsite", "pneumatic controller", 
   "methane" - all high-priority O&G terms
   
2. **Applicability**: Affects crude oil and natural gas production facilities - 
   matches all facility types in our monitoring scope
   
3. **Timeline**: Compliance deadline of May 2025 is within our alert threshold (180 days)

4. **Impact Assessment**: This rule requires ZERO-EMISSION pneumatic controllers at new sites,
   which represents a significant change from the current low-bleed standard (< 6 scfh)

**Recommended Actions:**
- Flag all facilities with pneumatic controllers built after May 2024
- Estimate replacement costs for affected equipment
- Schedule engineering review for compliance pathways
        """
        
        if self.console:
            self.console.print(Markdown(reasoning))
        else:
            print(reasoning)
        
        self.wait(2)
        return new_regulations
    
    async def run_section_2(self, regulations: list = None):
        """Section 2: Facility Impact Assessment."""
        self.print_header("Section 2: Facility Impact Assessment")
        
        self.print_step(
            "Load Facility Portfolio",
            "Analyzing 3 Oil & Gas facilities across TX, ND, and WY"
        )
        
        facilities = [
            {
                "id": "permian-001",
                "name": "Permian Basin Production Facility 1",
                "type": "Production",
                "state": "TX",
                "major_source": False,
                "emission_sources": 12,
                "pneumatic_controllers": 8,
                "storage_vessels": 3
            },
            {
                "id": "bakken-001",
                "name": "Bakken Gathering Station",
                "type": "Gathering",
                "state": "ND",
                "major_source": True,
                "emission_sources": 24,
                "pneumatic_controllers": 15,
                "storage_vessels": 6
            },
            {
                "id": "wyoming-001",
                "name": "Wyoming Gas Processing Plant",
                "type": "Processing",
                "state": "WY",
                "major_source": True,
                "emission_sources": 45,
                "pneumatic_controllers": 22,
                "storage_vessels": 12
            }
        ]
        
        if self.console:
            table = Table(title="Facility Portfolio", show_header=True)
            table.add_column("Facility", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("State", style="white")
            table.add_column("Major Source", style="yellow")
            table.add_column("Emission Sources", style="green")
            
            for fac in facilities:
                table.add_row(
                    fac["name"][:30],
                    fac["type"],
                    fac["state"],
                    "Yes" if fac["major_source"] else "No",
                    str(fac["emission_sources"])
                )
            self.console.print(table)
        
        self.wait()
        
        self.print_step(
            "Running Impact Assessment",
            "Mapping regulations to facilities and calculating compliance burden..."
        )
        
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                for fac in facilities:
                    task = progress.add_task(f"Assessing {fac['name'][:25]}...", total=None)
                    await asyncio.sleep(1.5 if not self.quick_mode else 0.3)
                    progress.remove_task(task)
        
        # Impact assessment results
        assessments = [
            {
                "facility": "Permian Basin Production Facility 1",
                "impact_score": 72,
                "regulations_applicable": 4,
                "equipment_affected": 11,
                "estimated_cost": 45000,
                "priority": "HIGH",
                "key_issues": [
                    "8 high-bleed pneumatic controllers require replacement",
                    "LDAR survey frequency increase from semi-annual to quarterly",
                    "Storage vessel control upgrade needed"
                ]
            },
            {
                "facility": "Bakken Gathering Station",
                "impact_score": 85,
                "regulations_applicable": 6,
                "equipment_affected": 21,
                "estimated_cost": 125000,
                "priority": "CRITICAL",
                "key_issues": [
                    "Major source triggers additional NESHAP requirements",
                    "15 pneumatic controllers need zero-emission upgrade",
                    "Glycol dehydrator lacks required HAP controls",
                    "Title V permit modification required"
                ]
            },
            {
                "facility": "Wyoming Gas Processing Plant",
                "impact_score": 68,
                "regulations_applicable": 5,
                "equipment_affected": 18,
                "estimated_cost": 95000,
                "priority": "HIGH",
                "key_issues": [
                    "Permit expiring in 75 days - renewal urgent",
                    "Compressor seal monitoring enhancement needed",
                    "GHG reporting methodology documentation gaps"
                ]
            }
        ]
        
        if self.console:
            for assessment in assessments:
                color = "red" if assessment["priority"] == "CRITICAL" else "yellow"
                self.console.print(Panel(
                    f"[bold]Impact Score:[/bold] {assessment['impact_score']}/100\n"
                    f"[bold]Regulations Applicable:[/bold] {assessment['regulations_applicable']}\n"
                    f"[bold]Equipment Affected:[/bold] {assessment['equipment_affected']}\n"
                    f"[bold]Estimated Cost:[/bold] ${assessment['estimated_cost']:,}\n\n"
                    f"[bold]Key Issues:[/bold]\n" + 
                    "\n".join(f"  • {issue}" for issue in assessment['key_issues']),
                    title=f"[{color}]{assessment['facility']} - {assessment['priority']}[/{color}]",
                    border_style=color
                ))
                self.wait(0.5)
        
        total_cost = sum(a["estimated_cost"] for a in assessments)
        self.print_step(
            "Impact Summary",
            f"Total estimated compliance cost: ${total_cost:,}"
        )
        
        return assessments
    
    async def run_section_3(self, assessments: list = None):
        """Section 3: Compliance Gap Analysis."""
        self.print_header("Section 3: Compliance Gap Analysis")
        
        self.print_step(
            "Initialize Gap Analyzer Agent",
            "Identifying specific compliance gaps with remediation recommendations"
        )
        
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Analyzing regulatory requirements...", total=None)
                await asyncio.sleep(1 if not self.quick_mode else 0.2)
                progress.update(task, description="Comparing against facility data...")
                await asyncio.sleep(1 if not self.quick_mode else 0.2)
                progress.update(task, description="Calculating risk scores...")
                await asyncio.sleep(0.5 if not self.quick_mode else 0.1)
        
        # Detailed gaps
        gaps = [
            {
                "id": "GAP-001",
                "title": "LDAR Survey Overdue - Permian Basin",
                "facility_name": "Permian Basin Production Facility 1",
                "severity": "critical",
                "regulation_id": "40 CFR 60.5397a",
                "description": "Last LDAR survey was conducted 95 days ago. Under NSPS OOOOa, "
                              "quarterly optical gas imaging (OGI) surveys are required for wellhead "
                              "and compressor components. Facility is 5 days past the 90-day deadline.",
                "recommended_action": "Conduct LDAR survey immediately using EPA Method 21 or OGI. "
                                     "Schedule remaining quarterly surveys for 2025. Consider hiring "
                                     "third-party LDAR contractor for compliance assurance.",
                "estimated_cost": 5000,
                "risk_score": 0.95,
                "potential_fine": 64618,  # Per day per violation
                "deadline": "2025-01-10"
            },
            {
                "id": "GAP-002",
                "title": "High-Bleed Pneumatic Controllers",
                "facility_name": "Bakken Gathering Station",
                "severity": "high",
                "regulation_id": "40 CFR 60.5390a",
                "description": "Found 15 high-bleed pneumatic controllers (>6 scfh bleed rate) at the "
                              "gathering station. NSPS OOOOa requires low-bleed controllers (<6 scfh) "
                              "or zero-emission alternatives. OOOOb will require zero-emission for new sites.",
                "recommended_action": "Replace high-bleed controllers with instrument air or electric "
                                     "actuators. Prioritize continuous-bleed devices first. Budget for "
                                     "approximately $500-2000 per controller replacement.",
                "estimated_cost": 22500,
                "risk_score": 0.75,
                "potential_fine": 25000,
                "deadline": "2025-03-01"
            },
            {
                "id": "GAP-003",
                "title": "Title V Permit Expiring",
                "facility_name": "Wyoming Gas Processing Plant",
                "severity": "high",
                "regulation_id": "Title V - 40 CFR 70",
                "description": "Title V operating permit WY-TV-2020-005 expires on March 15, 2025. "
                              "Wyoming DEQ requires permit renewal applications 6 months before expiration. "
                              "Application is past due and facility risks operating without valid permit.",
                "recommended_action": "Submit permit renewal application to WDEQ immediately. Include "
                                     "updated emissions inventory, compliance certifications, and any "
                                     "permit modification requests. Expect 3-6 month processing time.",
                "estimated_cost": 15000,
                "risk_score": 0.70,
                "potential_fine": 50000,
                "deadline": "2025-03-15"
            },
            {
                "id": "GAP-004",
                "title": "Uncontrolled Glycol Dehydrator",
                "facility_name": "Bakken Gathering Station",
                "severity": "medium",
                "regulation_id": "40 CFR 63 Subpart HH",
                "description": "Glycol dehydrator at the gathering station lacks HAP emission controls. "
                              "As a major source, NESHAP HH requires 95% HAP reduction from glycol "
                              "dehydrators with actual annual average benzene emissions >1 Mg/yr.",
                "recommended_action": "Install condenser on regenerator vent or route to combustion device. "
                                     "Alternatives include flash tank separator or BTEX recovery unit. "
                                     "Conduct benzene emissions calculation to confirm applicability.",
                "estimated_cost": 50000,
                "risk_score": 0.55,
                "potential_fine": 37500,
                "deadline": "2025-06-01"
            },
            {
                "id": "GAP-005",
                "title": "GHG Reporting Documentation Gap",
                "facility_name": "Wyoming Gas Processing Plant",
                "severity": "low",
                "regulation_id": "40 CFR 98 Subpart W",
                "description": "Missing calculation methodology documentation for several emission sources "
                              "in the Subpart W GHG report. EPA requires facilities to document the methods "
                              "used to calculate emissions for each source category.",
                "recommended_action": "Document emission calculation methods for all sources. Create "
                                     "standard operating procedures for annual GHG calculations. "
                                     "Review e-GGRT submission for completeness before March 31 deadline.",
                "estimated_cost": 2500,
                "risk_score": 0.25,
                "potential_fine": 10000,
                "deadline": "2025-03-31"
            }
        ]
        
        # Display gaps
        for gap in gaps:
            self.print_gap(gap)
            self.wait(0.5)
        
        # Gap summary
        self.print_step("Gap Summary", "Compliance gap analysis complete")
        
        summary = {
            "total_gaps": len(gaps),
            "critical": len([g for g in gaps if g["severity"] == "critical"]),
            "high": len([g for g in gaps if g["severity"] == "high"]),
            "medium": len([g for g in gaps if g["severity"] == "medium"]),
            "low": len([g for g in gaps if g["severity"] == "low"]),
            "total_remediation_cost": sum(g["estimated_cost"] for g in gaps),
            "total_potential_fines": sum(g["potential_fine"] for g in gaps)
        }
        
        if self.console:
            table = Table(title="Gap Analysis Summary", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Total Gaps Identified", str(summary["total_gaps"]))
            table.add_row("[red]Critical[/red]", str(summary["critical"]))
            table.add_row("[yellow]High[/yellow]", str(summary["high"]))
            table.add_row("[blue]Medium[/blue]", str(summary["medium"]))
            table.add_row("[green]Low[/green]", str(summary["low"]))
            table.add_row("Total Remediation Cost", f"${summary['total_remediation_cost']:,}")
            table.add_row("Potential Fine Exposure", f"${summary['total_potential_fines']:,}")
            
            self.console.print(table)
        
        return gaps
    
    async def run_section_4(self, gaps: list = None):
        """Section 4: Report Generation."""
        self.print_header("Section 4: Report Generation")
        
        self.print_step(
            "Initialize Report Generator Agent",
            "Creating compliance reports for different stakeholders"
        )
        
        report_types = [
            ("Gap Analysis Report", "Detailed technical report for compliance team"),
            ("Executive Summary", "High-level overview for C-suite leadership"),
            ("Regulatory Briefing", "Summary of recent regulatory changes"),
        ]
        
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                for report_name, desc in report_types:
                    task = progress.add_task(f"Generating {report_name}...", total=None)
                    await asyncio.sleep(1.5 if not self.quick_mode else 0.3)
                    progress.remove_task(task)
        
        # Sample executive summary
        executive_summary = """
# Environmental Compliance Executive Summary
## Demo Oil & Gas Co. - January 2025

### Compliance Posture: NEEDS ATTENTION (Score: 72/100)

**Key Findings:**
- 5 compliance gaps identified across 3 facilities
- 1 CRITICAL gap requiring immediate action (LDAR survey overdue)
- 2 HIGH priority gaps with near-term deadlines
- Total remediation investment needed: $95,000
- Potential fine exposure if unaddressed: $187,118

**Immediate Actions Required:**
1. ⚠️ Conduct LDAR survey at Permian Basin facility (OVERDUE)
2. 📋 Submit Title V permit renewal for Wyoming plant
3. 🔧 Begin pneumatic controller replacement program

**Financial Impact:**
| Category | Amount |
|----------|--------|
| Remediation Costs | $95,000 |
| Potential Fines | $187,118 |
| ROI of Compliance | 97% risk reduction |

**Recommendation:** Authorize immediate remediation budget of $100,000 
to address critical and high-priority gaps before Q2 2025.
        """
        
        self.print_step("Executive Summary Generated", "Report ready for leadership review")
        
        if self.console:
            self.console.print(Markdown(executive_summary))
        else:
            print(executive_summary)
        
        self.wait(2)
        
        # Show saved reports
        reports = [
            {
                "filename": "gap_analysis_20250107.md",
                "type": "Gap Analysis",
                "pages": 12,
                "generated": datetime.now().isoformat()
            },
            {
                "filename": "executive_summary_20250107.md", 
                "type": "Executive Summary",
                "pages": 2,
                "generated": datetime.now().isoformat()
            },
            {
                "filename": "regulatory_briefing_20250107.md",
                "type": "Regulatory Briefing",
                "pages": 5,
                "generated": datetime.now().isoformat()
            }
        ]
        
        if self.console:
            table = Table(title="Generated Reports", show_header=True)
            table.add_column("Filename", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("Pages", style="green")
            
            for report in reports:
                table.add_row(report["filename"], report["type"], str(report["pages"]))
            
            self.console.print(table)
        
        return reports
    
    async def run_section_5(self):
        """Section 5: Agent Learning & Decision Audit."""
        self.print_header("Section 5: Agent Learning & Decision Audit")
        
        self.print_step(
            "Agent Decision Transparency",
            "All agent decisions are logged for audit and continuous learning"
        )
        
        decisions = [
            {
                "agent": "Regulation Monitor",
                "decision": "Flag OOOOb as HIGH priority",
                "reasoning": "Contains 5+ O&G keywords, affects all facility types, deadline within 180 days",
                "confidence": 0.95,
                "timestamp": "2025-01-07T10:15:32Z"
            },
            {
                "agent": "Impact Assessor", 
                "decision": "Classify Bakken station as CRITICAL impact",
                "reasoning": "Major source status triggers NESHAP, 15 non-compliant pneumatics, Title V implications",
                "confidence": 0.88,
                "timestamp": "2025-01-07T10:16:45Z"
            },
            {
                "agent": "Gap Analyzer",
                "decision": "Assign CRITICAL severity to LDAR gap",
                "reasoning": "Survey is 5 days overdue, direct violation of 60.5397a, high enforcement priority",
                "confidence": 0.97,
                "timestamp": "2025-01-07T10:17:58Z"
            },
            {
                "agent": "Gap Analyzer",
                "decision": "Estimate $22,500 for pneumatic replacement",
                "reasoning": "15 controllers × $1,500 avg replacement cost, based on similar past remediations",
                "confidence": 0.72,
                "timestamp": "2025-01-07T10:18:12Z"
            }
        ]
        
        if self.console:
            for decision in decisions:
                color = "green" if decision["confidence"] > 0.8 else "yellow"
                self.console.print(Panel(
                    f"[bold]Decision:[/bold] {decision['decision']}\n\n"
                    f"[bold]Reasoning:[/bold] {decision['reasoning']}\n\n"
                    f"[bold]Confidence:[/bold] [{color}]{decision['confidence']*100:.0f}%[/{color}]",
                    title=f"[cyan]{decision['agent']}[/cyan]",
                    subtitle=decision["timestamp"]
                ))
                self.wait(0.3)
        
        self.print_step(
            "Continuous Learning",
            "Agents improve by learning from past decisions and outcomes"
        )
        
        learning_stats = {
            "total_decisions_logged": 1247,
            "accuracy_improvement": "+12% over 6 months",
            "cost_estimation_accuracy": "±15% vs actual",
            "false_positive_rate": "3.2%",
            "user_feedback_incorporated": 89
        }
        
        self.print_result(learning_stats, "Learning Metrics")
        
    async def run_full_demo(self):
        """Run the complete demonstration."""
        if self.console:
            self.console.print(Panel(
                "[bold blue]EnviroComply[/bold blue]\n"
                "[dim]AI-Powered Environmental Compliance for Oil & Gas[/dim]\n\n"
                "This demo showcases the multi-agent system for:\n"
                "• Regulatory monitoring and change detection\n"
                "• Facility impact assessment\n"
                "• Compliance gap identification\n"
                "• Automated report generation\n"
                "• Transparent decision reasoning",
                title="🌿 Welcome to the Demo",
                expand=False
            ))
        else:
            print("\n" + "="*60)
            print("  EnviroComply Demo")
            print("  AI-Powered Environmental Compliance for Oil & Gas")
            print("="*60 + "\n")
        
        self.wait(2)
        
        # Run all sections
        regulations = await self.run_section_1()
        assessments = await self.run_section_2(regulations)
        gaps = await self.run_section_3(assessments)
        reports = await self.run_section_4(gaps)
        await self.run_section_5()
        
        # Final summary
        self.print_header("Demo Complete")
        
        if self.console:
            self.console.print(Panel(
                "[bold green]✓ Regulatory Monitoring[/bold green] - 2 relevant changes identified\n"
                "[bold green]✓ Impact Assessment[/bold green] - 3 facilities analyzed\n"
                "[bold green]✓ Gap Analysis[/bold green] - 5 compliance gaps found\n"
                "[bold green]✓ Report Generation[/bold green] - 3 reports created\n"
                "[bold green]✓ Decision Audit[/bold green] - Full transparency maintained\n\n"
                "[bold]Total Value Delivered:[/bold]\n"
                "• $95,000 in remediation actions identified\n"
                "• $187,118 in potential fines avoided\n"
                "• 4+ hours of manual analysis automated",
                title="🎉 Demo Summary",
                border_style="green"
            ))
        
        print("\nThank you for exploring EnviroComply!")
        print("For questions: github.com/demo/enviro-comply\n")


async def main():
    parser = argparse.ArgumentParser(description="EnviroComply Interactive Demo")
    parser.add_argument("--quick", action="store_true", help="Run in quick mode (skip delays)")
    parser.add_argument("--section", type=int, choices=[1, 2, 3, 4, 5], help="Run specific section only")
    
    args = parser.parse_args()
    
    demo = DemoRunner(quick_mode=args.quick)
    
    if args.section:
        section_methods = {
            1: demo.run_section_1,
            2: demo.run_section_2,
            3: demo.run_section_3,
            4: demo.run_section_4,
            5: demo.run_section_5,
        }
        await section_methods[args.section]()
    else:
        await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())
