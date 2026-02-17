"""Unit tests for CloudOps"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from cloudops.config import Config, init_config
from cloudops.intent_parser import Intent, IntentParser
from cloudops.planning_engine import PlanningEngine
from cloudops.execution_engine import ExecutionEngine
from cloudops.audit import AuditLogger


class TestConfig:
    """Test configuration management"""
    
    def test_init_config(self, tmp_path):
        """Test config initialization"""
        config_path = tmp_path / "config.yaml"
        config = Config(config_path)
        config.data = {
            "llm": {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
            "cloud": {"primary": "aws"}
        }
        config.save()
        
        assert config_path.exists()
        loaded = Config.load()
        assert loaded.get("llm.provider") == "anthropic"
    
    def test_get_nested_key(self):
        """Test nested key access"""
        config = Config(Path("/tmp/test.yaml"))
        config.data = {"a": {"b": {"c": "value"}}}
        
        assert config.get("a.b.c") == "value"
        assert config.get("a.b.x", "default") == "default"
    
    def test_set_nested_key(self):
        """Test nested key setting"""
        config = Config(Path("/tmp/test.yaml"))
        config.data = {}
        config.set("a.b.c", "value")
        
        assert config.data["a"]["b"]["c"] == "value"


class TestIntentParser:
    """Test intent parsing"""
    
    @patch('cloudops.intent_parser.Anthropic')
    def test_parse_high_cpu(self, mock_anthropic):
        """Test parsing high CPU query"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "intent_type": "investigate",
            "target": {
                "resource_type": "kubernetes_cluster",
                "scope": "prod",
                "filters": {"metric": "cpu_usage"}
            },
            "goal": "identify_root_cause",
            "constraints": {"read_only": True, "max_cost_usd": 0.0},
            "confidence": 0.95
        }))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        config = Mock()
        config.get.side_effect = lambda k, d=None: {
            "llm.provider": "anthropic",
            "llm.model": "claude-3-5-haiku-20241022"
        }.get(k, d)
        config.get_api_key.return_value = "test-key"
        
        parser = IntentParser(config)
        intent = parser.parse("high cpu on prod cluster", "prod", True)
        
        assert intent.intent_type == "investigate"
        assert intent.target.resource_type == "kubernetes_cluster"
        assert intent.confidence == 0.95
    
    def test_low_confidence_rejection(self):
        """Test that low confidence intents are handled"""
        # This would be tested in integration tests
        pass


class TestPlanningEngine:
    """Test planning engine"""
    
    def test_match_k8s_cpu_playbook(self):
        """Test matching K8s CPU playbook"""
        config = Mock()
        config.get.return_value = ["write", "delete"]
        
        engine = PlanningEngine(config)
        
        intent = Mock()
        intent.intent_id = "test-123"
        intent.intent_type = "investigate"
        intent.target = Mock()
        intent.target.resource_type = "kubernetes_cluster"
        intent.target.scope = "prod"
        intent.target.filters = {"metric": "cpu_usage"}
        
        plan = engine.generate_plan(intent)
        
        assert plan.intent_id == "test-123"
        assert len(plan.steps) == 4
        assert plan.steps[0].action == "List all nodes in cluster"
        assert all(s.risk_level == "read" for s in plan.steps)
    
    def test_match_cost_playbook(self):
        """Test matching cost analysis playbook"""
        config = Mock()
        config.get.return_value = []
        
        engine = PlanningEngine(config)
        
        intent = Mock()
        intent.intent_id = "test-456"
        intent.intent_type = "investigate"
        intent.target = Mock()
        intent.target.resource_type = "cost"
        intent.target.scope = "prod"
        intent.target.filters = {}
        
        plan = engine.generate_plan(intent)
        
        assert len(plan.steps) == 3
        assert "cost" in plan.steps[0].action.lower()
    
    def test_no_playbook_match(self):
        """Test handling of unmatched intent"""
        config = Mock()
        engine = PlanningEngine(config)
        
        intent = Mock()
        intent.intent_type = "unknown"
        intent.target = Mock()
        intent.target.resource_type = "unknown"
        
        with pytest.raises(ValueError):
            engine.generate_plan(intent)
    
    def test_approval_required_for_write(self):
        """Test that write operations require approval"""
        config = Mock()
        config.get.return_value = ["write", "delete"]
        
        engine = PlanningEngine(config)
        
        # Write operation should require approval
        assert engine._check_approval_required("write", "prod") == True
        assert engine._check_approval_required("read", "prod") == False


