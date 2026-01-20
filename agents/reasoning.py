"""
Agent Reasoning Module
======================
Enhanced reasoning capabilities for compliance agents including:
- Chain-of-thought reasoning
- Multi-step analysis
- Confidence calibration
- Decision explanation
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from loguru import logger


class ReasoningType(str, Enum):
    """Types of reasoning steps."""
    OBSERVATION = "observation"
    ANALYSIS = "analysis"
    INFERENCE = "inference"
    DECISION = "decision"
    VALIDATION = "validation"


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""
    step_number: int
    step_type: ReasoningType
    content: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "type": self.step_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ReasoningChain:
    """Complete chain of reasoning for a decision."""
    task_id: str
    agent_type: str
    question: str
    steps: List[ReasoningStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    final_confidence: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def add_step(
        self,
        step_type: ReasoningType,
        content: str,
        confidence: float,
        evidence: List[str] = None
    ) -> ReasoningStep:
        """Add a reasoning step to the chain."""
        step = ReasoningStep(
            step_number=len(self.steps) + 1,
            step_type=step_type,
            content=content,
            confidence=confidence,
            evidence=evidence or []
        )
        self.steps.append(step)
        return step
    
    def complete(self, answer: str, confidence: float):
        """Mark the reasoning chain as complete."""
        self.final_answer = answer
        self.final_confidence = confidence
        self.completed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type,
            "question": self.question,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "final_confidence": self.final_confidence,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": (
                (self.completed_at - self.started_at).total_seconds() * 1000
                if self.completed_at else None
            )
        }
    
    def to_explanation(self) -> str:
        """Generate human-readable explanation."""
        lines = [
            f"## Reasoning for: {self.question}",
            ""
        ]
        
        for step in self.steps:
            emoji = {
                ReasoningType.OBSERVATION: "👁️",
                ReasoningType.ANALYSIS: "🔍",
                ReasoningType.INFERENCE: "💡",
                ReasoningType.DECISION: "✅",
                ReasoningType.VALIDATION: "✓"
            }.get(step.step_type, "•")
            
            lines.append(f"**Step {step.step_number}** ({step.step_type.value}) {emoji}")
            lines.append(f"{step.content}")
            
            if step.evidence:
                lines.append("*Evidence:*")
                for ev in step.evidence:
                    lines.append(f"  - {ev}")
            
            lines.append(f"*Confidence: {step.confidence*100:.0f}%*")
            lines.append("")
        
        if self.final_answer:
            lines.append("---")
            lines.append(f"**Conclusion:** {self.final_answer}")
            lines.append(f"**Overall Confidence:** {self.final_confidence*100:.0f}%")
        
        return "\n".join(lines)


class ChainOfThoughtReasoner:
    """
    Implements chain-of-thought reasoning for compliance analysis.
    
    This enables agents to:
    1. Break down complex problems into steps
    2. Show their reasoning explicitly
    3. Calibrate confidence based on evidence
    4. Validate conclusions before finalizing
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.chains: List[ReasoningChain] = []
    
    def start_chain(self, task_id: str, question: str) -> ReasoningChain:
        """Start a new reasoning chain."""
        chain = ReasoningChain(
            task_id=task_id,
            agent_type=self.agent_type,
            question=question
        )
        self.chains.append(chain)
        return chain
    
    def reason_about_regulation_relevance(
        self,
        regulation: Dict[str, Any],
        target_industry: str = "oil_and_gas"
    ) -> Tuple[bool, float, ReasoningChain]:
        """
        Determine if a regulation is relevant to the target industry.
        
        Returns:
            Tuple of (is_relevant, confidence, reasoning_chain)
        """
        chain = self.start_chain(
            task_id=f"rel_{regulation.get('id', 'unknown')}",
            question=f"Is '{regulation.get('title', 'Unknown')}' relevant to {target_industry}?"
        )
        
        # Step 1: Observe the regulation content
        title = regulation.get("title", "").lower()
        description = regulation.get("description", "").lower()
        citation = regulation.get("citation", "")
        
        chain.add_step(
            ReasoningType.OBSERVATION,
            f"Examining regulation: {citation} - {regulation.get('title', 'Unknown')}",
            confidence=1.0,
            evidence=[f"Title: {title[:100]}...", f"Citation: {citation}"]
        )
        
        # Step 2: Check for industry keywords
        og_keywords = [
            "oil", "gas", "petroleum", "natural gas", "crude oil",
            "wellsite", "wellhead", "compressor", "gathering",
            "processing", "transmission", "storage tank", "pneumatic",
            "fugitive emissions", "ldar", "methane", "voc"
        ]
        
        text_to_search = f"{title} {description}"
        found_keywords = [kw for kw in og_keywords if kw in text_to_search]
        
        keyword_confidence = min(len(found_keywords) / 3, 1.0)  # 3+ keywords = high confidence
        
        chain.add_step(
            ReasoningType.ANALYSIS,
            f"Searched for {len(og_keywords)} O&G keywords in regulation text",
            confidence=keyword_confidence,
            evidence=[f"Found keywords: {', '.join(found_keywords[:5])}"] if found_keywords else ["No keywords found"]
        )
        
        # Step 3: Check CFR citation
        cfr_relevance = 0.0
        cfr_evidence = []
        
        if "40 CFR 60" in citation:
            cfr_relevance = 0.8
            cfr_evidence.append("40 CFR 60 (NSPS) - includes O&G subparts OOOO, OOOOa, OOOOb")
        elif "40 CFR 63" in citation:
            cfr_relevance = 0.7
            cfr_evidence.append("40 CFR 63 (NESHAP) - includes O&G subpart HH")
        elif "40 CFR 98" in citation:
            cfr_relevance = 0.6
            cfr_evidence.append("40 CFR 98 (GHG Reporting) - includes O&G subpart W")
        
        if cfr_relevance > 0:
            chain.add_step(
                ReasoningType.ANALYSIS,
                f"CFR citation analysis indicates potential O&G applicability",
                confidence=cfr_relevance,
                evidence=cfr_evidence
            )
        
        # Step 4: Make inference
        combined_score = (keyword_confidence * 0.6) + (cfr_relevance * 0.4)
        is_relevant = combined_score > 0.3
        
        chain.add_step(
            ReasoningType.INFERENCE,
            f"Combined analysis suggests {'HIGH' if combined_score > 0.6 else 'MODERATE' if combined_score > 0.3 else 'LOW'} relevance",
            confidence=combined_score,
            evidence=[
                f"Keyword score: {keyword_confidence:.2f}",
                f"CFR relevance: {cfr_relevance:.2f}",
                f"Combined: {combined_score:.2f}"
            ]
        )
        
        # Step 5: Validation
        if is_relevant and combined_score < 0.5:
            chain.add_step(
                ReasoningType.VALIDATION,
                "Low confidence relevance - recommend manual review",
                confidence=combined_score,
                evidence=["Borderline score warrants human verification"]
            )
        
        # Complete the chain
        chain.complete(
            answer="RELEVANT" if is_relevant else "NOT RELEVANT",
            confidence=combined_score
        )
        
        return is_relevant, combined_score, chain
    
    def reason_about_gap_severity(
        self,
        gap: Dict[str, Any],
        facility: Dict[str, Any]
    ) -> Tuple[str, float, ReasoningChain]:
        """
        Determine the severity of a compliance gap.
        
        Returns:
            Tuple of (severity, confidence, reasoning_chain)
        """
        chain = self.start_chain(
            task_id=f"sev_{gap.get('id', 'unknown')}",
            question=f"What is the severity of gap: {gap.get('title', 'Unknown')}?"
        )
        
        # Step 1: Observe gap characteristics
        chain.add_step(
            ReasoningType.OBSERVATION,
            f"Analyzing gap: {gap.get('title', 'Unknown')} at {facility.get('name', 'Unknown facility')}",
            confidence=1.0,
            evidence=[
                f"Gap type: {gap.get('gap_type', 'unknown')}",
                f"Regulation: {gap.get('regulation_id', 'unknown')}"
            ]
        )
        
        # Step 2: Analyze deadline proximity
        deadline = gap.get("regulatory_deadline")
        deadline_severity = "low"
        deadline_confidence = 0.5
        
        if deadline:
            from datetime import datetime
            try:
                deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                days_until = (deadline_date.replace(tzinfo=None) - datetime.utcnow()).days
                
                if days_until < 0:
                    deadline_severity = "critical"
                    deadline_confidence = 0.95
                    deadline_evidence = f"Deadline PASSED {abs(days_until)} days ago"
                elif days_until < 30:
                    deadline_severity = "critical"
                    deadline_confidence = 0.9
                    deadline_evidence = f"Only {days_until} days until deadline"
                elif days_until < 90:
                    deadline_severity = "high"
                    deadline_confidence = 0.8
                    deadline_evidence = f"{days_until} days until deadline"
                elif days_until < 180:
                    deadline_severity = "medium"
                    deadline_confidence = 0.7
                    deadline_evidence = f"{days_until} days until deadline"
                else:
                    deadline_severity = "low"
                    deadline_confidence = 0.6
                    deadline_evidence = f"{days_until} days until deadline (>6 months)"
                
                chain.add_step(
                    ReasoningType.ANALYSIS,
                    f"Deadline analysis: {deadline_severity.upper()} urgency",
                    confidence=deadline_confidence,
                    evidence=[deadline_evidence]
                )
            except:
                pass
        
        # Step 3: Analyze enforcement risk
        enforcement_keywords = ["nsps", "neshap", "title v", "ghg reporting", "ldar"]
        regulation_id = gap.get("regulation_id", "").lower()
        
        enforcement_risk = "medium"
        enforcement_confidence = 0.5
        
        for kw in enforcement_keywords:
            if kw in regulation_id:
                enforcement_risk = "high"
                enforcement_confidence = 0.8
                break
        
        # EPA priority programs get higher enforcement
        if "oooo" in regulation_id or "methane" in gap.get("title", "").lower():
            enforcement_risk = "high"
            enforcement_confidence = 0.85
        
        chain.add_step(
            ReasoningType.ANALYSIS,
            f"Enforcement risk assessment: {enforcement_risk.upper()}",
            confidence=enforcement_confidence,
            evidence=[
                f"Regulation: {regulation_id}",
                f"EPA enforcement priority: {'YES' if enforcement_risk == 'high' else 'NORMAL'}"
            ]
        )
        
        # Step 4: Consider facility factors
        facility_risk = "medium"
        
        if facility.get("is_major_source"):
            facility_risk = "high"
            chain.add_step(
                ReasoningType.ANALYSIS,
                "Facility is a Major Source - higher regulatory scrutiny",
                confidence=0.85,
                evidence=["Major source status triggers additional requirements"]
            )
        
        # Step 5: Combine factors for final severity
        severity_scores = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        factors = [deadline_severity, enforcement_risk, facility_risk]
        avg_score = sum(severity_scores.get(f, 2) for f in factors) / len(factors)
        
        if avg_score >= 3.5:
            final_severity = "critical"
        elif avg_score >= 2.5:
            final_severity = "high"
        elif avg_score >= 1.5:
            final_severity = "medium"
        else:
            final_severity = "low"
        
        final_confidence = (deadline_confidence + enforcement_confidence + 0.7) / 3
        
        chain.add_step(
            ReasoningType.INFERENCE,
            f"Combined severity assessment: {final_severity.upper()}",
            confidence=final_confidence,
            evidence=[
                f"Deadline factor: {deadline_severity}",
                f"Enforcement factor: {enforcement_risk}",
                f"Facility factor: {facility_risk}",
                f"Average score: {avg_score:.2f}"
            ]
        )
        
        # Step 6: Validation
        chain.add_step(
            ReasoningType.VALIDATION,
            f"Severity determination validated with {final_confidence*100:.0f}% confidence",
            confidence=final_confidence,
            evidence=[
                f"All {len(factors)} risk factors considered",
                f"Final severity: {final_severity.upper()}"
            ]
        )
        
        chain.complete(
            answer=final_severity.upper(),
            confidence=final_confidence
        )
        
        return final_severity, final_confidence, chain
    
    def reason_about_remediation_cost(
        self,
        gap: Dict[str, Any],
        similar_gaps: List[Dict[str, Any]] = None
    ) -> Tuple[float, float, ReasoningChain]:
        """
        Estimate remediation cost for a gap.
        
        Returns:
            Tuple of (estimated_cost, confidence, reasoning_chain)
        """
        chain = self.start_chain(
            task_id=f"cost_{gap.get('id', 'unknown')}",
            question=f"What is the estimated remediation cost for: {gap.get('title', 'Unknown')}?"
        )
        
        # Step 1: Identify gap type
        gap_title = gap.get("title", "").lower()
        gap_type = "unknown"
        
        cost_estimates = {
            "ldar": (3000, 8000),  # Survey costs
            "pneumatic": (500, 2000),  # Per controller
            "storage": (25000, 75000),  # VRU or controls
            "permit": (10000, 25000),  # Application/renewal
            "dehydrator": (40000, 80000),  # Control installation
            "monitoring": (5000, 15000),  # Equipment upgrades
            "documentation": (2000, 5000),  # Paperwork/procedures
        }
        
        for gap_type_key, (low, high) in cost_estimates.items():
            if gap_type_key in gap_title:
                gap_type = gap_type_key
                base_low, base_high = low, high
                break
        else:
            base_low, base_high = 5000, 20000  # Default range
        
        chain.add_step(
            ReasoningType.OBSERVATION,
            f"Gap type identified: {gap_type if gap_type != 'unknown' else 'general compliance'}",
            confidence=0.8 if gap_type != "unknown" else 0.5,
            evidence=[f"Title keywords: {gap_title[:50]}"]
        )
        
        # Step 2: Check for quantity multipliers
        multiplier = 1
        description = gap.get("description", "")
        
        # Look for numbers in description
        import re
        numbers = re.findall(r'\b(\d+)\s*(?:controller|tank|vessel|source|unit)', description.lower())
        if numbers:
            multiplier = int(numbers[0])
            chain.add_step(
                ReasoningType.ANALYSIS,
                f"Found quantity multiplier: {multiplier} units",
                confidence=0.75,
                evidence=[f"Extracted from: '{description[:100]}...'"]
            )
        
        # Step 3: Learn from similar gaps if available
        if similar_gaps:
            similar_costs = [g.get("actual_cost") or g.get("estimated_cost", 0) for g in similar_gaps if g.get("actual_cost") or g.get("estimated_cost")]
            
            if similar_costs:
                avg_similar = sum(similar_costs) / len(similar_costs)
                chain.add_step(
                    ReasoningType.ANALYSIS,
                    f"Found {len(similar_costs)} similar historical gaps",
                    confidence=0.85,
                    evidence=[f"Average historical cost: ${avg_similar:,.0f}"]
                )
                # Weight historical data
                base_low = (base_low + avg_similar * 0.8) / 2
                base_high = (base_high + avg_similar * 1.2) / 2
        
        # Step 4: Calculate estimate
        estimated_cost = ((base_low + base_high) / 2) * multiplier
        cost_range = (base_low * multiplier, base_high * multiplier)
        
        # Confidence based on information quality
        confidence = 0.7
        if gap_type != "unknown":
            confidence += 0.1
        if similar_gaps:
            confidence += 0.1
        if multiplier > 1:
            confidence -= 0.05  # More uncertainty with multiple units
        
        chain.add_step(
            ReasoningType.INFERENCE,
            f"Estimated cost: ${estimated_cost:,.0f} (range: ${cost_range[0]:,.0f} - ${cost_range[1]:,.0f})",
            confidence=confidence,
            evidence=[
                f"Base range: ${base_low:,.0f} - ${base_high:,.0f}",
                f"Multiplier: {multiplier}x",
                f"Gap type: {gap_type}"
            ]
        )
        
        chain.complete(
            answer=f"${estimated_cost:,.0f}",
            confidence=confidence
        )
        
        return estimated_cost, confidence, chain
    
    def get_all_explanations(self) -> List[str]:
        """Get human-readable explanations for all reasoning chains."""
        return [chain.to_explanation() for chain in self.chains]
    
    def export_chains(self) -> List[Dict[str, Any]]:
        """Export all reasoning chains as dictionaries."""
        return [chain.to_dict() for chain in self.chains]


