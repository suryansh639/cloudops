"""Audit logging system"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional


class AuditLogger:
    def __init__(self, config):
        self.config = config
        self.audit_dir = Path.home() / ".cloudops" / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
    
    def log_execution(self, query: str, intent, plan, execution):
        """Log an execution to audit trail"""
        
        audit_entry = {
            "audit_id": execution.execution_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": {
                "id": os.getenv("USER", "unknown"),
                "ip_address": "127.0.0.1"  # Local CLI
            },
            "action": {
                "intent": query,
                "intent_id": intent.intent_id,
                "plan_id": plan.plan_id,
                "execution_id": execution.execution_id,
                "steps_executed": len(execution.steps),
                "risk_level": max((s.risk_level for s in plan.steps), default="read")
            },
            "result": {
                "status": execution.status,
                "duration_sec": sum(
                    (datetime.fromisoformat(s.completed_at.rstrip("Z")) - 
                     datetime.fromisoformat(s.started_at.rstrip("Z"))).total_seconds()
                    for s in execution.steps
                ),
                "cost_usd": sum(s.estimated_cost_usd for s in plan.steps)
            }
        }
        
        # Write to daily log file
        log_file = self.audit_dir / f"audit-{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    
    def get_logs(self, time_range: str = "24h", user: Optional[str] = None) -> List[dict]:
        """Retrieve audit logs"""
        
        # Parse time range
        if time_range.endswith("h"):
            hours = int(time_range[:-1])
            cutoff = datetime.utcnow() - timedelta(hours=hours)
        elif time_range.endswith("d"):
            days = int(time_range[:-1])
            cutoff = datetime.utcnow() - timedelta(days=days)
        else:
            cutoff = datetime.utcnow() - timedelta(hours=24)
        
        logs = []
        
        # Read all log files in range
        for log_file in sorted(self.audit_dir.glob("audit-*.jsonl")):
            with open(log_file) as f:
                for line in f:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"].rstrip("Z"))
                    
                    if entry_time < cutoff:
                        continue
                    
                    if user and entry["user"]["id"] != user:
                        continue
                    
                    logs.append(entry)
        
        return logs
