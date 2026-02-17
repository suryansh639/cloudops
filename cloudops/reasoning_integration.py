"""
Integration: Connect reasoning system to existing CloudOps CLI

This shows how the new reasoning-based system integrates with existing code.
"""
from cloudops.incident_classification import IncidentClassifier
from cloudops.reasoning_planner import ReasoningPlanner, PrimitiveRegistry
from cloudops.diagnostic_executor import DiagnosticExecutor, DiagnosticInterpreter
from cloudops.config import Config
from cloudops.providers.factory import get_cloud_provider


class ReasoningInvestigator:
    """
    New investigation system using reasoning architecture.
    
    Replaces static playbooks with dynamic primitive composition.
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Get AI provider for classification and interpretation
        from cloudops.ai.providers import get_provider
        self.ai_provider = get_provider(config)
        
        # Get cloud provider for primitives
        self.cloud_provider = get_cloud_provider(config)
        
        # Initialize reasoning components
        self.classifier = IncidentClassifier(self.ai_provider)
        self.primitive_registry = PrimitiveRegistry(self.cloud_provider)
        self.planner = ReasoningPlanner(self.primitive_registry)
        self.executor = DiagnosticExecutor(self.primitive_registry)
        self.interpreter = DiagnosticInterpreter(self.ai_provider)
    
    def investigate(self, query: str, scope: str = "production") -> dict:
        """
        Investigate incident using reasoning system.
        
        Flow:
        1. Classify query → incident class
        2. Plan → select primitives
        3. Execute → collect facts
        4. Interpret → generate insights
        """
        
        # Step 1: Classify incident
        classification = self.classifier.classify(query)
        
        print(f"✓ Incident class: {classification.primary_class.value}")
        print(f"✓ Resource: {classification.resource_type}")
        print(f"✓ Confidence: {classification.confidence:.2f}")
        print()
        
        # Step 2: Create diagnostic plan
        plan = self.planner.create_plan(classification)
        
        print(f"📋 Diagnostic Plan ({len(plan.primitives)} steps):")
        for i, primitive in enumerate(plan.primitives, 1):
            print(f"  {i}. {primitive}")
        print()
        
        # Step 3: Execute plan
        print("Executing diagnostics...")
        execution = self.executor.execute(plan)
        
        print(f"✓ Executed {execution.primitives_executed} primitives")
        print(f"✓ Succeeded: {execution.primitives_succeeded}")
        print(f"✓ Failed: {execution.primitives_failed}")
        print()
        
        # Step 4: Interpret results
        print("Analyzing results...")
        interpretation = self.interpreter.interpret(
            execution, 
            classification.primary_class.value
        )
        
        # Present findings
        print("="*80)
        print("INVESTIGATION RESULTS")
        print("="*80)
        print()
        
        print("KEY FINDINGS:")
        for finding in interpretation.key_findings:
            print(f"  • {finding}")
        print()
        
        print("LIKELY ROOT CAUSES:")
        for cause in interpretation.likely_root_causes:
            confidence_pct = cause['confidence'] * 100
            print(f"  • {cause['cause']} ({confidence_pct:.0f}% confidence)")
            print(f"    Evidence: {', '.join(cause['evidence'])}")
        print()
        
        print("RECOMMENDED ACTIONS:")
        for action in interpretation.recommended_actions:
            print(f"  {action['priority']}. {action['action']}")
            if action.get('command'):
                print(f"     $ {action['command']}")
        print()
        
        return {
            'classification': classification,
            'plan': plan,
            'execution': execution,
            'interpretation': interpretation
        }


# ============================================================================
# CLI INTEGRATION
# ============================================================================

def integrate_with_cli():
    """
    Example of how to integrate reasoning system with existing CLI.
    
    In cloudops/cli.py, add:
    """
    
    # Option 1: Replace existing investigate command
    """
    @cli.command()
    @click.argument('query')
    def investigate(query: str):
        config = Config.load()
        
        # Use new reasoning system
        investigator = ReasoningInvestigator(config)
        investigator.investigate(query)
    """
    
    # Option 2: Add new command for testing
    """
    @cli.command()
    @click.argument('query')
    def investigate_v2(query: str):
        '''New reasoning-based investigation (beta)'''
        config = Config.load()
        
        investigator = ReasoningInvestigator(config)
        investigator.investigate(query)
    """
    
    # Option 3: Feature flag
    """
    @cli.command()
    @click.argument('query')
    @click.option('--use-reasoning', is_flag=True, help='Use new reasoning system')
    def investigate(query: str, use_reasoning: bool):
        config = Config.load()
        
        if use_reasoning or config.get('features.reasoning_enabled'):
            investigator = ReasoningInvestigator(config)
            investigator.investigate(query)
        else:
            # Use old playbook system
            old_investigate(query)
    """


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    """
    Example: Investigate RDS high CPU using reasoning system
    """
    
    from cloudops.config import Config
    
    config = Config.load()
    investigator = ReasoningInvestigator(config)
    
    # Example 1: RDS high CPU
    print("Example 1: RDS High CPU")
    print("="*80)
    investigator.investigate("RDS database has high CPU usage")
    
    print("\n\n")
    
    # Example 2: Lambda timeout
    print("Example 2: Lambda Timeout")
    print("="*80)
    investigator.investigate("Lambda function timing out")
    
    print("\n\n")
    
    # Example 3: Pod crashing
    print("Example 3: Pod Crashing")
    print("="*80)
    investigator.investigate("my pod is in CrashLoopBackOff")
