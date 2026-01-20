"""
Data Loaders
============
Utilities for loading sample and real regulatory data.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date
from loguru import logger


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).parent


def load_sample_facilities() -> List[Dict[str, Any]]:
    """Load sample facility data."""
    facilities_path = get_data_dir() / "facilities" / "sample_facilities.json"
    
    if not facilities_path.exists():
        logger.warning(f"Sample facilities file not found: {facilities_path}")
        return _get_default_facilities()
    
    try:
        with open(facilities_path) as f:
            data = json.load(f)
        return data.get("facilities", [])
    except Exception as e:
        logger.error(f"Failed to load sample facilities: {e}")
        return _get_default_facilities()


def load_sample_regulations() -> List[Dict[str, Any]]:
    """Load sample regulation data."""
    regulations_path = get_data_dir() / "regulations" / "epa_regulations.json"
    
    if not regulations_path.exists():
        logger.warning(f"Sample regulations file not found: {regulations_path}")
        return _get_default_regulations()
    
    try:
        with open(regulations_path) as f:
            data = json.load(f)
        return data.get("regulations", [])
    except Exception as e:
        logger.error(f"Failed to load sample regulations: {e}")
        return _get_default_regulations()


def _get_default_facilities() -> List[Dict[str, Any]]:
    """Return default sample facilities if file not available."""
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
                        "last_inspection": str(date.today()),
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
        {
            "facility_id": "wyoming-001",
            "name": "Wyoming Gas Processing Plant",
            "facility_type": "processing",
            "state": "WY",
            "county": "Sublette",
            "operator": "Demo Oil & Gas Co.",
            "is_major_source": True,
            "title_v_applicable": True,
            "metadata": {
                "emission_sources": [
                    {
                        "id": "src-020",
                        "name": "Amine Unit",
                        "source_type": "process",
                        "equipment_type": "amine gas treating",
                    },
                    {
                        "id": "src-021",
                        "name": "Flare",
                        "source_type": "combustion",
                        "equipment_type": "emergency flare",
                    },
                    {
                        "id": "src-022",
                        "name": "Product Storage",
                        "source_type": "storage",
                        "equipment_type": "NGL storage tanks",
                        "controlled": True,
                    },
                ],
                "permits": [
                    {
                        "permit_number": "WY-TV-2020-005",
                        "permit_type": "Title V",
                        "status": "active",
                        "expiration_date": "2025-03-15",
                    }
                ],
                "total_potential_emissions_tpy": {
                    "VOC": 250.0,
                    "NOx": 150.0,
                    "CO": 95.0,
                    "HAP": 25.0,
                    "CO2e": 120000,
                },
            },
        },
    ]


def _get_default_regulations() -> List[Dict[str, Any]]:
    """Return default sample regulations if file not available."""
    return [
        {
            "id": "nsps-ooooa",
            "citation": "40 CFR 60 Subpart OOOOa",
            "title": "Standards of Performance for Crude Oil and Natural Gas Facilities for which Construction, Modification or Reconstruction Commenced After September 18, 2015",
            "regulation_type": "nsps",
            "status": "effective",
            "description": "Establishes emission standards for VOC and methane from affected facilities in the crude oil and natural gas source category.",
            "applicable_facility_types": ["production", "gathering", "processing", "transmission"],
            "key_requirements": [
                "Reduce VOC emissions from storage vessels by 95%",
                "Use low-bleed or no-bleed pneumatic controllers",
                "Conduct LDAR surveys at wellsites and compressor stations",
                "Control emissions from centrifugal compressors",
                "Monitor and repair fugitive emissions",
            ],
            "effective_date": "2016-08-02",
        },
        {
            "id": "nsps-oooob",
            "citation": "40 CFR 60 Subpart OOOOb",
            "title": "Standards of Performance for Crude Oil and Natural Gas Facilities: Emissions Standards for GHG and VOC",
            "regulation_type": "nsps",
            "status": "effective",
            "description": "Updates and strengthens standards for new and modified sources, adding super-emitter response program.",
            "applicable_facility_types": ["production", "gathering", "processing", "transmission"],
            "key_requirements": [
                "Zero-emission pneumatic controllers at new sites",
                "Enhanced LDAR requirements",
                "Super-emitter response program participation",
                "Reduced emissions during liquids unloading",
                "Flare efficiency requirements",
            ],
            "effective_date": "2024-05-07",
        },
        {
            "id": "neshap-hh",
            "citation": "40 CFR 63 Subpart HH",
            "title": "National Emission Standards for Hazardous Air Pollutants from Oil and Natural Gas Production Facilities",
            "regulation_type": "neshap",
            "status": "effective",
            "description": "Establishes HAP emission standards for major sources in oil and natural gas production.",
            "applicable_facility_types": ["production", "processing"],
            "key_requirements": [
                "HAP emission reduction from glycol dehydrators",
                "Triethylene glycol (TEG) dehydrator controls",
                "Small glycol dehydrator exemptions",
                "Initial notification and compliance reports",
            ],
            "effective_date": "1999-06-17",
        },
        {
            "id": "ghg-subpart-w",
            "citation": "40 CFR 98 Subpart W",
            "title": "Petroleum and Natural Gas Systems - Greenhouse Gas Reporting",
            "regulation_type": "ghg_reporting",
            "status": "effective",
            "description": "Requires annual GHG reporting from facilities exceeding 25,000 MT CO2e.",
            "applicable_facility_types": ["production", "gathering", "processing", "transmission"],
            "key_requirements": [
                "Calculate GHG emissions using specified methods",
                "Report annually by March 31",
                "Maintain records for 3 years",
                "Use electronic reporting (e-GGRT)",
            ],
            "effective_date": "2010-12-01",
        },
    ]


# Export loaders
__all__ = [
    "load_sample_facilities",
    "load_sample_regulations",
    "get_data_dir",
]
