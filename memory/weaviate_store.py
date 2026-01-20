"""
Weaviate Memory Store
=====================
Vector database operations for storing and retrieving regulatory documents,
facility profiles, compliance records, and agent memory.
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery, Filter
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from loguru import logger

from core.config import settings
from core.models import Regulation, Facility, ComplianceGap, AgentDecision
from core.exceptions import WeaviateError


class WeaviateStore:
    """
    Vector database store using Weaviate for semantic search
    over regulatory documents and compliance data.
    """
    
    def __init__(self):
        self.client = None
        self.settings = settings.weaviate
        
    async def connect(self):
        """Connect to Weaviate instance."""
        try:
            if self.settings.api_key:
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.settings.url,
                    auth_credentials=Auth.api_key(self.settings.api_key),
                )
            else:
                self.client = weaviate.connect_to_local(
                    host=self.settings.url.replace("http://", "").replace("https://", "").split(":")[0],
                    port=int(self.settings.url.split(":")[-1]) if ":" in self.settings.url else 8080,
                )
            
            logger.info(f"Connected to Weaviate at {self.settings.url}")
            
            # Initialize collections
            await self._initialize_collections()
            
        except Exception as e:
            raise WeaviateError("connect", str(e))
    
    async def disconnect(self):
        """Disconnect from Weaviate."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from Weaviate")
    
    async def _initialize_collections(self):
        """Create collections if they don't exist."""
        collections = [
            self._get_regulation_collection_config(),
            self._get_facility_collection_config(),
            self._get_compliance_gap_collection_config(),
            self._get_agent_memory_collection_config(),
        ]
        
        for config in collections:
            name = config["name"]
            if not self.client.collections.exists(name):
                self.client.collections.create(**config)
                logger.info(f"Created collection: {name}")
            else:
                logger.debug(f"Collection exists: {name}")
    
    def _get_regulation_collection_config(self) -> Dict:
        """Get Regulation collection configuration."""
        return {
            "name": self.settings.regulations_collection,
            "description": "EPA and state environmental regulations for Oil & Gas",
            "vectorizer_config": Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small"
            ),
            "properties": [
                Property(name="regulation_id", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="citation", data_type=DataType.TEXT),
                Property(name="regulation_type", data_type=DataType.TEXT),
                Property(name="status", data_type=DataType.TEXT),
                Property(name="full_text", data_type=DataType.TEXT),
                Property(name="key_requirements", data_type=DataType.TEXT_ARRAY),
                Property(name="applicable_facility_types", data_type=DataType.TEXT_ARRAY),
                Property(name="effective_date", data_type=DataType.DATE),
                Property(name="compliance_deadline", data_type=DataType.DATE),
                Property(name="sector_segments", data_type=DataType.TEXT_ARRAY),
                Property(name="metadata", data_type=DataType.TEXT),
            ],
        }
    
    def _get_facility_collection_config(self) -> Dict:
        """Get Facility collection configuration."""
        return {
            "name": self.settings.facilities_collection,
            "description": "Oil & Gas facility profiles",
            "vectorizer_config": Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small"
            ),
            "properties": [
                Property(name="facility_id", data_type=DataType.TEXT),
                Property(name="name", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="facility_type", data_type=DataType.TEXT),
                Property(name="state", data_type=DataType.TEXT),
                Property(name="county", data_type=DataType.TEXT),
                Property(name="operator", data_type=DataType.TEXT),
                Property(name="emission_sources_text", data_type=DataType.TEXT),
                Property(name="permits_text", data_type=DataType.TEXT),
                Property(name="is_major_source", data_type=DataType.BOOL),
                Property(name="title_v_applicable", data_type=DataType.BOOL),
                Property(name="metadata", data_type=DataType.TEXT),
            ],
        }
    
    def _get_compliance_gap_collection_config(self) -> Dict:
        """Get ComplianceGap collection configuration."""
        return {
            "name": self.settings.compliance_collection,
            "description": "Identified compliance gaps",
            "vectorizer_config": Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small"
            ),
            "properties": [
                Property(name="gap_id", data_type=DataType.TEXT),
                Property(name="facility_id", data_type=DataType.TEXT),
                Property(name="regulation_id", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="severity", data_type=DataType.TEXT),
                Property(name="status", data_type=DataType.TEXT),
                Property(name="risk_score", data_type=DataType.NUMBER),
                Property(name="recommended_action", data_type=DataType.TEXT),
                Property(name="regulatory_deadline", data_type=DataType.DATE),
                Property(name="identified_at", data_type=DataType.DATE),
                Property(name="metadata", data_type=DataType.TEXT),
            ],
        }
    
    def _get_agent_memory_collection_config(self) -> Dict:
        """Get AgentMemory collection configuration."""
        return {
            "name": self.settings.agent_memory_collection,
            "description": "Agent decisions and reasoning history",
            "vectorizer_config": Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small"
            ),
            "properties": [
                Property(name="decision_id", data_type=DataType.TEXT),
                Property(name="agent_id", data_type=DataType.TEXT),
                Property(name="agent_type", data_type=DataType.TEXT),
                Property(name="decision_type", data_type=DataType.TEXT),
                Property(name="action_taken", data_type=DataType.TEXT),
                Property(name="reasoning", data_type=DataType.TEXT),
                Property(name="confidence", data_type=DataType.NUMBER),
                Property(name="timestamp", data_type=DataType.DATE),
                Property(name="context", data_type=DataType.TEXT),
            ],
        }
    
    # ========================================================================
    # Regulation Operations
    # ========================================================================
    
    async def store_regulation(self, regulation: Regulation) -> str:
        """Store a regulation document."""
        try:
            collection = self.client.collections.get(self.settings.regulations_collection)
            
            data = {
                "regulation_id": regulation.id,
                "title": regulation.title,
                "description": regulation.description,
                "citation": regulation.citation,
                "regulation_type": regulation.regulation_type.value,
                "status": regulation.status.value,
                "full_text": regulation.full_text or "",
                "key_requirements": regulation.key_requirements,
                "applicable_facility_types": [ft.value for ft in regulation.applicable_facility_types],
                "effective_date": regulation.effective_date.isoformat() if regulation.effective_date else None,
                "compliance_deadline": regulation.compliance_deadline.isoformat() if regulation.compliance_deadline else None,
                "sector_segments": regulation.sector_segments,
                "metadata": json.dumps({
                    "source_url": regulation.source_url,
                    "federal_register_citation": regulation.federal_register_citation,
                    "monitoring_requirements": regulation.monitoring_requirements,
                    "recordkeeping_requirements": regulation.recordkeeping_requirements,
                    "reporting_requirements": regulation.reporting_requirements,
                }),
            }
            
            uuid = collection.data.insert(data)
            logger.info(f"Stored regulation: {regulation.title} ({uuid})")
            return str(uuid)
            
        except Exception as e:
            raise WeaviateError("store_regulation", str(e))
    
    async def search_regulations(
        self,
        query: str,
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict]:
        """
        Semantic search over regulations.
        
        Args:
            query: Search query (e.g., "methane emissions monitoring requirements")
            limit: Maximum results to return
            filters: Optional filters (e.g., {"regulation_type": "nsps"})
        """
        try:
            collection = self.client.collections.get(self.settings.regulations_collection)
            
            # Build filter if provided
            weaviate_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(Filter.by_property(key).equal(value))
                if len(conditions) == 1:
                    weaviate_filter = conditions[0]
                else:
                    weaviate_filter = Filter.all_of(conditions)
            
            response = collection.query.near_text(
                query=query,
                limit=limit,
                filters=weaviate_filter,
                return_metadata=MetadataQuery(distance=True),
            )
            
            results = []
            for obj in response.objects:
                result = obj.properties.copy()
                result["_distance"] = obj.metadata.distance
                result["_uuid"] = str(obj.uuid)
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                results.append(result)
            
            return results
            
        except Exception as e:
            raise WeaviateError("search_regulations", str(e))
    
    async def get_regulation_by_citation(self, citation: str) -> Optional[Dict]:
        """Get a regulation by its CFR citation."""
        try:
            collection = self.client.collections.get(self.settings.regulations_collection)
            
            response = collection.query.fetch_objects(
                filters=Filter.by_property("citation").equal(citation),
                limit=1,
            )
            
            if response.objects:
                result = response.objects[0].properties.copy()
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                return result
            
            return None
            
        except Exception as e:
            raise WeaviateError("get_regulation_by_citation", str(e))
    
    async def get_applicable_regulations(
        self,
        facility_type: str,
        state: str = None
    ) -> List[Dict]:
        """Get regulations applicable to a facility type."""
        try:
            collection = self.client.collections.get(self.settings.regulations_collection)
            
            # Search for regulations mentioning this facility type
            response = collection.query.near_text(
                query=f"{facility_type} oil gas facility requirements",
                limit=50,
                return_metadata=MetadataQuery(distance=True),
            )
            
            results = []
            for obj in response.objects:
                props = obj.properties
                applicable_types = props.get("applicable_facility_types", [])
                
                # Filter by facility type
                if facility_type.lower() in [ft.lower() for ft in applicable_types]:
                    result = props.copy()
                    result["_distance"] = obj.metadata.distance
                    if result.get("metadata"):
                        result["metadata"] = json.loads(result["metadata"])
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise WeaviateError("get_applicable_regulations", str(e))
    
    # ========================================================================
    # Facility Operations
    # ========================================================================
    
    async def store_facility(self, facility: Facility) -> str:
        """Store a facility profile."""
        try:
            collection = self.client.collections.get(self.settings.facilities_collection)
            
            # Create text representation of emission sources for search
            sources_text = "\n".join([
                f"{s.name}: {s.source_type.value} - {s.equipment_type}"
                for s in facility.emission_sources
            ])
            
            # Create text representation of permits
            permits_text = "\n".join([
                f"{p.permit_number}: {p.permit_type} ({p.status})"
                for p in facility.permits
            ])
            
            data = {
                "facility_id": facility.id,
                "name": facility.name,
                "description": facility.description or "",
                "facility_type": facility.facility_type.value,
                "state": facility.state,
                "county": facility.county,
                "operator": facility.operator,
                "emission_sources_text": sources_text,
                "permits_text": permits_text,
                "is_major_source": facility.is_major_source,
                "title_v_applicable": facility.title_v_applicable,
                "metadata": json.dumps({
                    "emission_sources": [s.model_dump() for s in facility.emission_sources],
                    "permits": [p.model_dump() for p in facility.permits],
                    "total_potential_emissions_tpy": facility.total_potential_emissions_tpy,
                    "epa_id": facility.epa_id,
                    "state_id": facility.state_id,
                }),
            }
            
            uuid = collection.data.insert(data)
            logger.info(f"Stored facility: {facility.name} ({uuid})")
            return str(uuid)
            
        except Exception as e:
            raise WeaviateError("store_facility", str(e))
    
    async def get_facility(self, facility_id: str) -> Optional[Dict]:
        """Get a facility by ID."""
        try:
            collection = self.client.collections.get(self.settings.facilities_collection)
            
            response = collection.query.fetch_objects(
                filters=Filter.by_property("facility_id").equal(facility_id),
                limit=1,
            )
            
            if response.objects:
                result = response.objects[0].properties.copy()
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                return result
            
            return None
            
        except Exception as e:
            raise WeaviateError("get_facility", str(e))
    
    async def get_all_facilities(self) -> List[Dict]:
        """Get all facilities."""
        try:
            collection = self.client.collections.get(self.settings.facilities_collection)
            
            response = collection.query.fetch_objects(limit=1000)
            
            results = []
            for obj in response.objects:
                result = obj.properties.copy()
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                results.append(result)
            
            return results
            
        except Exception as e:
            raise WeaviateError("get_all_facilities", str(e))
    
    # ========================================================================
    # Compliance Gap Operations
    # ========================================================================
    
    async def store_gap(self, gap: ComplianceGap) -> str:
        """Store a compliance gap."""
        try:
            collection = self.client.collections.get(self.settings.compliance_collection)
            
            data = {
                "gap_id": gap.id,
                "facility_id": gap.facility_id,
                "regulation_id": gap.regulation_id,
                "title": gap.title,
                "description": gap.description,
                "severity": gap.severity.value,
                "status": gap.status.value,
                "risk_score": gap.risk_score,
                "recommended_action": gap.recommended_action,
                "regulatory_deadline": gap.regulatory_deadline.isoformat() if gap.regulatory_deadline else None,
                "identified_at": gap.identified_at.isoformat(),
                "metadata": json.dumps({
                    "potential_fine": gap.potential_fine,
                    "estimated_cost": gap.estimated_cost,
                    "estimated_effort_hours": gap.estimated_effort_hours,
                    "evidence": gap.evidence,
                }),
            }
            
            uuid = collection.data.insert(data)
            logger.info(f"Stored gap: {gap.title} ({uuid})")
            return str(uuid)
            
        except Exception as e:
            raise WeaviateError("store_gap", str(e))
    
    async def get_facility_gaps(
        self,
        facility_id: str,
        status: str = None,
        severity: str = None
    ) -> List[Dict]:
        """Get compliance gaps for a facility."""
        try:
            collection = self.client.collections.get(self.settings.compliance_collection)
            
            conditions = [Filter.by_property("facility_id").equal(facility_id)]
            if status:
                conditions.append(Filter.by_property("status").equal(status))
            if severity:
                conditions.append(Filter.by_property("severity").equal(severity))
            
            filter_obj = Filter.all_of(conditions) if len(conditions) > 1 else conditions[0]
            
            response = collection.query.fetch_objects(
                filters=filter_obj,
                limit=100,
            )
            
            results = []
            for obj in response.objects:
                result = obj.properties.copy()
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                results.append(result)
            
            return results
            
        except Exception as e:
            raise WeaviateError("get_facility_gaps", str(e))
    
    async def search_similar_gaps(self, description: str, limit: int = 5) -> List[Dict]:
        """Find similar compliance gaps (for pattern recognition)."""
        try:
            collection = self.client.collections.get(self.settings.compliance_collection)
            
            response = collection.query.near_text(
                query=description,
                limit=limit,
                return_metadata=MetadataQuery(distance=True),
            )
            
            results = []
            for obj in response.objects:
                result = obj.properties.copy()
                result["_distance"] = obj.metadata.distance
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                results.append(result)
            
            return results
            
        except Exception as e:
            raise WeaviateError("search_similar_gaps", str(e))
    
    # ========================================================================
    # Agent Memory Operations
    # ========================================================================
    
    async def store_agent_decision(self, decision: AgentDecision) -> str:
        """Store an agent decision for learning."""
        try:
            collection = self.client.collections.get(self.settings.agent_memory_collection)
            
            data = {
                "decision_id": decision.id,
                "agent_id": decision.agent_id,
                "agent_type": decision.agent_type,
                "decision_type": decision.decision_type,
                "action_taken": decision.action_taken,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
                "timestamp": decision.timestamp.isoformat(),
                "context": json.dumps({
                    "input_data": decision.input_data,
                    "output_data": decision.output_data,
                    "facility_ids": decision.facility_ids,
                    "regulation_ids": decision.regulation_ids,
                }),
            }
            
            uuid = collection.data.insert(data)
            return str(uuid)
            
        except Exception as e:
            raise WeaviateError("store_agent_decision", str(e))
    
    async def get_similar_decisions(
        self,
        context: str,
        agent_type: str = None,
        limit: int = 5
    ) -> List[Dict]:
        """Find similar past decisions for learning."""
        try:
            collection = self.client.collections.get(self.settings.agent_memory_collection)
            
            filter_obj = None
            if agent_type:
                filter_obj = Filter.by_property("agent_type").equal(agent_type)
            
            response = collection.query.near_text(
                query=context,
                limit=limit,
                filters=filter_obj,
                return_metadata=MetadataQuery(distance=True),
            )
            
            results = []
            for obj in response.objects:
                result = obj.properties.copy()
                result["_distance"] = obj.metadata.distance
                if result.get("context"):
                    result["context"] = json.loads(result["context"])
                results.append(result)
            
            return results
            
        except Exception as e:
            raise WeaviateError("get_similar_decisions", str(e))


# Singleton instance
_store: Optional[WeaviateStore] = None


async def get_weaviate_store() -> WeaviateStore:
    """Get or create the Weaviate store instance."""
    global _store
    if _store is None:
        _store = WeaviateStore()
        await _store.connect()
    return _store
