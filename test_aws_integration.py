#!/usr/bin/env python3
"""Test CloudOps with AWS account"""
import sys
import boto3
from cloudops.config import Config
from cloudops.planning_engine import PlanningEngine, Plan, Step
from cloudops.execution_engine import ExecutionEngine

def test_aws_connectivity():
    """Test basic AWS connectivity"""
    print("Testing AWS connectivity...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS Account: {identity['Account']}")
        print(f"✓ User: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"✗ AWS connectivity failed: {e}")
        return False

def test_execution_engine():
    """Test CloudOps execution engine"""
    print("\nTesting CloudOps execution engine...")
    try:
        config = Config.load()
        engine = ExecutionEngine(config)
        
        # Create a simple plan
        plan = Plan(
            plan_id="test-001",
            intent="List EC2 instances",
            steps=[
                Step(
                    step_id="step-1",
                    action="list",
                    target="ec2_instances",
                    provider="cloud",
                    params={"service": "ec2", "action": "describe_instances"}
                )
            ],
            risk_level="low",
            requires_approval=False
        )
        
        # Execute the plan
        result = engine.execute(plan)
        print(f"✓ Execution engine successful")
        print(f"  Plan ID: {result.plan_id}")
        print(f"  Steps executed: {len(result.steps)}")
        print(f"  Status: {result.steps[0].status}")
        
        return True
    except Exception as e:
        print(f"✗ Execution engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_planning_engine():
    """Test CloudOps planning engine"""
    print("\nTesting CloudOps planning engine...")
    try:
        config = Config.load()
        planner = PlanningEngine(config)
        
        # Test simple intent
        intent = {
            'action': 'list',
            'resource': 'ec2_instances',
            'scope': 'dev'
        }
        plan = planner.generate_plan(intent)
        print(f"✓ Planning engine created plan")
        print(f"  Plan ID: {plan.plan_id}")
        print(f"  Steps: {len(plan.steps)}")
        print(f"  Risk level: {plan.risk_level}")
        return True
    except Exception as e:
        print(f"✗ Planning engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("CloudOps AWS Integration Test\n" + "="*50)
    
    results = []
    results.append(("AWS Connectivity", test_aws_connectivity()))
    results.append(("Execution Engine", test_execution_engine()))
    results.append(("Planning Engine", test_planning_engine()))
    
    print("\n" + "="*50)
    print("Test Results:")
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("="*50))
    if all_passed:
        print("✓ All tests passed! CloudOps is working with your AWS account.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Check the output above.")
        sys.exit(1)
