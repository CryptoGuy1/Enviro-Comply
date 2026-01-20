"""
EnviroComply Tools
==================
LangChain tools for EPA data retrieval and document processing.
"""

from .epa_tools import (
    FederalRegisterTool,
    EPAECHOTool,
    CFRParserTool,
    EmissionsCalculatorTool,
    get_epa_tools,
    EPA_TOOLS,
)

from .document_tools import (
    PDFExtractorTool,
    DocumentChunkerTool,
    PermitParserTool,
    ReportFormatterTool,
    ComplianceFormGeneratorTool,
    get_document_tools,
    DOCUMENT_TOOLS,
)


def get_all_tools():
    """Get all available tools."""
    return EPA_TOOLS + DOCUMENT_TOOLS


__all__ = [
    # EPA Tools
    "FederalRegisterTool",
    "EPAECHOTool",
    "CFRParserTool",
    "EmissionsCalculatorTool",
    "get_epa_tools",
    "EPA_TOOLS",
    # Document Tools
    "PDFExtractorTool",
    "DocumentChunkerTool",
    "PermitParserTool",
    "ReportFormatterTool",
    "ComplianceFormGeneratorTool",
    "get_document_tools",
    "DOCUMENT_TOOLS",
    # All tools
    "get_all_tools",
]
