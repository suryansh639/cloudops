"""CLI entry point"""
import click
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

from cloudops.config import Config
from cloudops.intent_parser import IntentParser
from cloudops.planning_engine import PlanningEngine
from cloudops.execution_engine import ExecutionEngine
from cloudops.audit import AuditLogger

console = Console()


@click.group()
@click.version_option()
def cli():
    """CloudOps - AI-Assisted Cloud Operations Control Plane"""
    pass


@cli.command()
def init():
    """Initialize CloudOps configuration"""
    from cloudops.ai import ModelRegistry, ReasoningMode
    
    console.print("[bold blue]CloudOps Configuration Setup[/bold blue]\n")
    
    # Step 1: Select AI provider
    console.print("[bold]Step 1: Select AI Provider[/bold]")
    providers = ModelRegistry.get_providers()
    provider_choices = {str(i+1): p for i, p in enumerate(providers)}
    
    for idx, provider in provider_choices.items():
        console.print(f"  {idx}. {provider}")
    
    provider_idx = click.prompt("\nSelect provider", type=click.Choice(list(provider_choices.keys())))
    provider = provider_choices[provider_idx]
    
    # Step 2: Select model
    console.print(f"\n[bold]Step 2: Select Model ({provider})[/bold]")
    models = ModelRegistry.get_models(provider)
    model_choices = {str(i+1): m for i, m in enumerate(models)}
    
    for idx, model in model_choices.items():
        cost_color = {"low": "green", "medium": "yellow", "high": "red"}[model.capabilities.cost_tier.value]
        console.print(f"  {idx}. {model.name} [{cost_color}]{model.capabilities.cost_tier.value}[/{cost_color}] "
                     f"(context: {model.capabilities.context_window})")
    
    default_model = ModelRegistry.get_default_model(provider)
    default_idx = next((idx for idx, m in model_choices.items() if m.id == default_model.id), "1")
    
    model_idx = click.prompt("\nSelect model", type=click.Choice(list(model_choices.keys())), default=default_idx)
    selected_model = model_choices[model_idx]
    
    # Step 3: Configure credentials
    console.print(f"\n[bold]Step 3: Configure Credentials[/bold]")
    console.print("  1. Environment variable")
    console.print("  2. OS keychain (not yet implemented)")
    console.print("  3. Skip (will fail at runtime if needed)")
    
    cred_choice = click.prompt("\nSelect credential source", type=click.Choice(["1", "2", "3"]), default="1")
    
    credentials = {}
    if cred_choice == "1":
        default_env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "bedrock": "AWS_ACCESS_KEY_ID",
            "deepseek": "DEEPSEEK_API_KEY",
            "local": "NONE",
            "none": "NONE"
        }
        default_env = default_env_vars.get(provider, f"{provider.upper()}_API_KEY")
        
        if provider in ["local", "none"]:
            env_var = "NONE"
        else:
            env_var = click.prompt("Environment variable name", default=default_env)
        
        credentials = {
            "source": "env",
            "env_var": env_var
        }
    elif cred_choice == "2":
        console.print("[yellow]Keychain support not yet implemented. Using skip.[/yellow]")
        credentials = {"source": "skip"}
    else:
        credentials = {"source": "skip"}
    
    # Step 4: Select reasoning mode
    console.print(f"\n[bold]Step 4: Select Default Reasoning Mode[/bold]")
    console.print("  1. fast - Quick responses, lower quality")
    console.print("  2. balanced - Good balance of speed and quality")
    console.print("  3. deep - Slower, higher quality reasoning")
    
    mode_choice = click.prompt("\nSelect mode", type=click.Choice(["1", "2", "3"]), default="2")
    mode_map = {"1": "fast", "2": "balanced", "3": "deep"}
    reasoning_mode = mode_map[mode_choice]
    
    # Additional config for specific providers
    additional_config = {}
    if provider == "local":
        base_url = click.prompt("Local model base URL", default="http://localhost:11434/v1")
        additional_config["base_url"] = base_url
    elif provider == "bedrock":
        region = click.prompt("AWS region", default="us-east-1")
        additional_config["region"] = region
    
    # Build configuration
    config_data = {
        "ai": {
            "provider": provider,
            "model": selected_model.id,
            "reasoning": reasoning_mode,
            "credentials": credentials,
            **additional_config
        },
        "llm": {
            "provider": provider,
            "model": selected_model.id,
            "api_key_source": f"env:{credentials.get('env_var', 'NONE')}" if credentials.get('source') == 'env' else "skip",
            "max_tokens": selected_model.capabilities.max_tokens,
            "temperature": 0.0
        },
        "cloud": {
            "primary": "aws",
            "use_real_apis": False
        },
        "policy": {
            "require_approval_for": ["write", "delete"],
            "auto_approve": ["read"],
            "scopes": {
                "prod": "require_approval",
                "dev": "auto_approve_reads"
            }
        }
    }
    
    # Save configuration
    config_path = Path.home() / ".cloudops" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    console.print(f"\n[green]✓[/green] Configuration saved to {config_path}")
    
    # Show summary
    console.print("\n[bold]Configuration Summary:[/bold]")
    console.print(f"  Provider: {provider}")
    console.print(f"  Model: {selected_model.name}")
    console.print(f"  Reasoning: {reasoning_mode}")
    console.print(f"  Credentials: {credentials.get('source')}")
    
    if credentials.get('source') == 'env':
        env_var = credentials.get('env_var')
        if env_var != "NONE":
            env_set = os.getenv(env_var) is not None
            if env_set:
                console.print(f"  [green]✓[/green] {env_var} is set")
            else:
                console.print(f"  [yellow]⚠[/yellow] {env_var} is not set (set it before using)")
    
    console.print("\n[bold]Next steps:[/bold]")
    if credentials.get('source') == 'env' and credentials.get('env_var') != "NONE":
        console.print(f"  1. Set your API key: export {credentials.get('env_var')}='your-key'")
    console.print("  2. Enable real cloud APIs: cloudops config cloud.use_real_apis true")
    console.print("  3. Run an investigation: cloudops investigate 'high cpu on prod cluster'")



