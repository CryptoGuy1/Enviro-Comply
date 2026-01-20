"""
EnviroComply Configuration
==========================
Centralized configuration management using Pydantic settings.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class LLMSettings(BaseSettings):
    """LLM provider configuration."""
    
    provider: str = Field(default="openai", description="LLM provider: openai, ollama, anthropic")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, description="Temperature for responses")
    
    # Ollama fallback
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3:8b", alias="OLLAMA_MODEL")
    
    # Rate limiting
    max_tokens: int = Field(default=4096, description="Max tokens per request")
    requests_per_minute: int = Field(default=20, description="Rate limit")
    
    class Config:
        env_prefix = "LLM_"
        extra = "ignore"


class WeaviateSettings(BaseSettings):
    """Weaviate vector database configuration."""
    
    url: str = Field(default="http://localhost:8080", alias="WEAVIATE_URL")
    api_key: Optional[str] = Field(default=None, alias="WEAVIATE_API_KEY")
    
    # Collection names
    regulations_collection: str = "Regulation"
    facilities_collection: str = "Facility"
    compliance_collection: str = "ComplianceRecord"
    agent_memory_collection: str = "AgentMemory"
    
    # Embedding settings
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    class Config:
        env_prefix = "WEAVIATE_"
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""
    
    url: str = Field(
        default="postgresql://enviro:enviro@localhost:5432/envirocomply",
        alias="DATABASE_URL"
    )
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    
    class Config:
        extra = "ignore"


class EPASettings(BaseSettings):
    """EPA data source configuration."""
    
    # Federal Register API
    federal_register_base_url: str = "https://www.federalregister.gov/api/v1"
    
    # EPA ECHO API
    echo_base_url: str = "https://echo.epa.gov/api"
    
    # API Keys (optional, for higher rate limits)
    epa_api_key: Optional[str] = Field(default=None, alias="EPA_API_KEY")
    
    # Monitoring settings
    check_interval_hours: int = Field(default=24, description="Hours between regulation checks")
    lookback_days: int = Field(default=30, description="Days to look back for changes")
    
    # Oil & Gas specific CFR parts to monitor
    monitored_cfr_parts: List[str] = Field(default=[
        "40 CFR 60",      # NSPS
        "40 CFR 63",      # NESHAP  
        "40 CFR 98",      # GHG Reporting
        "40 CFR 51",      # State Implementation Plans
        "40 CFR 52",      # Approval of State Plans
    ])
    
    # Keywords for Oil & Gas relevance filtering
    oil_gas_keywords: List[str] = Field(default=[
        "oil and gas",
        "petroleum",
        "natural gas",
        "crude oil",
        "VOC",
        "volatile organic compound",
        "methane",
        "flaring",
        "venting",
        "fugitive emissions",
        "LDAR",
        "leak detection",
        "storage vessel",
        "tank battery",
        "pneumatic",
        "compressor",
        "dehydrator",
        "glycol",
        "wellhead",
        "separator",
        "heater treater",
    ])
    
    class Config:
        env_prefix = "EPA_"
        extra = "ignore"


class StateRegulationSettings(BaseSettings):
    """State environmental agency configuration."""
    
    # Primary states for Oil & Gas
    monitored_states: List[str] = Field(default=[
        "TX",  # Texas - TCEQ
        "OK",  # Oklahoma - ODEQ
        "WY",  # Wyoming - WDEQ
        "NM",  # New Mexico - NMED
        "CO",  # Colorado - CDPHE
        "ND",  # North Dakota - NDDEQ
        "LA",  # Louisiana - LDEQ
        "PA",  # Pennsylvania - DEP
    ])
    
    # State agency URLs
    state_agency_urls: dict = Field(default={
        "TX": "https://www.tceq.texas.gov",
        "OK": "https://www.deq.ok.gov",
        "WY": "https://deq.wyoming.gov",
        "NM": "https://www.env.nm.gov",
        "CO": "https://cdphe.colorado.gov",
        "ND": "https://deq.nd.gov",
        "LA": "https://deq.louisiana.gov",
        "PA": "https://www.dep.pa.gov",
    })
    
    class Config:
        env_prefix = "STATE_"
        extra = "ignore"


class AgentSettings(BaseSettings):
    """Agent behavior configuration."""
    
    # Execution settings
    max_iterations: int = Field(default=10, description="Max iterations per agent task")
    verbose: bool = Field(default=True, description="Verbose agent output")
    
    # Memory settings
    memory_window: int = Field(default=50, description="Number of recent decisions to remember")
    
    # Thresholds
    critical_risk_threshold: float = Field(default=0.8, description="Risk score for critical classification")
    high_risk_threshold: float = Field(default=0.6, description="Risk score for high classification")
    medium_risk_threshold: float = Field(default=0.3, description="Risk score for medium classification")
    
    # Deadlines
    critical_deadline_days: int = Field(default=30, description="Days until deadline for critical")
    high_deadline_days: int = Field(default=90, description="Days until deadline for high priority")
    
    # Report settings
    report_output_dir: str = Field(default="./reports", description="Directory for generated reports")
    
    class Config:
        env_prefix = "AGENT_"
        extra = "ignore"


class NotificationSettings(BaseSettings):
    """Notification and alerting configuration."""
    
    # Email settings
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    alert_email: Optional[str] = Field(default=None, alias="ALERT_EMAIL")
    
    # Slack integration
    slack_webhook_url: Optional[str] = Field(default=None, alias="SLACK_WEBHOOK_URL")
    
    # Alert thresholds
    alert_on_critical: bool = True
    alert_on_high: bool = True
    alert_on_new_regulation: bool = True
    daily_digest: bool = True
    digest_time: str = "08:00"
    
    class Config:
        env_prefix = "NOTIFY_"
        extra = "ignore"


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = "EnviroComply"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Sub-settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    weaviate: WeaviateSettings = Field(default_factory=WeaviateSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    epa: EPASettings = Field(default_factory=EPASettings)
    state: StateRegulationSettings = Field(default_factory=StateRegulationSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience accessor
settings = get_settings()