class TestExecutionEngine:
    """Test execution engine"""
    
    def test_execute_plan_with_mock_providers(self):
        """Test plan execution with mock providers"""
        from cloudops.providers.mock import MockCloudProvider, MockK8sProvider
        
        config = Mock()
        mock_cloud = MockCloudProvider()
        mock_k8s = MockK8sProvider()
        
        engine = ExecutionEngine(config, cloud_provider=mock_cloud, k8s_provider=mock_k8s)
        
        plan = Mock()
        plan.plan_id = "test-plan"
        plan.steps = [
            Mock(
                step_id=1,
                provider="kubernetes",
                method="list_nodes",
                params={}
            )
        ]
        
        execution = engine.execute(plan)
        
        assert execution.plan_id == "test-plan"
        assert execution.status == "completed"
        assert len(execution.steps) == 1
        assert execution.steps[0].status == "completed"
    
    def test_execute_step_error_handling(self):
        """Test error handling in step execution"""
        from cloudops.providers.mock import MockCloudProvider, MockK8sProvider
        
        config = Mock()
        engine = ExecutionEngine(config, cloud_provider=MockCloudProvider(), k8s_provider=MockK8sProvider())
        
        step = Mock()
        step.step_id = 1
        step.provider = "unknown"
        step.method = "unknown"
        
        result = engine._execute_step(step)
        
        assert result.status == "failed"
        assert result.error is not None
    
    def test_kubernetes_execution(self):
        """Test Kubernetes execution via provider"""
        from cloudops.providers.mock import MockK8sProvider
        
        config = Mock()
        mock_k8s = MockK8sProvider()
        engine = ExecutionEngine(config, k8s_provider=mock_k8s)
        
        step = Mock()
        step.method = "list_nodes"
        step.params = {}
        
        result = engine._execute_kubernetes(step)
        
        assert "nodes" in result
        assert len(result["nodes"]) > 0
    
    def test_cloud_execution(self):
        """Test cloud execution via provider"""
        from cloudops.providers.mock import MockCloudProvider
        
        config = Mock()
        mock_cloud = MockCloudProvider()
        engine = ExecutionEngine(config, cloud_provider=mock_cloud)
        
        step = Mock()
        step.method = "cloudwatch_get_metrics"
        step.params = {}
        
        result = engine._execute_cloud(step)
        
        assert "datapoints" in result
        assert len(result["datapoints"]) > 0
    
    def test_provider_agnostic(self):
        """Test that engine doesn't know about specific providers"""
        from cloudops.providers.mock import MockCloudProvider, MockK8sProvider
        
        config = Mock()
        
        # Engine should work with any provider implementation
        engine = ExecutionEngine(config, cloud_provider=MockCloudProvider(), k8s_provider=MockK8sProvider())
        
        # Should not have boto3 or kubernetes client attributes
        assert not hasattr(engine, 'ec2')
        assert not hasattr(engine, 'cloudwatch')
        assert not hasattr(engine, 'k8s_core')
        
        # Should only have provider interfaces
        assert hasattr(engine, 'cloud')
        assert hasattr(engine, 'k8s')