class ConfidenceCalibrator:
    """
    Calibrates confidence scores based on historical accuracy.
    
    Tracks predictions vs actual outcomes to adjust future confidence.
    """
    
    def __init__(self):
        self.predictions: List[Dict[str, Any]] = []
        self.calibration_factor = 1.0
    
    def record_prediction(
        self,
        prediction_id: str,
        predicted_value: Any,
        confidence: float,
        category: str
    ):
        """Record a prediction for later calibration."""
        self.predictions.append({
            "id": prediction_id,
            "predicted": predicted_value,
            "confidence": confidence,
            "category": category,
            "timestamp": datetime.utcnow().isoformat(),
            "actual": None,
            "correct": None
        })
    
    def record_outcome(self, prediction_id: str, actual_value: Any):
        """Record the actual outcome for a prediction."""
        for pred in self.predictions:
            if pred["id"] == prediction_id:
                pred["actual"] = actual_value
                pred["correct"] = pred["predicted"] == actual_value
                break
    
    def calculate_calibration(self) -> Dict[str, float]:
        """Calculate calibration statistics."""
        resolved = [p for p in self.predictions if p["correct"] is not None]
        
        if not resolved:
            return {"calibration_factor": 1.0, "accuracy": None, "samples": 0}
        
        # Group by confidence buckets
        buckets = {
            "high": [p for p in resolved if p["confidence"] >= 0.8],
            "medium": [p for p in resolved if 0.5 <= p["confidence"] < 0.8],
            "low": [p for p in resolved if p["confidence"] < 0.5]
        }
        
        results = {"samples": len(resolved)}
        
        for bucket_name, bucket in buckets.items():
            if bucket:
                accuracy = sum(1 for p in bucket if p["correct"]) / len(bucket)
                avg_confidence = sum(p["confidence"] for p in bucket) / len(bucket)
                results[f"{bucket_name}_accuracy"] = accuracy
                results[f"{bucket_name}_avg_confidence"] = avg_confidence
                results[f"{bucket_name}_calibration"] = accuracy / avg_confidence if avg_confidence > 0 else 1.0
        
        # Overall calibration factor
        total_correct = sum(1 for p in resolved if p["correct"])
        overall_accuracy = total_correct / len(resolved)
        avg_confidence = sum(p["confidence"] for p in resolved) / len(resolved)
        
        results["accuracy"] = overall_accuracy
        results["avg_confidence"] = avg_confidence
        results["calibration_factor"] = overall_accuracy / avg_confidence if avg_confidence > 0 else 1.0
        
        self.calibration_factor = results["calibration_factor"]
        
        return results
    
    def adjust_confidence(self, raw_confidence: float) -> float:
        """Adjust a confidence score based on calibration."""
        adjusted = raw_confidence * self.calibration_factor
        return max(0.0, min(1.0, adjusted))  # Clamp to [0, 1]
