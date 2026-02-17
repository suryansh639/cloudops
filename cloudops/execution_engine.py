"""Execution engine for running plans"""
import uuid
import time
from typing import List
from pydantic import BaseModel
from datetime import datetime
from cloudops.providers import CloudProvider, KubernetesProvider
from cloudops.providers.factory import build_cloud_provider, build_kubernetes_provider


class StepResult(BaseModel):
    step_id: int
    status: str
    started_at: str
    completed_at: str
    output: dict
    error: str = None


class Execution(BaseModel):
    execution_id: str
    plan_id: str
    status: str
    steps: List[StepResult]


class ExecutionEngine:
    """Provider-agnostic execution engine"""
    
    def __init__(self, config, cloud_provider: CloudProvider = None, k8s_provider: KubernetesProvider = None):
        self.config = config
        
        # Use provided providers or build from config
        self.cloud = cloud_provider or build_cloud_provider(config)
        self.k8s = k8s_provider or build_kubernetes_provider(config)
    
    def execute(self, plan) -> Execution:
        """Execute a plan"""
        execution = Execution(
            execution_id=str(uuid.uuid4()),
            plan_id=plan.plan_id,
            status="running",
            steps=[]
        )
        
        for step in plan.steps:
            result = self._execute_step(step)
            execution.steps.append(result)
            
            if result.status == "failed":
                execution.status = "failed"
                break
        
        if execution.status != "failed":
            execution.status = "completed"
        
        return execution
    
    def _execute_step(self, step) -> StepResult:
        """Execute a single step"""
        started_at = datetime.utcnow().isoformat() + "Z"
        
        try:
            # Route to appropriate provider
            if step.provider == "kubernetes":
                output = self._execute_kubernetes(step)
            elif step.provider == "aws":
                output = self._execute_cloud(step)
            elif step.provider == "local":
                output = self._execute_local(step)
            else:
                raise ValueError(f"Unknown provider: {step.provider}")
            
            # Simulate execution time
            time.sleep(1)
            
            completed_at = datetime.utcnow().isoformat() + "Z"
            
            return StepResult(
                step_id=step.step_id,
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                output=output
            )
        
        except Exception as e:
            completed_at = datetime.utcnow().isoformat() + "Z"
            return StepResult(
                step_id=step.step_id,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                output={},
                error=str(e)
            )
    
    def _execute_kubernetes(self, step) -> dict:
        """Execute Kubernetes operations via provider"""
        if step.method == "list_nodes":
            return self.k8s.list_nodes(**step.params)
        
        elif step.method == "top_pods":
            return self.k8s.list_pods(**step.params)
        
        elif step.method == "list_deployments":
            return self.k8s.list_deployments(**step.params)
        
        else:
            raise ValueError(f"Unknown Kubernetes method: {step.method}")
    
    def _execute_cloud(self, step) -> dict:
        """Execute cloud operations via provider"""
        if step.method == "cloudwatch_get_metrics":
            return self.cloud.get_cpu_metrics(**step.params)
        
        elif step.method == "cost_explorer_get_cost":
            return self.cloud.get_cost_data(**step.params)
        
        elif step.method == "ec2_describe_security_groups":
            return self.cloud.list_security_groups(**step.params)
        
        else:
            raise ValueError(f"Unknown cloud method: {step.method}")
    
    def _execute_local(self, step) -> dict:
        """Execute local analysis"""
        if step.method == "analyze_security_rules":
            return {
                "risky_groups": [
                    {
                        "id": "sg-12345",
                        "name": "web-servers",
                        "risk": "high",
                        "reason": "Allows unrestricted access from 0.0.0.0/0"
                    }
                ]
            }
        
        return {"status": "success"}
