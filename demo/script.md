# ChaosProof — 5-minute demo script

## 0:00–0:30  Opening
"ChaosProof is a multi-agent reasoning system on Microsoft Foundry
that automatically plans, injects, and remediates distributed system failures.
Five specialised agents, each model matched to its reasoning demands."

## 0:30–1:00  Show the graph
Open tools/graph_tool.py. Show the service topology.
"Before touching anything, the Graph Analyst — running on o3 — computes
blast radius. If an experiment would cascade to more than five critical
services, the whole run is aborted."

## 1:00–2:30  Run live
  python main.py --service order-service

Walk the output:
 - Chaos Planner (gpt-5.2) proposes 3 experiments with rationale
 - Graph Analyst (o3) ranks them by blast radius, confirms safe_to_inject
 - Fault Injector injects latency on payment-service
 - Remediator generates circuit breaker config, applies it
 - Verifier confirms healthy state

## 2:30–3:30  Foundry thread trace
Go to: https://ai.azure.com > your project > Agents > Threads > paste thread ID
Show each agent's run step in sequence.
Highlight: verifier FAIL on attempt 1, retry with hint, PASS on attempt 2.
"This is the reasoning loop — not a script, not a pipeline.
Each agent sees prior context and reasons from it."

## 3:30–4:30  Show the remediation artifact
Print the generated circuit breaker YAML.
"The agent reasoned about root cause and generated this from scratch.
It then applied it and confirmed the system recovered."

## 4:30–5:00  Close
"Multi-step reasoning. Cross-agent collaboration. Self-correction via
the critic loop. Safe sandboxed execution. Full observability via
Foundry thread tracing."
