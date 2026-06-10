import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import AzureCliCredential, get_bearer_token_provider
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.graph_tool import get_graph_json
from tools.otel_tool import get_recent_traces, compute_error_rate, compute_p99_latency

load_dotenv()
console = Console()

token_provider = get_bearer_token_provider(
    AzureCliCredential(),
    'https://cognitiveservices.azure.com/.default'
)

client = AzureOpenAI(
    azure_endpoint='https://chaosproof-v2-resource.services.ai.azure.com',
    azure_ad_token_provider=token_provider,
    api_version='2025-01-01-preview'
)

CHAOS_PLANNER_ID  = os.environ["CHAOS_PLANNER_ID"]
GRAPH_ANALYST_ID  = os.environ["GRAPH_ANALYST_ID"]
FAULT_INJECTOR_ID = os.environ["FAULT_INJECTOR_ID"]
REMEDIATOR_ID     = os.environ["REMEDIATOR_ID"]
VERIFIER_ID       = os.environ["VERIFIER_ID"]

MAX_RETRIES = 2


def _run_agent(agent_id: str, message: str) -> dict:
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=message
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=agent_id
    )
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    for msg in msgs.data:
        if msg.role == "assistant":
            raw = msg.content[0].text.value
            clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(clean)
    raise ValueError("No assistant message found")


def run_chaosproof(target_service: str) -> dict:
    console.print(Panel(
        f"[bold]Target:[/bold]  {target_service}",
        title="ChaosProof", border_style="blue",
    ))

    # Step 1: telemetry
    traces = get_recent_traces(target_service)
    err_rate = compute_error_rate(traces)
    p99 = compute_p99_latency(traces)
    console.print(f"[cyan]Telemetry[/cyan]  error_rate={err_rate}  p99={p99}ms")

    # Step 2: plan
    console.print("\n[yellow][1/4] Chaos Planner[/yellow] reasoning...")
    plan = _run_agent(
        CHAOS_PLANNER_ID,
        f"Target service: {target_service}\n"
        f"Error rate: {err_rate}\nP99 latency: {p99}ms\n\n"
        f"Sample traces:\n{json.dumps(traces[:5], indent=2)}"
    )
    for exp in plan["experiments"]:
        console.print(f"  [{exp['id']}] {exp['type']:12s} on {exp['target']}")

    # Step 3: graph
    console.print("\n[yellow][2/4] Graph Analyst[/yellow] computing blast radius...")
    graph_result = _run_agent(
        GRAPH_ANALYST_ID,
        f"Service graph:\n{get_graph_json()}\n\n"
        f"Experiments:\n{json.dumps(plan['experiments'], indent=2)}"
    )

    if not graph_result.get("safe_to_inject", False):
        console.print(f"[yellow]Graph analyst flagged risk — proceeding with safest experiment only[/yellow]")
        graph_result["ranked_experiments"] = graph_result.get("ranked_experiments", [e["id"] for e in plan["experiments"]])[:1]

    console.print(f"  Blast radius: {graph_result['blast_radius']}")
    console.print(f"  Ranked: {graph_result['ranked_experiments']}")

    # Steps 3+4
    results = []
    exp_map = {e["id"]: e for e in plan["experiments"]}

    for exp_id in graph_result["ranked_experiments"]:
        experiment = exp_map[exp_id]
        console.print(f"\n[yellow][3+4][/yellow] [{exp_id}] {experiment['type']} on [bold]{experiment['target']}[/bold]")

        verdict = {"pass": False, "reason": "not run"}
        for attempt in range(MAX_RETRIES + 1):
            injection = _run_agent(
                FAULT_INJECTOR_ID,
                f"Inject (attempt {attempt+1}):\n{json.dumps(experiment, indent=2)}"
            )
            console.print(f"  Injected: {injection.get('observations', '')[:80]}")

            remediation = _run_agent(
                REMEDIATOR_ID,
                f"Fault:\n{json.dumps(injection, indent=2)}"
            )
            console.print(f"  Remediated: {remediation.get('root_cause', '')[:80]}")

            verdict = _run_agent(
                VERIFIER_ID,
                f"Goal: {json.dumps(experiment)}\n"
                f"Injection: {json.dumps(injection)}\n"
                f"Remediation: {json.dumps(remediation)}"
            )

            color = "green" if verdict["pass"] else "red"
            console.print(f"  Attempt {attempt+1}: [{color}]{'PASS' if verdict['pass'] else 'FAIL'}[/{color}] — {verdict['reason']}")

            if verdict["pass"]:
                results.append({
                    "experiment_id": exp_id,
                    "type": experiment["type"],
                    "target": experiment["target"],
                    "status": "pass",
                    "attempts": attempt + 1,
                    "artifact": remediation.get("artifact"),
                })
                break
            if attempt < MAX_RETRIES and verdict.get("retry_suggestion"):
                experiment["retry_hint"] = verdict["retry_suggestion"]
        else:
            results.append({
                "experiment_id": exp_id,
                "status": "failed",
                "reason": verdict.get("reason")
            })

    # Summary table
    table = Table(title="Results")
    for col in ["ID", "Type", "Target", "Status", "Attempts"]:
        table.add_column(col)
    for r in results:
        c = "green" if r["status"] == "pass" else "red"
        table.add_row(
            r.get("experiment_id", "?"),
            r.get("type", "?"),
            r.get("target", "?"),
            f"[{c}]{r['status']}[/{c}]",
            str(r.get("attempts", "?"))
        )
    console.print(table)
    console.print("\n[dim]Go to ai.azure.com > your project > Agents to see your agents[/dim]")
    return {"target": target_service, "results": results}