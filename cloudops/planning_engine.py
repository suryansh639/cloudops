"""Deterministic planning engine with playbook system"""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class Step(BaseModel):
    step_id: int
    action: str
    provider: str
    method: str
    params: dict
    risk_level: str
    estimated_cost_usd: float
    requires_approval: bool


class Plan(BaseModel):
    plan_id: str
    intent_id: str
    steps: List[Step]
    rollback_plan: Optional[dict] = None
    estimated_duration_sec: int
    human_summary: str


class PlanningEngine:
    def __init__(self, config):
        self.config = config
        self.playbooks = self._load_playbooks()
    
    def _load_playbooks(self) -> dict:
        """Load playbook definitions"""
        return {
            "investigate_k8s_high_cpu": {
                "triggers": {
                    "intent_type": "investigate",
                    "resource_type": "kubernetes_cluster",
                    "metric": "cpu_usage"
                },
                "steps": [
                    {
                        "action": "List all nodes in cluster",
                        "provider": "kubernetes",
                        "method": "list_nodes",
                        "params": {"output": "json"},
                        "risk_level": "read",
                        "estimated_cost_usd": 0.0
                    },
                    {
                        "action": "Fetch CPU metrics from CloudWatch (last 1h)",
                        "provider": "aws",
                        "method": "cloudwatch_get_metrics",
                        "params": {
                            "metric": "CPUUtilization",
                            "period": 3600,
                            "stat": "Average"
                        },
                        "risk_level": "read",
                        "estimated_cost_usd": 0.001
                    },
                    {
                        "action": "List top CPU-consuming pods",
                        "provider": "kubernetes",
                        "method": "top_pods",
                        "params": {"all_namespaces": True},
                        "risk_level": "read",
                        "estimated_cost_usd": 0.0
                    },
                    {
                        "action": "Check recent deployments",
                        "provider": "kubernetes",
                        "method": "list_deployments",
                        "params": {"since": "1h"},
                        "risk_level": "read",
                        "estimated_cost_usd": 0.0
                    }
                ],
                "summary": "This plan will list all nodes, fetch CPU metrics, identify top consumers, and check recent deployments to find the root cause."
            },
            "investigate_cost_spike": {
                "triggers": {
                    "intent_type": "investigate",
                    "resource_type": "cost"
                },
                "steps": [
                    {
                        "action": "Get cost breakdown by service (last 30 days)",
                        "provider": "aws",
                        "method": "cost_explorer_get_cost",
                        "params": {
                            "time_period": "LAST_30_DAYS",
                            "granularity": "DAILY",
                            "group_by": "SERVICE"
                        },
                        "risk_level": "read",
                        "estimated_cost_usd": 0.01
                    },
                    {
                        "action": "Compare with previous month",
                        "provider": "aws",
                        "method": "cost_explorer_get_cost",
                        "params": {
                            "time_period": "PREVIOUS_30_DAYS",
                            "granularity": "MONTHLY"
                        },
                        "risk_level": "read",
                        "estimated_cost_usd": 0.01
                    },
                    {
                        "action": "List new resources created this month",
                        "provider": "aws",
                        "method": "config_list_resources",
                        "params": {"created_after": "30d"},
                        "risk_level": "read",
                        "estimated_cost_usd": 0.0
                    }
                ],
                "summary": "This plan will analyze cost trends, compare with previous periods, and identify new resources contributing to the spike."
            },
            "list_risky_security_groups": {
                "triggers": {
                    "intent_type": "list",
                    "resource_type": "security_group"
                },
                "steps": [
                    {
                        "action": "List all security groups",
                        "provider": "aws",
                        "method": "ec2_describe_security_groups",
                        "params": {},
                        "risk_level": "read",
                        "estimated_cost_usd": 0.0
                    },
                    {
                        "action": "Analyze rules for overly permissive access",
                        "provider": "local",
                        "method": "analyze_security_rules",
                        "params": {"check_public_access": True},
                        "risk_level": "read",
                        "estimated_cost_usd": 0.0
                    }
                ],
                "summary": "This plan will list all security groups and identify those with overly permissive rules (e.g., 0.0.0.0/0 access)."
            }
        }
    
    def generate_plan(self, intent) -> Plan:
        """Generate execution plan from intent"""
        
        # Match playbook
        playbook = self._match_playbook(intent)
        
        if not playbook:
            raise ValueError(f"No playbook found for intent type: {intent.intent_type}, resource: {intent.target.resource_type}")
        
        # Build steps
        steps = []
        for idx, step_def in enumerate(playbook["steps"], 1):
            requires_approval = self._check_approval_required(
                step_def["risk_level"],
                intent.target.scope
            )
            
            steps.append(Step(
                step_id=idx,
                action=step_def["action"],
                provider=step_def["provider"],
                method=step_def["method"],
                params=step_def["params"],
                risk_level=step_def["risk_level"],
                estimated_cost_usd=step_def["estimated_cost_usd"],
                requires_approval=requires_approval
            ))
        
        return Plan(
            plan_id=str(uuid.uuid4()),
            intent_id=intent.intent_id,
            steps=steps,
            estimated_duration_sec=len(steps) * 5,  # Rough estimate
            human_summary=playbook["summary"]
        )
    
    def _match_playbook(self, intent) -> Optional[dict]:
        """Match intent to playbook"""
        for playbook_id, playbook in self.playbooks.items():
            triggers = playbook["triggers"]
            
            if triggers.get("intent_type") != intent.intent_type:
                continue
            
            if triggers.get("resource_type") != intent.target.resource_type:
                continue
            
            # Check filters if specified
            if "metric" in triggers:
                if triggers["metric"] not in intent.target.filters.get("metric", ""):
                    continue
            
            return playbook
        
        return None
    
    def _check_approval_required(self, risk_level: str, scope: str) -> bool:
        """Check if approval is required based on policy"""
        require_approval_for = self.config.get("policy.require_approval_for", [])
        
        if risk_level in require_approval_for:
            return True
        
        if scope == "prod" and risk_level != "read":
            return True
        
        return False
