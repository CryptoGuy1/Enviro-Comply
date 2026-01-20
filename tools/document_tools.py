"""
Document Processing Tools
=========================
Tools for processing regulatory documents, permits, and reports.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from loguru import logger

from langchain.tools import BaseTool
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import Field


class PDFExtractorTool(BaseTool):
    """Tool for extracting text from PDF documents."""
    
    name: str = "pdf_extractor"
    description: str = """Extract text content from a PDF document.
    Provide the file path to the PDF. Returns the extracted text
    suitable for analysis."""
    
    def _run(self, file_path: str) -> str:
        """Extract text from PDF."""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"File not found: {file_path}"
            
            if not path.suffix.lower() == ".pdf":
                return f"Not a PDF file: {file_path}"
            
            loader = PyPDFLoader(str(path))
            pages = loader.load()
            
            text = "\n\n".join([page.page_content for page in pages])
            
            return f"Extracted {len(pages)} pages:\n\n{text[:10000]}..."
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return f"Error extracting PDF: {e}"
    
    async def _arun(self, file_path: str) -> str:
        """Async extraction."""
        return self._run(file_path)


class DocumentChunkerTool(BaseTool):
    """Tool for splitting documents into chunks for RAG."""
    
    name: str = "document_chunker"
    description: str = """Split a document into chunks suitable for embedding
    and retrieval. Provide the text content to chunk."""
    
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    
    def _run(self, text: str) -> str:
        """Split text into chunks."""
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            
            chunks = splitter.split_text(text)
            
            result = {
                "chunk_count": len(chunks),
                "avg_chunk_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "chunks": [
                    {"id": i, "text": chunk[:200] + "...", "length": len(chunk)}
                    for i, chunk in enumerate(chunks[:5])  # Preview first 5
                ],
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Chunking failed: {e}")
            return f"Error chunking document: {e}"
    
    async def _arun(self, text: str) -> str:
        """Async chunking."""
        return self._run(text)


class PermitParserTool(BaseTool):
    """Tool for parsing environmental permit documents."""
    
    name: str = "permit_parser"
    description: str = """Parse an environmental permit document to extract
    key information like permit number, conditions, emission limits, and
    compliance requirements. Provide the permit text."""
    
    def _run(self, permit_text: str) -> str:
        """Parse permit document."""
        try:
            # Extract common permit elements using patterns
            import re
            
            result = {
                "permit_numbers": [],
                "emission_limits": [],
                "monitoring_requirements": [],
                "reporting_requirements": [],
                "key_conditions": [],
            }
            
            # Look for permit numbers
            permit_patterns = [
                r"Permit\s*(?:No\.?|Number:?)\s*([A-Z0-9-]+)",
                r"Title\s+V\s+Permit\s*[:#]?\s*([A-Z0-9-]+)",
                r"PSD\s+Permit\s*[:#]?\s*([A-Z0-9-]+)",
            ]
            
            for pattern in permit_patterns:
                matches = re.findall(pattern, permit_text, re.IGNORECASE)
                result["permit_numbers"].extend(matches)
            
            # Look for emission limits
            limit_patterns = [
                r"(\d+\.?\d*)\s*(tons?|tpy|lb|ppm|gr/dscf)\s+(?:of\s+)?(\w+)",
                r"(\w+)\s*[:=]\s*(\d+\.?\d*)\s*(tons?|tpy|lb/hr|ppm)",
            ]
            
            for pattern in limit_patterns:
                matches = re.findall(pattern, permit_text, re.IGNORECASE)
                for match in matches[:10]:  # Limit results
                    result["emission_limits"].append(" ".join(match))
            
            # Look for monitoring keywords
            monitoring_keywords = [
                "CEMS", "continuous monitoring", "stack test",
                "Method 21", "OGI", "LDAR", "annual test",
            ]
            
            for keyword in monitoring_keywords:
                if keyword.lower() in permit_text.lower():
                    # Extract surrounding context
                    idx = permit_text.lower().find(keyword.lower())
                    context = permit_text[max(0, idx-50):idx+100]
                    result["monitoring_requirements"].append(context.strip())
            
            # Look for reporting requirements
            reporting_patterns = [
                r"(semi-?annual|annual|quarterly|monthly)\s+report",
                r"submit\s+(?:a\s+)?report\s+(?:within|by|no later than)",
                r"deviation\s+report",
            ]
            
            for pattern in reporting_patterns:
                matches = re.findall(pattern, permit_text, re.IGNORECASE)
                result["reporting_requirements"].extend(matches[:5])
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Permit parsing failed: {e}")
            return f"Error parsing permit: {e}"
    
    async def _arun(self, permit_text: str) -> str:
        """Async parsing."""
        return self._run(permit_text)


class ReportFormatterTool(BaseTool):
    """Tool for formatting compliance reports."""
    
    name: str = "report_formatter"
    description: str = """Format compliance data into a professional report.
    Provide structured data (JSON) with report type, content sections,
    and any tables or figures to include."""
    
    def _run(self, data: str) -> str:
        """Format report."""
        try:
            report_data = json.loads(data)
            
            report_type = report_data.get("type", "general")
            title = report_data.get("title", "Compliance Report")
            sections = report_data.get("sections", [])
            
            # Generate markdown report
            lines = [
                f"# {title}",
                f"",
                f"**Report Type:** {report_type}",
                f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                f"",
                "---",
                "",
            ]
            
            for section in sections:
                lines.append(f"## {section.get('title', 'Section')}")
                lines.append("")
                lines.append(section.get("content", ""))
                lines.append("")
                
                # Add tables if present
                if "table" in section:
                    table = section["table"]
                    headers = table.get("headers", [])
                    rows = table.get("rows", [])
                    
                    if headers:
                        lines.append("| " + " | ".join(headers) + " |")
                        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                        for row in rows:
                            lines.append("| " + " | ".join(str(c) for c in row) + " |")
                        lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Report formatting failed: {e}")
            return f"Error formatting report: {e}"
    
    async def _arun(self, data: str) -> str:
        """Async formatting."""
        return self._run(data)


class ComplianceFormGeneratorTool(BaseTool):
    """Tool for generating EPA compliance forms."""
    
    name: str = "compliance_form_generator"
    description: str = """Generate pre-filled EPA compliance forms based on
    facility data. Provide facility ID and form type (e.g., 'title_v_certification',
    'emissions_inventory', 'deviation_report')."""
    
    def _run(self, params: str) -> str:
        """Generate compliance form."""
        try:
            data = json.loads(params)
            form_type = data.get("form_type", "").lower()
            facility_data = data.get("facility", {})
            
            if form_type == "title_v_certification":
                return self._generate_title_v_cert(facility_data)
            elif form_type == "emissions_inventory":
                return self._generate_emissions_inventory(facility_data)
            elif form_type == "deviation_report":
                return self._generate_deviation_report(facility_data)
            else:
                return f"Unknown form type: {form_type}"
                
        except Exception as e:
            logger.error(f"Form generation failed: {e}")
            return f"Error generating form: {e}"
    
    async def _arun(self, params: str) -> str:
        """Async generation."""
        return self._run(params)
    
    def _generate_title_v_cert(self, facility: Dict) -> str:
        """Generate Title V Annual Compliance Certification."""
        return f"""