@cli.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, help="Show plan without executing")
@click.option("--explain", is_flag=True, help="Show detailed reasoning")
@click.option("--read-only", is_flag=True, help="Enforce read-only mode")
@click.option("--scope", default="prod", help="Target environment")
@click.option("--approve", is_flag=True, help="Skip approval prompt")
def investigate(query, dry_run, explain, read_only, scope, approve):
    """Investigate cloud infrastructure issues"""
    query_str = " ".join(query)
    
    try:
        config = Config.load()
    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found. Run 'cloudops init' first.")
        sys.exit(1)
    
    audit = AuditLogger(config)
    
    console.print(f"[bold]Investigating:[/bold] {query_str}\n")
    
    # Parse intent
    console.print("🤖 Understanding your request...")
    parser = IntentParser(config)
    intent = parser.parse(query_str, scope, read_only)
    
    if intent.confidence < 0.8:
        console.print(f"[yellow]Warning:[/yellow] Low confidence ({intent.confidence:.2f}). Please rephrase.")
        sys.exit(1)
    
    console.print(f"[green]✓[/green] Intent: {intent.intent_type}")
    console.print(f"[green]✓[/green] Target: {intent.target.resource_type} (scope: {intent.target.scope})")
    console.print(f"[green]✓[/green] Confidence: {intent.confidence:.2f}\n")
    
    # Generate plan
    console.print("📋 Generating investigation plan...")
    planner = PlanningEngine(config)
    plan = planner.generate_plan(intent)
    
    console.print(f"\n[bold]Investigation Plan:[/bold]\n")
    for step in plan.steps:
        risk_color = "green" if step.risk_level == "read" else "yellow"
        console.print(f"{step.step_id}. {step.action}")
        console.print(f"   Risk: [{risk_color}]{step.risk_level}[/{risk_color}] | "
                     f"Cost: ${step.estimated_cost_usd:.4f} | "
                     f"Approval: {'required' if step.requires_approval else 'not required'}")
    
    console.print(f"\nEstimated duration: {plan.estimated_duration_sec} seconds")
    console.print(f"Total cost: ${sum(s.estimated_cost_usd for s in plan.steps):.4f}\n")
    
    if explain:
        console.print(f"[bold]Explanation:[/bold]\n{plan.human_summary}\n")
    
    if dry_run:
        console.print("[yellow]Dry-run mode:[/yellow] Plan generated but not executed.")
        return
    
    # Check approval
    needs_approval = any(s.requires_approval for s in plan.steps)
    if needs_approval and not approve:
        if not Confirm.ask("This plan requires approval. Proceed?"):
            console.print("Aborted.")
            return
    elif not approve:
        if not Confirm.ask("Proceed?"):
            console.print("Aborted.")
            return
    
    # Execute
    console.print("\n[bold]Executing...[/bold]\n")
    executor = ExecutionEngine(config)
    execution = executor.execute(plan)
    
    for step_result in execution.steps:
        status_icon = "✓" if step_result.status == "completed" else "✗"
        console.print(f"[green]{status_icon}[/green] Step {step_result.step_id}: {step_result.status}")
    
    # Log audit
    audit.log_execution(query_str, intent, plan, execution)
    
    console.print(f"\n[bold green]Investigation Complete[/bold green]")
    console.print(f"\nExecution ID: {execution.execution_id}")


@cli.command()
@click.option("--last", default="24h", help="Time range (e.g., 24h, 7d)")
@click.option("--user", help="Filter by user")
def audit(last, user):
    """View audit logs"""
    try:
        config = Config.load()
    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found.")
        sys.exit(1)
    
    audit_logger = AuditLogger(config)
    logs = audit_logger.get_logs(last, user)
    
    console.print(f"[bold]Audit Logs (last {last}):[/bold]\n")
    for log in logs:
        console.print(f"[cyan]{log['timestamp']}[/cyan] - {log['user']['id']}")
        console.print(f"  Action: {log['action']['intent']}")
        console.print(f"  Status: {log['result']['status']}")
        console.print()


@cli.command()
@click.argument("key")
@click.argument("value")
def config(key, value):
    """Update configuration"""
    try:
        cfg = Config.load()
        cfg.set(key, value)
        cfg.save()
        console.print(f"[green]✓[/green] Updated {key} = {value}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def main():
    cli()


if __name__ == "__main__":
    main()
