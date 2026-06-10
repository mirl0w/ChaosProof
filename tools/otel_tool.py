"""
OpenTelemetry trace collector.
Swap get_recent_traces() for a real OTLP/Jaeger/Tempo query in production.
"""
import time
import random


def get_recent_traces(service_name: str, window_seconds: int = 300) -> list[dict]:
    """
    Replace this stub with real OTLP queries, e.g.:
        requests.get(f"http://jaeger:16686/api/traces?service={service_name}")
    """
    now = int(time.time())
    return [
        {
            "trace_id": f"trace_{i:04x}",
            "service": service_name,
            "operation": random.choice(["GET /orders", "POST /checkout", "GET /inventory"]),
            "duration_ms": random.randint(20, 1200),
            "status": random.choice(["OK", "OK", "OK", "ERROR"]),
            "timestamp": now - random.randint(0, window_seconds),
            "attributes": {
                "http.status_code": random.choice([200, 200, 200, 500, 503]),
            },
        }
        for i in range(20)
    ]


def compute_error_rate(traces: list[dict]) -> float:
    if not traces:
        return 0.0
    errors = sum(1 for t in traces if t["status"] == "ERROR")
    return round(errors / len(traces), 3)


def compute_p99_latency(traces: list[dict]) -> float:
    if not traces:
        return 0.0
    durations = sorted(t["duration_ms"] for t in traces)
    idx = int(len(durations) * 0.99)
    return float(durations[min(idx, len(durations) - 1)])