TITLE V ANNUAL COMPLIANCE CERTIFICATION

Facility Name: {facility.get('name', '[FACILITY NAME]')}
Permit Number: {facility.get('permit_number', '[PERMIT NUMBER]')}
Reporting Period: {datetime.now().year - 1}

CERTIFICATION STATEMENT:

I certify that, based on information and belief formed after reasonable inquiry,
the statements and information in this certification are true, accurate, and complete.

I certify that the facility identified above was in compliance with all applicable
requirements of the Clean Air Act and the Title V operating permit during the
reporting period, except as noted in the attached deviation reports.

Compliance Status:
[ ] Continuous Compliance
[ ] Intermittent Compliance (deviations attached)
[ ] Non-compliance (explanation attached)

Responsible Official:
Name: ________________________________
Title: ________________________________
Signature: ____________________________
Date: ________________________________

Submit to: [State Agency Address]
Due Date: March 15, {datetime.now().year}
"""
    
    def _generate_emissions_inventory(self, facility: Dict) -> str:
        """Generate emissions inventory form."""
        emissions = facility.get("emissions", {})
        
        return f"""
ANNUAL EMISSIONS INVENTORY REPORT

Facility: {facility.get('name', '[FACILITY NAME]')}
Year: {datetime.now().year - 1}
SIC Code: {facility.get('sic_code', '[SIC]')}
NAICS Code: {facility.get('naics_code', '[NAICS]')}

CRITERIA POLLUTANT EMISSIONS (tons/year):
- Volatile Organic Compounds (VOC): {emissions.get('VOC', '___')}
- Nitrogen Oxides (NOx): {emissions.get('NOx', '___')}
- Carbon Monoxide (CO): {emissions.get('CO', '___')}
- Sulfur Dioxide (SO2): {emissions.get('SO2', '___')}
- Particulate Matter (PM10): {emissions.get('PM10', '___')}
- Particulate Matter (PM2.5): {emissions.get('PM2.5', '___')}

HAZARDOUS AIR POLLUTANTS (tons/year):
- Total HAPs: {emissions.get('HAP', '___')}
- Benzene: {emissions.get('Benzene', '___')}
- n-Hexane: {emissions.get('n-Hexane', '___')}
- Other HAPs: ___

GREENHOUSE GAS EMISSIONS (metric tons CO2e/year):
- Total GHGs: {emissions.get('CO2e', '___')}

Certification: I certify the above emissions data is accurate.
Signature: _________________________ Date: _____________
"""
    
    def _generate_deviation_report(self, facility: Dict) -> str:
        """Generate deviation report form."""
        return f"""
DEVIATION REPORT

Facility: {facility.get('name', '[FACILITY NAME]')}
Permit Number: {facility.get('permit_number', '[PERMIT NUMBER]')}
Report Date: {datetime.now().strftime('%Y-%m-%d')}

DEVIATION DETAILS:

1. Date/Time of Deviation:
   Start: _________________________ End: _________________________

2. Permit Condition Deviated From:
   Condition Number: _____________
   Requirement: _________________________________________________

3. Description of Deviation:
   _____________________________________________________________
   _____________________________________________________________

4. Cause of Deviation:
   [ ] Equipment Malfunction
   [ ] Startup/Shutdown
   [ ] Upset Condition
   [ ] Operator Error
   [ ] Other: ______________

5. Corrective Actions Taken:
   _____________________________________________________________
   _____________________________________________________________

6. Steps to Prevent Recurrence:
   _____________________________________________________________

7. Excess Emissions (if applicable):
   Pollutant: _____________ Amount: _____________ Duration: _______

Submitted by: _________________________ Date: _____________
"""


# Tool registry
DOCUMENT_TOOLS = [
    PDFExtractorTool(),
    DocumentChunkerTool(),
    PermitParserTool(),
    ReportFormatterTool(),
    ComplianceFormGeneratorTool(),
]


def get_document_tools() -> List[BaseTool]:
    """Get all document processing tools."""
    return DOCUMENT_TOOLS
