-- EnviroComply Database Initialization
-- =====================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS enviro;

-- Set search path
SET search_path TO enviro, public;

-- ============================================================================
-- Facilities Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS facilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    facility_type VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Location
    address VARCHAR(255),
    city VARCHAR(100),
    county VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(20),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    
    -- Regulatory IDs
    epa_id VARCHAR(50),
    state_id VARCHAR(50),
    frs_id VARCHAR(50),
    
    -- Classification
    sic_code VARCHAR(10),
    naics_code VARCHAR(10),
    operator VARCHAR(255) NOT NULL,
    operational_status VARCHAR(50) DEFAULT 'active',
    
    -- Compliance status
    is_major_source BOOLEAN DEFAULT FALSE,
    title_v_applicable BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_compliance_review TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_facilities_state ON facilities(state);
CREATE INDEX idx_facilities_type ON facilities(facility_type);
CREATE INDEX idx_facilities_operator ON facilities(operator);

-- ============================================================================
-- Regulations Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS regulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulation_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    citation VARCHAR(100) NOT NULL,
    
    -- Classification
    regulation_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    
    -- Dates
    publication_date DATE,
    effective_date DATE,
    compliance_deadline DATE,
    
    -- Content
    key_requirements JSONB DEFAULT '[]'::JSONB,
    monitoring_requirements JSONB DEFAULT '[]'::JSONB,
    recordkeeping_requirements JSONB DEFAULT '[]'::JSONB,
    reporting_requirements JSONB DEFAULT '[]'::JSONB,
    
    -- Source
    source_url TEXT,
    federal_register_citation VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_checked TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_regulations_type ON regulations(regulation_type);
CREATE INDEX idx_regulations_status ON regulations(status);
CREATE INDEX idx_regulations_deadline ON regulations(compliance_deadline);

-- ============================================================================
-- Compliance Gaps Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS compliance_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gap_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Relationships
    facility_id UUID REFERENCES facilities(id),
    regulation_id UUID REFERENCES regulations(id),
    
    -- Gap details
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    
    -- Risk assessment
    risk_score DECIMAL(3, 2),
    potential_fine DECIMAL(12, 2),
    enforcement_likelihood DECIMAL(3, 2),
    
    -- Deadlines
    regulatory_deadline DATE,
    internal_deadline DATE,
    
    -- Remediation
    recommended_action TEXT,
    estimated_cost DECIMAL(12, 2),
    estimated_effort_hours DECIMAL(8, 2),
    responsible_party VARCHAR(255),
    
    -- Resolution
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    
    -- Tracking
    identified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    identified_by VARCHAR(100) DEFAULT 'gap_analyzer_agent',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_gaps_facility ON compliance_gaps(facility_id);
CREATE INDEX idx_gaps_severity ON compliance_gaps(severity);
CREATE INDEX idx_gaps_status ON compliance_gaps(status);
CREATE INDEX idx_gaps_deadline ON compliance_gaps(regulatory_deadline);

-- ============================================================================
-- Agent Decisions Table (Audit Trail)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Agent info
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    
    -- Decision details
    decision_type VARCHAR(100) NOT NULL,
    action_taken TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL,
    
    -- Context
    input_data JSONB DEFAULT '{}'::JSONB,
    output_data JSONB DEFAULT '{}'::JSONB,
    
    -- Related entities
    facility_ids JSONB DEFAULT '[]'::JSONB,
    regulation_ids JSONB DEFAULT '[]'::JSONB,
    gap_ids JSONB DEFAULT '[]'::JSONB,
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_time_ms DECIMAL(10, 2),
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

CREATE INDEX idx_decisions_agent ON agent_decisions(agent_type);
CREATE INDEX idx_decisions_type ON agent_decisions(decision_type);
CREATE INDEX idx_decisions_timestamp ON agent_decisions(timestamp);

-- ============================================================================
-- Reports Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Report info
    report_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    
    -- Content
    executive_summary TEXT,
    compliance_score DECIMAL(5, 2),
    
    -- Related entities
    facility_ids JSONB DEFAULT '[]'::JSONB,
    gap_ids JSONB DEFAULT '[]'::JSONB,
    regulation_ids JSONB DEFAULT '[]'::JSONB,
    
    -- Period
    reporting_period_start DATE,
    reporting_period_end DATE,
    
    -- Output
    file_path TEXT,
    format VARCHAR(20) DEFAULT 'pdf',
    
    -- Metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by VARCHAR(100) DEFAULT 'report_generator_agent'
);

CREATE INDEX idx_reports_type ON reports(report_type);
CREATE INDEX idx_reports_generated ON reports(generated_at);

-- ============================================================================
-- Regulatory Alerts Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS regulatory_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Alert info
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    
    -- Related regulation
    regulation_id UUID REFERENCES regulations(id),
    regulation_citation VARCHAR(100),
    
    -- Deadline
    deadline DATE,
    days_until_deadline INTEGER,
    
    -- Status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_severity ON regulatory_alerts(severity);
CREATE INDEX idx_alerts_deadline ON regulatory_alerts(deadline);
CREATE INDEX idx_alerts_acknowledged ON regulatory_alerts(acknowledged);

-- ============================================================================
-- Functions
-- ============================================================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER update_facilities_timestamp
    BEFORE UPDATE ON facilities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_regulations_timestamp
    BEFORE UPDATE ON regulations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_gaps_timestamp
    BEFORE UPDATE ON compliance_gaps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- Views
-- ============================================================================

-- Facility compliance summary view
CREATE OR REPLACE VIEW facility_compliance_summary AS
SELECT 
    f.id,
    f.facility_id,
    f.name,
    f.facility_type,
    f.state,
    f.operator,
    COUNT(g.id) AS total_gaps,
    COUNT(CASE WHEN g.severity = 'critical' THEN 1 END) AS critical_gaps,
    COUNT(CASE WHEN g.severity = 'high' THEN 1 END) AS high_gaps,
    COUNT(CASE WHEN g.severity = 'medium' THEN 1 END) AS medium_gaps,
    COUNT(CASE WHEN g.severity = 'low' THEN 1 END) AS low_gaps,
    COALESCE(SUM(g.estimated_cost), 0) AS total_remediation_cost,
    MIN(g.regulatory_deadline) AS nearest_deadline
FROM facilities f
LEFT JOIN compliance_gaps g ON f.id = g.facility_id AND g.status = 'open'
GROUP BY f.id, f.facility_id, f.name, f.facility_type, f.state, f.operator;

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'EnviroComply database initialized successfully';
END $$;
