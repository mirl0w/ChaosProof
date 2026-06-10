import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import AzureCliCredential, get_bearer_token_provider

load_dotenv()

token_provider = get_bearer_token_provider(
    AzureCliCredential(),
    'https://cognitiveservices.azure.com/.default'
)

client = AzureOpenAI(
    azure_endpoint='https://chaosproof-v2-resource.services.ai.azure.com',
    azure_ad_token_provider=token_provider,
    api_version='2025-01-01-preview'
)

AGENT_SPECS = [
    dict(name="chaos-planner", env_key="CHAOS_PLANNER_ID",
         instructions="You are a chaos engineering planning agent. Given telemetry data, output exactly 3 chaos experiments. Respond ONLY with valid JSON: {\"target_service\": \"order-service\", \"experiments\": [{\"id\": \"exp_1\", \"type\": \"latency\", \"target\": \"payment-service\", \"params\": {\"delay_ms\": 500}, \"rationale\": \"high p99\"}]}"),
    dict(name="graph-analyst", env_key="GRAPH_ANALYST_ID",
         instructions="You are a dependency graph reasoning agent. Compute blast radius and rank experiments safest-first. Respond ONLY with valid JSON: {\"blast_radius\": [\"svc_a\"], \"critical_paths\": [], \"safe_to_inject\": true, \"ranked_experiments\": [\"exp_1\", \"exp_2\", \"exp_3\"], \"abort_reason\": null}"),
    dict(name="fault-injector", env_key="FAULT_INJECTOR_ID",
         instructions="You are a fault injection agent. Simulate injecting the fault. Respond ONLY with valid JSON: {\"experiment_id\": \"exp_1\", \"commands_run\": [\"docker exec ...\"], \"container_id\": \"sandbox_1\", \"initial_status\": \"injected\", \"observations\": \"latency increased to 800ms\"}"),
    dict(name="remediator", env_key="REMEDIATOR_ID",
         instructions="You are a remediation agent. Reason about root cause and generate a fix. Respond ONLY with valid JSON: {\"root_cause\": \"no circuit breaker\", \"remediation_type\": \"config\", \"artifact\": \"apiVersion: v1\", \"applied\": true, \"post_remediation_status\": \"healthy\", \"health_check_output\": \"HTTP 200 in 42ms\"}"),
    dict(name="verifier", env_key="VERIFIER_ID",
         instructions="You are a verifier. Judge if fault was injected, remediation worked, system is healthy. Respond ONLY with valid JSON: {\"injection_valid\": true, \"remediation_valid\": true, \"system_healthy\": true, \"pass\": true, \"reason\": \"all passed\", \"retry_suggestion\": null}"),
]


def main():
    env_lines = []
    print("Creating ChaosProof agents in Foundry...\n")
    for spec in AGENT_SPECS:
        agent = client.beta.assistants.create(
            model='gpt-4.1-mini',
            name=spec["name"],
            instructions=spec["instructions"],
        )
        line = f"{spec['env_key']}={agent.id}"
        env_lines.append(line)
        print(f"  {spec['name']:20s} -> {agent.id}")
    print("\n--- Copy into your .env ---")
    for line in env_lines:
        print(line)


if __name__ == "__main__":
    main()