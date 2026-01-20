"""
Base Agent
==========
Abstract base class for all EnviroComply agents with shared capabilities.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4
import asyncio
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from core.config import settings
from core.models import AgentDecision
from core.exceptions import AgentError, LLMError


class BaseAgent(ABC):
    """
    Abstract base class for EnviroComply agents.
    
    Provides:
    - LLM integration with fallback
    - Memory access for context
    - Decision logging
    - Common utilities
    """
    
    def __init__(
        self,
        agent_id: str = None,
        memory_store = None,
    ):
        self.agent_id = agent_id or f"{self.agent_type}_{uuid4().hex[:8]}"
        self.memory_store = memory_store
        self.llm = self._initialize_llm()
        self.decision_history: List[AgentDecision] = []
        
        logger.info(f"Initialized {self.agent_type} agent: {self.agent_id}")
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return the agent type identifier."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @property
    def description(self) -> str:
        """Return a description of the agent's purpose."""
        return f"{self.agent_type} agent"
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the LLM client."""
        llm_settings = settings.llm
        
        if llm_settings.provider == "openai":
            return ChatOpenAI(
                model=llm_settings.openai_model,
                temperature=llm_settings.openai_temperature,
                max_tokens=llm_settings.max_tokens,
                api_key=llm_settings.openai_api_key,
            )
        else:
            # Fallback to Ollama
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=llm_settings.ollama_model,
                base_url=llm_settings.ollama_base_url,
            )
    
    async def think(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        examples: List[Dict] = None,
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The main prompt/question
            context: Additional context to include
            examples: Few-shot examples
            
        Returns:
            LLM response text
        """
        try:
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add context if provided
            if context:
                context_str = self._format_context(context)
                messages.append(HumanMessage(content=f"Context:\n{context_str}"))
            
            # Add examples if provided
            if examples:
                for example in examples:
                    messages.append(HumanMessage(content=example.get("input", "")))
                    messages.append(AIMessage(content=example.get("output", "")))
            
            # Add main prompt
            messages.append(HumanMessage(content=prompt))
            
            # Generate response
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"LLM error in {self.agent_type}: {e}")
            raise LLMError(settings.llm.provider, str(e))
    
    async def think_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured response from the LLM.
        
        Args:
            prompt: The main prompt
            output_schema: Expected output structure
            context: Additional context
            
        Returns:
            Parsed structured response
        """
        import json
        
        schema_str = json.dumps(output_schema, indent=2)
        
        structured_prompt = f"""{prompt}

Respond with a valid JSON object matching this schema:
{schema_str}

Respond ONLY with the JSON object, no other text."""
        
        response = await self.think(structured_prompt, context)
        
        # Parse JSON from response
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse structured response: {e}")
            return {"raw_response": response, "parse_error": str(e)}
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for LLM consumption."""
        lines = []
        for key, value in context.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value[:10]:  # Limit to 10 items
                    lines.append(f"  - {item}")
            elif isinstance(value, dict):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    async def get_relevant_memory(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant past decisions from memory."""
        if not self.memory_store:
            return []
        
        try:
            return await self.memory_store.get_similar_decisions(
                context=query,
                agent_type=self.agent_type,
                limit=limit,
            )
        except Exception as e:
            logger.warning(f"Failed to retrieve memory: {e}")
            return []
    
    async def log_decision(
        self,
        decision_type: str,
        action_taken: str,
        reasoning: str,
        confidence: float,
        input_data: Dict = None,
        output_data: Dict = None,
        facility_ids: List[str] = None,
        regulation_ids: List[str] = None,
    ) -> AgentDecision:
        """Log a decision made by this agent."""
        decision = AgentDecision(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            decision_type=decision_type,
            action_taken=action_taken,
            reasoning=reasoning,
            confidence=confidence,
            input_data=input_data or {},
            output_data=output_data or {},
            facility_ids=facility_ids or [],
            regulation_ids=regulation_ids or [],
        )
        
        self.decision_history.append(decision)
        
        # Store in memory if available
        if self.memory_store:
            try:
                await self.memory_store.store_agent_decision(decision)
            except Exception as e:
                logger.warning(f"Failed to store decision in memory: {e}")
        
        logger.info(
            f"[{self.agent_type}] Decision: {decision_type} - {action_taken[:50]}... "
            f"(confidence: {confidence:.2f})"
        )
        
        return decision
    
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main task.
        
        Returns:
            Dictionary containing results and any generated data
        """
        pass
    
    async def health_check(self) -> bool:
        """Check if the agent is functioning properly."""
        try:
            response = await self.think("Respond with 'OK' if you are functioning.")
            return "OK" in response.upper()
        except Exception as e:
            logger.error(f"Health check failed for {self.agent_type}: {e}")
            return False


class AgentContext:
    """
    Shared context for multi-agent coordination.
    
    Provides a way for agents to share information during
    a coordinated analysis run.
    """
    
    def __init__(self):
        self.regulations: List[Dict] = []
        self.facilities: List[Dict] = []
        self.gaps: List[Dict] = []
        self.decisions: List[AgentDecision] = []
        self.alerts: List[Dict] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
    
    def add_regulation(self, regulation: Dict):
        """Add a regulation to the context."""
        self.regulations.append(regulation)
    
    def add_facility(self, facility: Dict):
        """Add a facility to the context."""
        self.facilities.append(facility)
    
    def add_gap(self, gap: Dict):
        """Add a compliance gap to the context."""
        self.gaps.append(gap)
    
    def add_decision(self, decision: AgentDecision):
        """Add an agent decision to the context."""
        self.decisions.append(decision)
    
    def add_alert(self, alert: Dict):
        """Add an alert to the context."""
        self.alerts.append(alert)
    
    def get_summary(self) -> Dict:
        """Get a summary of the context."""
        return {
            "regulations_count": len(self.regulations),
            "facilities_count": len(self.facilities),
            "gaps_count": len(self.gaps),
            "decisions_count": len(self.decisions),
            "alerts_count": len(self.alerts),
            "critical_gaps": len([g for g in self.gaps if g.get("severity") == "critical"]),
            "created_at": self.created_at.isoformat(),
        }
