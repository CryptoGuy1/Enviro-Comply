"""
EnviroComply Exceptions
=======================
Custom exception classes for the application.
"""


class EnviroComplyError(Exception):
    """Base exception for EnviroComply."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# Configuration Exceptions
# ============================================================================

class ConfigurationError(EnviroComplyError):
    """Raised when configuration is invalid or missing."""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when a required API key is not configured."""
    
    def __init__(self, key_name: str):
        super().__init__(
            f"Missing required API key: {key_name}",
            {"key_name": key_name}
        )


# ============================================================================
# Data Exceptions
# ============================================================================

class DataError(EnviroComplyError):
    """Base exception for data-related errors."""
    pass


class RegulationNotFoundError(DataError):
    """Raised when a regulation cannot be found."""
    
    def __init__(self, regulation_id: str):
        super().__init__(
            f"Regulation not found: {regulation_id}",
            {"regulation_id": regulation_id}
        )


class FacilityNotFoundError(DataError):
    """Raised when a facility cannot be found."""
    
    def __init__(self, facility_id: str):
        super().__init__(
            f"Facility not found: {facility_id}",
            {"facility_id": facility_id}
        )


class DuplicateRecordError(DataError):
    """Raised when attempting to create a duplicate record."""
    
    def __init__(self, record_type: str, identifier: str):
        super().__init__(
            f"Duplicate {record_type}: {identifier}",
            {"record_type": record_type, "identifier": identifier}
        )


class DataValidationError(DataError):
    """Raised when data validation fails."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            f"Validation error for {field}: {message}",
            {"field": field, "validation_message": message}
        )


# ============================================================================
# Agent Exceptions
# ============================================================================

class AgentError(EnviroComplyError):
    """Base exception for agent-related errors."""
    pass


class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize."""
    
    def __init__(self, agent_name: str, reason: str):
        super().__init__(
            f"Failed to initialize agent '{agent_name}': {reason}",
            {"agent_name": agent_name, "reason": reason}
        )


class AgentExecutionError(AgentError):
    """Raised when an agent fails during execution."""
    
    def __init__(self, agent_name: str, task: str, reason: str):
        super().__init__(
            f"Agent '{agent_name}' failed during '{task}': {reason}",
            {"agent_name": agent_name, "task": task, "reason": reason}
        )


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""
    
    def __init__(self, agent_name: str, timeout_seconds: float):
        super().__init__(
            f"Agent '{agent_name}' timed out after {timeout_seconds}s",
            {"agent_name": agent_name, "timeout_seconds": timeout_seconds}
        )


class LLMError(AgentError):
    """Raised when LLM interaction fails."""
    
    def __init__(self, provider: str, message: str):
        super().__init__(
            f"LLM error ({provider}): {message}",
            {"provider": provider, "error_message": message}
        )


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    
    def __init__(self, provider: str, retry_after: float = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after}s"
        super().__init__(provider, message)
        self.details["retry_after"] = retry_after


# ============================================================================
# External Service Exceptions
# ============================================================================

class ExternalServiceError(EnviroComplyError):
    """Base exception for external service errors."""
    pass


class EPAAPIError(ExternalServiceError):
    """Raised when EPA API call fails."""
    
    def __init__(self, endpoint: str, status_code: int = None, message: str = None):
        error_msg = f"EPA API error for {endpoint}"
        if status_code:
            error_msg += f" (HTTP {status_code})"
        if message:
            error_msg += f": {message}"
        super().__init__(
            error_msg,
            {"endpoint": endpoint, "status_code": status_code}
        )


class WeaviateError(ExternalServiceError):
    """Raised when Weaviate operation fails."""
    
    def __init__(self, operation: str, message: str):
        super().__init__(
            f"Weaviate {operation} failed: {message}",
            {"operation": operation}
        )


class DatabaseError(ExternalServiceError):
    """Raised when database operation fails."""
    
    def __init__(self, operation: str, message: str):
        super().__init__(
            f"Database {operation} failed: {message}",
            {"operation": operation}
        )


# ============================================================================
# Compliance Exceptions
# ============================================================================

class ComplianceError(EnviroComplyError):
    """Base exception for compliance-related errors."""
    pass


class GapAnalysisError(ComplianceError):
    """Raised when gap analysis fails."""
    
    def __init__(self, facility_id: str, reason: str):
        super().__init__(
            f"Gap analysis failed for facility {facility_id}: {reason}",
            {"facility_id": facility_id, "reason": reason}
        )


class ReportGenerationError(ComplianceError):
    """Raised when report generation fails."""
    
    def __init__(self, report_type: str, reason: str):
        super().__init__(
            f"Failed to generate {report_type} report: {reason}",
            {"report_type": report_type, "reason": reason}
        )


# ============================================================================
# Tool Exceptions
# ============================================================================

class ToolError(EnviroComplyError):
    """Base exception for tool-related errors."""
    pass


class DocumentProcessingError(ToolError):
    """Raised when document processing fails."""
    
    def __init__(self, document: str, reason: str):
        super().__init__(
            f"Failed to process document '{document}': {reason}",
            {"document": document, "reason": reason}
        )


class WebScrapingError(ToolError):
    """Raised when web scraping fails."""
    
    def __init__(self, url: str, reason: str):
        super().__init__(
            f"Failed to scrape {url}: {reason}",
            {"url": url, "reason": reason}
        )
