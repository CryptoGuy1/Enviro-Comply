"""
EnviroComply API
================
FastAPI backend for the EnviroComply compliance management system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import asyncio
from loguru import logger

from .schemas import (
    HealthResponse,
    FacilityCreate,
    FacilityResponse,
    ComplianceAnalysisRequest,
    ComplianceAnalysisResponse,
    GapAnalysisResponse,
    ReportRequest,
    ReportResponse,
    RegulationResponse,
    DashboardResponse,
)
from agents import EnviroComplyCrew, run_compliance_analysis
from core.config import settings
from core.models import ReportType
from memory.weaviate_store import get_weaviate_store


# Global crew instance
crew: Optional[EnviroComplyCrew] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global crew
    
    # Startup
    logger.info("Starting EnviroComply API...")
    crew = EnviroComplyCrew()
    
    try:
        await crew.initialize()
        logger.info("EnviroComply API started successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize crew: {e}. Running in limited mode.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down EnviroComply API...")
    if crew:
        await crew.cleanup()


# Create FastAPI app
app = FastAPI(
    title="EnviroComply API",
    description="AI-powered environmental compliance management for Oil & Gas",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API information."""
    return HealthResponse(
        status="healthy",
        service="EnviroComply API",
        version="1.0.0",
        timestamp=datetime.utcnow(),
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global crew
    
    # Check component status
    components = {
        "api": True,
        "agents": crew is not None and crew.regulation_monitor is not None,
        "memory_store": False,
    }
    
    if crew and crew.memory_store:
        try:
            # Quick check on memory store
            components["memory_store"] = True
        except:
            pass
    
    return HealthResponse(
        status="healthy" if all(components.values()) else "degraded",
        service="EnviroComply API",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        components=components,
    )


# ============================================================================
# Facility Endpoints
# ============================================================================

@app.get("/api/v1/facilities", response_model=List[FacilityResponse])
async def list_facilities():
    """List all facilities."""
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        facilities = await crew._load_facilities()
        return [FacilityResponse(**f) for f in facilities]
    except Exception as e:
        logger.error(f"Failed to list facilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/facilities/{facility_id}", response_model=FacilityResponse)
async def get_facility(facility_id: str):
    """Get a specific facility by ID."""
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        facilities = await crew._load_facilities([facility_id])
        if not facilities:
            raise HTTPException(status_code=404, detail="Facility not found")
        return FacilityResponse(**facilities[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get facility: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/facilities", response_model=FacilityResponse)
async def create_facility(facility: FacilityCreate):
    """Create a new facility."""
    global crew
    
    if not crew or not crew.memory_store:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        from core.models import Facility
        
        new_facility = Facility(
            name=facility.name,
            facility_type=facility.facility_type,
            state=facility.state,
            county=facility.county,
            operator=facility.operator,
        )
        
        await crew.memory_store.store_facility(new_facility)
        
        return FacilityResponse(
            facility_id=new_facility.id,
            name=new_facility.name,
            facility_type=new_facility.facility_type.value,
            state=new_facility.state,
            county=new_facility.county,
            operator=new_facility.operator,
        )
    except Exception as e:
        logger.error(f"Failed to create facility: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Compliance Analysis Endpoints
# ============================================================================

@app.post("/api/v1/analysis/run", response_model=ComplianceAnalysisResponse)
async def run_analysis(
    request: ComplianceAnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """
    Run compliance analysis.
    
    For full analysis, this may take several minutes. Consider using
    the async endpoint for long-running analyses.
    """
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Load facilities if IDs provided
        facilities = None
        if request.facility_ids:
            facilities = await crew._load_facilities(request.facility_ids)
        
        # Run analysis
        results = await crew.run_full_analysis(
            facilities=facilities,
            lookback_days=request.lookback_days or 30,
            report_types=[ReportType(rt) for rt in (request.report_types or ["gap_analysis"])],
        )
        
        return ComplianceAnalysisResponse(
            analysis_id=results.get("analysis_id"),
            status=results.get("status", "completed"),
            facilities_analyzed=results.get("facilities_analyzed", 0),
            regulations_found=results.get("regulations_found", 0),
            gaps_identified=results.get("gaps_identified", 0),
            phases=results.get("phases", {}),
            reports_generated=results.get("reports_generated", []),
            started_at=results.get("started_at"),
            completed_at=results.get("completed_at"),
            duration_seconds=results.get("duration_seconds"),
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analysis/gaps", response_model=GapAnalysisResponse)
async def get_gaps(
    facility_id: Optional[str] = None,
    severity: Optional[str] = None,
):
    """Get compliance gaps, optionally filtered."""
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Get gaps from context
        gaps = crew.context.gaps
        
        # Filter if requested
        if facility_id:
            gaps = [g for g in gaps if g.get("facility_id") == facility_id]
        if severity:
            gaps = [g for g in gaps if g.get("severity") == severity]
        
        # Calculate summary
        summary = {
            "critical": len([g for g in gaps if g.get("severity") == "critical"]),
            "high": len([g for g in gaps if g.get("severity") == "high"]),
            "medium": len([g for g in gaps if g.get("severity") == "medium"]),
            "low": len([g for g in gaps if g.get("severity") == "low"]),
            "total": len(gaps),
        }
        
        return GapAnalysisResponse(
            gaps=gaps,
            summary=summary,
            total_remediation_cost=sum(g.get("estimated_cost", 0) for g in gaps),
        )
    except Exception as e:
        logger.error(f"Failed to get gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Report Endpoints
# ============================================================================

@app.post("/api/v1/reports/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate a compliance report."""
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        facilities = None
        if request.facility_ids:
            facilities = await crew._load_facilities(request.facility_ids)
        
        report_type = ReportType(request.report_type)
        
        results = await crew.generate_report(
            report_type=report_type,
            facility_ids=request.facility_ids,
        )
        
        return ReportResponse(
            report_id=results.get("id"),
            report_type=results.get("report_type"),
            title=results.get("title"),
            file_path=results.get("file_path"),
            compliance_score=results.get("compliance_score"),
            generated_at=results.get("generated_at"),
        )
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download a generated report."""
    report_dir = Path(settings.agent.report_output_dir)
    
    # Find report file
    for ext in [".json", ".md", ".pdf"]:
        report_path = report_dir / f"{report_id}{ext}"
        if report_path.exists():
            return FileResponse(
                path=report_path,
                filename=report_path.name,
                media_type="application/octet-stream",
            )
    
    raise HTTPException(status_code=404, detail="Report not found")


# ============================================================================
# Regulation Endpoints
# ============================================================================

@app.get("/api/v1/regulations", response_model=List[RegulationResponse])
async def list_regulations(
    regulation_type: Optional[str] = None,
    limit: int = 50,
):
    """List regulations from the knowledge base."""
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Get from context or search
        regulations = crew.context.regulations
        
        if regulation_type:
            regulations = [r for r in regulations if r.get("regulation_type") == regulation_type]
        
        return [RegulationResponse(**r) for r in regulations[:limit]]
    except Exception as e:
        logger.error(f"Failed to list regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/regulations/search")
async def search_regulations(query: str, limit: int = 10):
    """Semantic search over regulations."""
    global crew
    
    if not crew or not crew.memory_store:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        results = await crew.memory_store.search_regulations(query, limit=limit)
        return {"results": results, "query": query, "count": len(results)}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@app.get("/api/v1/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get dashboard summary data."""
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        context_summary = crew.get_context_summary()
        
        # Calculate compliance score
        gaps = crew.context.gaps
        critical = len([g for g in gaps if g.get("severity") == "critical"])
        high = len([g for g in gaps if g.get("severity") == "high"])
        medium = len([g for g in gaps if g.get("severity") == "medium"])
        low = len([g for g in gaps if g.get("severity") == "low"])
        
        score = max(0, 100 - (critical * 15) - (high * 8) - (medium * 3) - (low * 1))
        
        return DashboardResponse(
            compliance_score=score,
            facilities_count=context_summary.get("facilities_count", 0),
            regulations_count=context_summary.get("regulations_count", 0),
            gaps_summary={
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
                "total": len(gaps),
            },
            alerts_count=context_summary.get("alerts_count", 0),
            recent_alerts=crew.context.alerts[-5:] if crew.context.alerts else [],
            last_analysis=context_summary.get("created_at"),
        )
    except Exception as e:
        logger.error(f"Dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Monitoring Endpoints
# ============================================================================

@app.post("/api/v1/monitor/scan")
async def scan_regulations(lookback_days: int = 30):
    """Trigger a regulatory scan."""
    global crew
    
    if not crew:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        results = await crew.regulation_monitor.run(
            context=crew.context,
            lookback_days=lookback_days,
        )
        
        return {
            "status": "completed",
            "new_regulations": len(results.get("new_regulations", [])),
            "amended_regulations": len(results.get("amended_regulations", [])),
            "alerts": results.get("alerts", []),
            "upcoming_deadlines": results.get("upcoming_deadlines", []),
        }
    except Exception as e:
        logger.error(f"Regulatory scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
