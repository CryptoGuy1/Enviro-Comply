#!/usr/bin/env python3
"""
EnviroComply - Main Entry Point
===============================
AI-powered environmental compliance management for Oil & Gas.

Usage:
    # Run API server
    python main.py serve
    
    # Run full compliance analysis
    python main.py analyze --mode full
    
    # Monitor for regulatory changes
    python main.py monitor
    
    # Generate report
    python main.py report --type gap_analysis
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from core.models import ReportType


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )
    logger.add(
        "logs/enviro_comply_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
    )


async def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server."""
    import uvicorn
    
    logger.info(f"Starting EnviroComply API server on {host}:{port}")
    
    config = uvicorn.Config(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_analysis(mode: str = "full", facility_ids: list = None):
    """Run compliance analysis."""
    from agents import EnviroComplyCrew
    
    logger.info(f"Running compliance analysis in '{mode}' mode")
    
    crew = EnviroComplyCrew()
    
    try:
        await crew.initialize()
        
        # Load facilities
        facilities = await crew._load_facilities(facility_ids)
        logger.info(f"Loaded {len(facilities)} facilities")
        
        if mode == "full":
            results = await crew.run_full_analysis(
                facilities=facilities,
                report_types=[ReportType.GAP_ANALYSIS, ReportType.EXECUTIVE_SUMMARY],
            )
        elif mode == "monitor":
            results = await crew.regulation_monitor.run(context=crew.context)
        elif mode == "assess":
            results = await crew.impact_assessor.run(
                context=crew.context,
                facilities=facilities,
            )
        elif mode == "gaps":
            impact = await crew.impact_assessor.run(
                context=crew.context,
                facilities=facilities,
            )
            results = await crew.gap_analyzer.run(
                context=crew.context,
                facilities=facilities,
                impact_assessments=impact.get("assessments", []),
            )
        else:
            logger.error(f"Unknown mode: {mode}")
            return
        
        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        
        if isinstance(results, dict):
            for key, value in results.items():
                if key not in ["phases", "reports_generated", "gaps"]:
                    print(f"{key}: {value}")
        
        print("=" * 60 + "\n")
        
    finally:
        await crew.cleanup()


async def run_monitor(lookback_days: int = 30):
    """Run regulatory monitoring."""
    from agents import EnviroComplyCrew
    
    logger.info(f"Scanning for regulatory changes (last {lookback_days} days)")
    
    crew = EnviroComplyCrew()
    
    try:
        await crew.initialize()
        
        results = await crew.regulation_monitor.run(
            context=crew.context,
            lookback_days=lookback_days,
        )
        
        # Print results
        print("\n" + "=" * 60)
        print("REGULATORY SCAN RESULTS")
        print("=" * 60)
        print(f"New Regulations: {len(results.get('new_regulations', []))}")
        print(f"Amended Regulations: {len(results.get('amended_regulations', []))}")
        print(f"Alerts: {len(results.get('alerts', []))}")
        
        if results.get("alerts"):
            print("\nALERTS:")
            for alert in results["alerts"]:
                print(f"  - {alert.get('message')}")
        
        if results.get("upcoming_deadlines"):
            print("\nUPCOMING DEADLINES:")
            for deadline in results["upcoming_deadlines"]:
                print(f"  - {deadline.get('requirement')}: {deadline.get('deadline')}")
        
        print("=" * 60 + "\n")
        
    finally:
        await crew.cleanup()


async def generate_report(report_type: str, facility_ids: list = None):
    """Generate a compliance report."""
    from agents import EnviroComplyCrew
    
    logger.info(f"Generating {report_type} report")
    
    crew = EnviroComplyCrew()
    
    try:
        await crew.initialize()
        
        # Run gap analysis first if needed
        facilities = await crew._load_facilities(facility_ids)
        
        impact = await crew.impact_assessor.run(
            context=crew.context,
            facilities=facilities,
        )
        
        await crew.gap_analyzer.run(
            context=crew.context,
            facilities=facilities,
            impact_assessments=impact.get("assessments", []),
        )
        
        # Generate report
        results = await crew.generate_report(
            report_type=ReportType(report_type),
            facility_ids=facility_ids,
        )
        
        print("\n" + "=" * 60)
        print("REPORT GENERATED")
        print("=" * 60)
        print(f"Title: {results.get('title')}")
        print(f"Type: {results.get('report_type')}")
        print(f"File: {results.get('file_path')}")
        if results.get("compliance_score"):
            print(f"Compliance Score: {results.get('compliance_score')}/100")
        print("=" * 60 + "\n")
        
    finally:
        await crew.cleanup()


async def load_sample_data():
    """Load sample data into the system."""
    import json
    from memory.weaviate_store import get_weaviate_store
    from core.models import Facility, Regulation, FacilityType, RegulationType, RegulatoryStatus
    
    logger.info("Loading sample data...")
    
    store = await get_weaviate_store()
    
    # Load facilities
    facilities_path = Path("data/facilities/sample_facilities.json")
    if facilities_path.exists():
        with open(facilities_path) as f:
            facilities_data = json.load(f)
        
        for fac_data in facilities_data.get("facilities", []):
            try:
                facility = Facility(
                    id=fac_data.get("facility_id"),
                    name=fac_data.get("name"),
                    facility_type=FacilityType(fac_data.get("facility_type", "production")),
                    state=fac_data.get("state", "TX"),
                    county=fac_data.get("county", "Unknown"),
                    operator=fac_data.get("operator", "Unknown"),
                )
                await store.store_facility(facility)
                logger.info(f"Loaded facility: {facility.name}")
            except Exception as e:
                logger.warning(f"Failed to load facility: {e}")
    
    # Load regulations
    regulations_path = Path("data/regulations/epa_regulations.json")
    if regulations_path.exists():
        with open(regulations_path) as f:
            regulations_data = json.load(f)
        
        for reg_data in regulations_data.get("regulations", []):
            try:
                regulation = Regulation(
                    id=reg_data.get("id"),
                    title=reg_data.get("title"),
                    description=reg_data.get("description", ""),
                    citation=reg_data.get("citation"),
                    regulation_type=RegulationType(reg_data.get("regulation_type", "other")),
                    status=RegulatoryStatus(reg_data.get("status", "effective")),
                    key_requirements=reg_data.get("key_requirements", []),
                )
                await store.store_regulation(regulation)
                logger.info(f"Loaded regulation: {regulation.citation}")
            except Exception as e:
                logger.warning(f"Failed to load regulation: {e}")
    
    await store.disconnect()
    logger.info("Sample data loading complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="EnviroComply - AI-powered environmental compliance management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Run the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run compliance analysis")
    analyze_parser.add_argument(
        "--mode",
        choices=["full", "monitor", "assess", "gaps"],
        default="full",
        help="Analysis mode",
    )
    analyze_parser.add_argument(
        "--facilities",
        nargs="+",
        help="Facility IDs to analyze",
    )
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor for regulatory changes")
    monitor_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days to look back",
    )
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate a report")
    report_parser.add_argument(
        "--type",
        choices=["gap_analysis", "executive_summary", "regulatory_briefing", "annual_certification"],
        default="gap_analysis",
        help="Report type",
    )
    report_parser.add_argument(
        "--facilities",
        nargs="+",
        help="Facility IDs to include",
    )
    
    # Load data command
    load_parser = subparsers.add_parser("load-data", help="Load sample data")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Execute command
    if args.command == "serve":
        asyncio.run(run_server(args.host, args.port, args.reload))
    elif args.command == "analyze":
        asyncio.run(run_analysis(args.mode, args.facilities))
    elif args.command == "monitor":
        asyncio.run(run_monitor(args.days))
    elif args.command == "report":
        asyncio.run(generate_report(args.type, args.facilities))
    elif args.command == "load-data":
        asyncio.run(load_sample_data())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
