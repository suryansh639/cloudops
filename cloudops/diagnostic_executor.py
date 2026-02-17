"""
Diagnostic Execution Engine

Executes diagnostic plans by running primitives in sequence.
Collects facts and passes them to interpretation layer.
"""
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from cloudops.reasoning_planner import DiagnosticPlan, PrimitiveRegistry
from cloudops.diagnostic_primitives import DiagnosticResult


class DiagnosticExecution(BaseModel):
    """Result of executing a diagnostic plan"""
    
    plan_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Results from each primitive
    results: List[DiagnosticResult]
    
    # Summary
    primitives_executed: int
    primitives_succeeded: int
    primitives_failed: int
    
    # Overall status
    status: str  # 'completed', 'partial', 'failed'


class DiagnosticExecutor:
    """
    Executes diagnostic plans.
    
    Key responsibilities:
    - Run primitives in order
    - Collect structured facts
    - Handle errors gracefully
    - NO interpretation (that's for AI layer)
    """
    
    def __init__(self, primitive_registry: PrimitiveRegistry):
        self.registry = primitive_registry
    
    def execute(self, plan: DiagnosticPlan) -> DiagnosticExecution:
        """
        Execute diagnostic plan.
        
        Returns raw facts from each primitive.
        Does NOT interpret or draw conclusions.
        """
        
        start_time = datetime.utcnow()
        results = []
        
        # Execute each primitive in sequence
        for primitive_name in plan.primitives:
            try:
                primitive = self.registry.get(primitive_name)
                
                # Execute primitive with shared context
                result = primitive.execute(plan.context)
                results.append(result)
                
                # Optionally: enrich context with results for next primitive
                # This allows primitives to build on each other
                if result.success:
                    plan.context[f'{primitive_name}_result'] = result.facts
                
            except Exception as e:
                # Record failure but continue
                results.append(DiagnosticResult(
                    primitive=primitive_name,
                    resource_type=plan.context.get('resource_type', 'unknown'),
                    resource_id=plan.context.get('resource_id'),
                    timestamp=datetime.utcnow(),
                    facts={},
                    success=False,
                    error=str(e)
                ))
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        succeeded = sum(1 for r in results if r.success)
        failed = len(results) - succeeded
        
        # Determine overall status
        if failed == 0:
            status = 'completed'
        elif succeeded > 0:
            status = 'partial'
        else:
            status = 'failed'
        
        return DiagnosticExecution(
            plan_id=plan.plan_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            results=results,
            primitives_executed=len(results),
            primitives_succeeded=succeeded,
            primitives_failed=failed,
            status=status
        )


# ============================================================================
# INTERPRETATION LAYER
# ============================================================================

class DiagnosticInterpretation(BaseModel):
    """AI interpretation of diagnostic results"""
    
    # Facts (from primitives)
    key_findings: List[str]
    
    # Hypotheses (AI reasoning)
    likely_root_causes: List[Dict[str, Any]]  # [{cause, confidence, evidence}]
    
    # Recommendations (actionable)
    recommended_actions: List[Dict[str, Any]]  # [{action, priority, command}]
    
    # Metadata
    confidence: float
    requires_human_review: bool


class DiagnosticInterpreter:
    """
    Interprets diagnostic results using AI.
    
    Key principle: Clearly separate FACTS from HYPOTHESES.
    - Facts: What primitives observed
    - Hypotheses: What AI thinks is happening
    - Recommendations: What to do next
    """
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
    
    def interpret(self, execution: DiagnosticExecution, 
                  incident_class: str) -> DiagnosticInterpretation:
        """
        Interpret diagnostic results.
        
        Sends facts to AI and asks for:
        1. Key findings (summarize facts)
        2. Likely root causes (hypotheses with confidence)
        3. Recommended actions (what to do next)
        """
        
        # Extract facts from all results
        facts = self._extract_facts(execution.results)
        
        prompt = f"""
You are analyzing diagnostic results for a {incident_class} incident.

FACTS (from diagnostic primitives):
{self._format_facts(facts)}

Your task:
1. Summarize KEY FINDINGS (facts only, no speculation)
2. Propose LIKELY ROOT CAUSES (hypotheses with confidence 0-1)
3. Recommend ACTIONS (specific, actionable steps)

Rules:
- Clearly separate facts from hypotheses
- Assign confidence to each hypothesis
- Cite evidence from facts
- Do NOT hallucinate data not in facts
- Do NOT promise fixes that may not work

Return JSON:
{{
  "key_findings": ["finding1", "finding2", ...],
  "likely_root_causes": [
    {{"cause": "description", "confidence": 0.8, "evidence": ["fact1", "fact2"]}}
  ],
  "recommended_actions": [
    {{"action": "description", "priority": 1, "command": "optional command"}}
  ],
  "confidence": 0.7,
  "requires_human_review": false
}}
"""
        
        response = self.ai_provider.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=2000
        )
        
        import json
        data = json.loads(response)
        
        return DiagnosticInterpretation(**data)
    
    def _extract_facts(self, results: List[DiagnosticResult]) -> Dict[str, Any]:
        """Extract all facts from diagnostic results"""
        
        facts = {}
        for result in results:
            if result.success:
                facts[result.primitive] = result.facts
        
        return facts
    
    def _format_facts(self, facts: Dict[str, Any]) -> str:
        """Format facts for AI prompt"""
        
        lines = []
        for primitive, data in facts.items():
            lines.append(f"\n{primitive}:")
            for key, value in data.items():
                lines.append(f"  - {key}: {value}")
        
        return '\n'.join(lines)
