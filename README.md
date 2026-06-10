# ChaosProof

Automated chaos engineering via multi-agent reasoning on Microsoft Foundry.

## Setup (15 min)

### 1. Create Foundry project
1. Go to https://ai.azure.com
2. Create a new project (or use existing hub)
3. Copy the project endpoint URL

### 2. Install dependencies
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure credentials
```bash
cp .env.example .env
# Edit .env — add AZURE_PROJECT_ENDPOINT
# For local dev, `az login` handles auth via DefaultAzureCredential
```

### 4. Create the five agents (run once)
```bash
python main.py --setup
# Prints five agent IDs — paste them into .env
```

### 5. Run ChaosProof
```bash
python main.py --service order-service
```

## Viewing the reasoning trace
After each run, copy the printed Thread ID and open:
**Foundry portal > your project > Agents > Threads > paste ID**

You will see every agent's reasoning step, tool calls, and outputs —
exactly what judges want to see for the Reasoning Agents track.

## Replacing stubs with real data
| File | Stub to replace |
|------|----------------|
| tools/otel_tool.py | `get_recent_traces()` → query Jaeger/Tempo/OTLP |
| tools/graph_tool.py | `build_service_graph()` → k8s API / Consul / Istio |
| tools/docker_tool.py | Works as-is with Docker Desktop or DinD |

## Project structure
```
chaosproof/
├── agents/setup.py       # Creates all 5 Foundry agents
├── tools/
│   ├── graph_tool.py     # NetworkX dependency graph
│   ├── docker_tool.py    # Sandboxed fault injection
│   └── otel_tool.py      # Telemetry collection
├── orchestrator.py       # Main reasoning loop
├── main.py               # Entrypoint
└── demo/script.md        # 5-minute demo guide
```