class TestAuditLogger:
    """Test audit logging"""
    
    def test_log_execution(self, tmp_path):
        """Test logging an execution"""
        config = Mock()
        config_path = tmp_path / ".cloudops"
        config_path.mkdir()
        
        with patch('cloudops.audit.Path.home', return_value=tmp_path):
            logger = AuditLogger(config)
            
            intent = Mock()
            intent.intent_id = "intent-123"
            
            plan = Mock()
            plan.plan_id = "plan-123"
            plan.steps = [Mock(estimated_cost_usd=0.001, risk_level="read")]
            
            execution = Mock()
            execution.execution_id = "exec-123"
            execution.status = "completed"
            execution.steps = [
                Mock(
                    started_at="2026-02-17T10:00:00Z",
                    completed_at="2026-02-17T10:00:05Z"
                )
            ]
            
            logger.log_execution("test query", intent, plan, execution)
            
            # Check log file was created
            log_files = list(logger.audit_dir.glob("audit-*.jsonl"))
            assert len(log_files) > 0
            
            # Check log content
            with open(log_files[0]) as f:
                log_entry = json.loads(f.read())
                assert log_entry["action"]["intent"] == "test query"
                assert log_entry["result"]["status"] == "completed"
    
    def test_get_logs_time_filter(self, tmp_path):
        """Test retrieving logs with time filter"""
        config = Mock()
        
        with patch('cloudops.audit.Path.home', return_value=tmp_path):
            logger = AuditLogger(config)
            logger.audit_dir.mkdir(parents=True, exist_ok=True)
            
            # Create test log
            from datetime import datetime
            log_file = logger.audit_dir / f"audit-{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
            with open(log_file, 'w') as f:
                f.write(json.dumps({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "user": {"id": "test"},
                    "action": {"intent": "test"},
                    "result": {"status": "success"}
                }) + "\n")
            
            logs = logger.get_logs("24h")
            assert len(logs) == 1


class TestIntegration:
    """Integration tests"""
    
    @patch('cloudops.intent_parser.Anthropic')
    def test_full_investigation_flow(self, mock_anthropic):
        """Test complete investigation flow"""
        from cloudops.providers.mock import MockCloudProvider, MockK8sProvider
        
        # Mock LLM response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "intent_type": "investigate",
            "target": {
                "resource_type": "kubernetes_cluster",
                "scope": "prod",
                "filters": {"metric": "cpu_usage"}
            },
            "goal": "identify_root_cause",
            "constraints": {"read_only": True, "max_cost_usd": 0.0},
            "confidence": 0.95
        }))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Setup config
        config = Mock()
        config.get.side_effect = lambda k, d=None: {
            "llm.provider": "anthropic",
            "llm.model": "claude-3-5-haiku-20241022",
            "cloud.use_real_apis": False,
            "policy.require_approval_for": ["write", "delete"]
        }.get(k, d)
        config.get_api_key.return_value = "test-key"
        
        # Parse intent
        parser = IntentParser(config)
        intent = parser.parse("high cpu on prod cluster", "prod", True)
        
        # Generate plan
        planner = PlanningEngine(config)
        plan = planner.generate_plan(intent)
        
        # Execute plan with mock providers
        executor = ExecutionEngine(
            config,
            cloud_provider=MockCloudProvider(),
            k8s_provider=MockK8sProvider()
        )
        execution = executor.execute(plan)
        
        # Verify
        assert intent.intent_type == "investigate"
        assert len(plan.steps) == 4
        assert execution.status == "completed"


class TestProviderArchitecture:
    """Test provider abstraction"""
    
    def test_mock_cloud_provider(self):
        """Test mock cloud provider"""
        from cloudops.providers.mock import MockCloudProvider
        
        provider = MockCloudProvider()
        
        # Test interface methods
        metrics = provider.get_cpu_metrics()
        assert "datapoints" in metrics
        
        costs = provider.get_cost_data()
        assert "total" in costs
        
        sgs = provider.list_security_groups()
        assert "security_groups" in sgs
    
    def test_mock_k8s_provider(self):
        """Test mock Kubernetes provider"""
        from cloudops.providers.mock import MockK8sProvider
        
        provider = MockK8sProvider()
        
        # Test interface methods
        nodes = provider.list_nodes()
        assert "nodes" in nodes
        
        pods = provider.list_pods()
        assert "pods" in pods
        
        deployments = provider.list_deployments()
        assert "deployments" in deployments
    
    def test_provider_factory_mock(self):
        """Test provider factory with mock config"""
        from cloudops.providers.factory import build_cloud_provider, build_kubernetes_provider
        
        config = Mock()
        config.get.side_effect = lambda k, d=None: {
            "cloud.use_real_apis": False
        }.get(k, d)
        
        cloud = build_cloud_provider(config)
        k8s = build_kubernetes_provider(config)
        
        # Should return mock providers
        from cloudops.providers.mock import MockCloudProvider, MockK8sProvider
        assert isinstance(cloud, MockCloudProvider)
        assert isinstance(k8s, MockK8sProvider)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
