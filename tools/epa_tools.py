"""
EPA Data Retrieval Tools
========================
Tools for fetching data from EPA APIs and databases.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import asyncio
import httpx
from loguru import logger

from langchain.tools import BaseTool
from pydantic import Field

from core.config import settings


class FederalRegisterTool(BaseTool):
    """Tool for searching the Federal Register API."""
    
    name: str = "federal_register_search"
    description: str = """Search the Federal Register for EPA regulations.
    Use this to find new rules, proposed rules, and notices related to 
    environmental regulations. Provide search terms related to oil and gas,
    emissions, or specific CFR parts."""
    
    base_url: str = Field(default="https://www.federalregister.gov/api/v1")
    
    def _run(self, query: str) -> str:
        """Synchronous run - use async version."""
        import asyncio
        return asyncio.run(self._arun(query))
    
    async def _arun(self, query: str) -> str:
        """Search Federal Register for relevant documents."""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "conditions[term]": query,
                    "conditions[agencies][]": "environmental-protection-agency",
                    "conditions[type][]": ["RULE", "PRORULE", "NOTICE"],
                    "per_page": 20,
                    "order": "newest",
                }
                
                response = await client.get(
                    f"{self.base_url}/documents.json",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for doc in data.get("results", []):
                    results.append({
                        "title": doc.get("title"),
                        "type": doc.get("type"),
                        "publication_date": doc.get("publication_date"),
                        "abstract": doc.get("abstract", "")[:500],
                        "html_url": doc.get("html_url"),
                        "document_number": doc.get("document_number"),
                    })
                
                return str(results)
                
        except Exception as e:
            logger.error(f"Federal Register search failed: {e}")
            return f"Error searching Federal Register: {e}"


class EPAECHOTool(BaseTool):
    """Tool for querying EPA ECHO database."""
    
    name: str = "epa_echo_search"
    description: str = """Query the EPA ECHO (Enforcement and Compliance History Online) 
    database to find facility compliance information, violations, and enforcement actions.
    Provide a facility name, EPA ID, or location to search."""
    
    base_url: str = Field(default="https://echo.epa.gov/api")
    
    def _run(self, query: str) -> str:
        """Synchronous run."""
        import asyncio
        return asyncio.run(self._arun(query))
    
    async def _arun(self, query: str) -> str:
        """Search ECHO for facility information."""
        try:
            async with httpx.AsyncClient() as client:
                # Search for facilities
                params = {
                    "output": "JSON",
                    "p_fn": query,  # Facility name
                    "p_act": "CAA",  # Clean Air Act
                }
                
                response = await client.get(
                    f"{self.base_url}/air_rest_services.get_facilities",
                    params=params,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    return response.text[:5000]  # Truncate large responses
                else:
                    return f"ECHO API returned status {response.status_code}"
                    
        except Exception as e:
            logger.error(f"ECHO search failed: {e}")
            return f"Error querying ECHO: {e}"


class CFRParserTool(BaseTool):
    """Tool for parsing CFR regulation text."""
    
    name: str = "cfr_parser"
    description: str = """Parse and extract information from Code of Federal Regulations
    citations. Provide a CFR citation like '40 CFR 60.5395' to get the regulation text
    and requirements."""
    
    def _run(self, citation: str) -> str:
        """Parse CFR citation."""
        import asyncio
        return asyncio.run(self._arun(citation))
    
    async def _arun(self, citation: str) -> str:
        """Fetch and parse CFR text."""
        try:
            # Parse citation
            parts = citation.upper().replace("CFR", "").split()
            if len(parts) < 2:
                return "Invalid CFR citation format. Use format: '40 CFR 60.5395'"
            
            title = parts[0].strip()
            part_section = parts[1].strip()
            
            # Use eCFR API
            async with httpx.AsyncClient() as client:
                # This is a simplified example - real implementation would
                # need to handle the eCFR API structure
                url = f"https://www.ecfr.gov/api/versioner/v1/full/{date.today()}/title-{title}.json"
                
                response = await client.get(url, timeout=30.0)
                
                if response.status_code == 200:
                    # Parse and extract relevant section
                    return f"CFR {citation} retrieved successfully. [Full parsing would extract specific section]"
                else:
                    return f"Could not retrieve CFR {citation}"
                    
        except Exception as e:
            logger.error(f"CFR parsing failed: {e}")
            return f"Error parsing CFR: {e}"


class EmissionsCalculatorTool(BaseTool):
    """Tool for calculating emissions using EPA methodologies."""
    
    name: str = "emissions_calculator"
    description: str = """Calculate emissions using EPA-approved methodologies.
    Provide emission source type, activity data, and relevant parameters.
    Supports calculations for storage tanks, engines, fugitives, and flares."""
    
    def _run(self, params: str) -> str:
        """Calculate emissions."""
        return self._calculate(params)
    
    async def _arun(self, params: str) -> str:
        """Async calculate emissions."""
        return self._calculate(params)
    
    def _calculate(self, params: str) -> str:
        """Perform emissions calculation."""
        # Parse parameters
        import json
        try:
            data = json.loads(params)
        except:
            return "Invalid parameters. Provide JSON with source_type, activity, and relevant factors."
        
        source_type = data.get("source_type", "").lower()
        
        if source_type == "storage_tank":
            return self._calculate_tank_emissions(data)
        elif source_type == "engine":
            return self._calculate_engine_emissions(data)
        elif source_type == "fugitive":
            return self._calculate_fugitive_emissions(data)
        elif source_type == "flare":
            return self._calculate_flare_emissions(data)
        else:
            return f"Unknown source type: {source_type}. Supported: storage_tank, engine, fugitive, flare"
    
    def _calculate_tank_emissions(self, data: Dict) -> str:
        """Calculate storage tank emissions using AP-42 methods."""
        # Simplified working/breathing loss calculation
        throughput = data.get("throughput_bbl_yr", 0)
        vapor_pressure = data.get("vapor_pressure_psia", 5)
        
        # Very simplified calculation
        voc_emissions = throughput * vapor_pressure * 0.0001  # Placeholder factor
        
        return f"""Storage Tank Emissions Estimate:
        - Throughput: {throughput} bbl/yr
        - Vapor Pressure: {vapor_pressure} psia
        - Estimated VOC Emissions: {voc_emissions:.2f} tons/year
        
        Note: This is a simplified estimate. Use EPA TANKS 4.09 for accurate calculations."""
    
    def _calculate_engine_emissions(self, data: Dict) -> str:
        """Calculate engine emissions using EPA factors."""
        horsepower = data.get("horsepower", 0)
        hours_per_year = data.get("hours_per_year", 8760)
        engine_type = data.get("engine_type", "4-stroke lean burn")
        
        # AP-42 factors for natural gas engines (lb/hp-hr)
        factors = {
            "4-stroke lean burn": {"NOx": 0.013, "CO": 0.0075, "VOC": 0.0018},
            "4-stroke rich burn": {"NOx": 0.027, "CO": 0.015, "VOC": 0.0025},
            "2-stroke lean burn": {"NOx": 0.018, "CO": 0.012, "VOC": 0.0022},
        }
        
        ef = factors.get(engine_type, factors["4-stroke lean burn"])
        
        nox = horsepower * hours_per_year * ef["NOx"] / 2000
        co = horsepower * hours_per_year * ef["CO"] / 2000
        voc = horsepower * hours_per_year * ef["VOC"] / 2000
        
        return f"""Engine Emissions Estimate:
        - Engine: {horsepower} HP, {engine_type}
        - Operating Hours: {hours_per_year}/year
        - NOx: {nox:.2f} tons/year
        - CO: {co:.2f} tons/year
        - VOC: {voc:.2f} tons/year
        
        Factors from AP-42 Chapter 3.2"""
    
    def _calculate_fugitive_emissions(self, data: Dict) -> str:
        """Calculate fugitive emissions using EPA factors."""
        component_counts = data.get("components", {})
        
        # EPA default factors (kg/hr/component)
        factors = {
            "valve": 0.0056,
            "connector": 0.00083,
            "pump": 0.0214,
            "compressor": 0.228,
            "pressure_relief": 0.104,
            "open_ended_line": 0.0017,
        }
        
        total_voc = 0
        details = []
        
        for component, count in component_counts.items():
            if component in factors:
                emissions = count * factors[component] * 8760 / 1000  # kg to tons
                total_voc += emissions
                details.append(f"  - {component}: {count} units = {emissions:.3f} tpy")
        
        return f"""Fugitive Emissions Estimate:
{chr(10).join(details)}
        - Total VOC: {total_voc:.2f} tons/year
        
        Using EPA Protocol for Equipment Leak Emission Estimates"""
    
    def _calculate_flare_emissions(self, data: Dict) -> str:
        """Calculate flare emissions."""
        gas_rate = data.get("gas_rate_scf_day", 0)
        heating_value = data.get("heating_value_btu_scf", 1000)
        destruction_efficiency = data.get("destruction_efficiency", 0.98)
        
        # Simplified calculation
        voc_destroyed = gas_rate * 365 * (1 - destruction_efficiency) / 1e6  # MMSCF
        co2_emissions = gas_rate * 365 * heating_value * 0.053 / 1e9  # tons CO2
        
        return f"""Flare Emissions Estimate:
        - Gas Rate: {gas_rate} scf/day
        - Destruction Efficiency: {destruction_efficiency * 100}%
        - VOC (unburned): ~{voc_destroyed:.2f} tons/year
        - CO2: ~{co2_emissions:.0f} tons/year
        
        Note: Actual emissions depend on gas composition and flare design."""


# Tool registry
EPA_TOOLS = [
    FederalRegisterTool(),
    EPAECHOTool(),
    CFRParserTool(),
    EmissionsCalculatorTool(),
]


def get_epa_tools() -> List[BaseTool]:
    """Get all EPA-related tools."""
    return EPA_TOOLS
