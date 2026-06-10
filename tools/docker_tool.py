"""
Docker-in-Docker sandboxed fault injection.
All containers run on SANDBOX_NETWORK — host is never affected.
"""
import time
import docker

_client = docker.from_env()
SANDBOX_NETWORK = "chaosproof-sandbox"


def ensure_sandbox_network():
    try:
        _client.networks.get(SANDBOX_NETWORK)
    except docker.errors.NotFound:
        _client.networks.create(SANDBOX_NETWORK, driver="bridge")
        print(f"Created sandbox network: {SANDBOX_NETWORK}")


def inject_latency(container_name: str, delay_ms: int, jitter_ms: int = 50) -> dict:
    try:
        c = _client.containers.get(container_name)
        code, out = c.exec_run(
            f"tc qdisc add dev eth0 root netem delay {delay_ms}ms {jitter_ms}ms",
            privileged=True,
        )
        return {
            "status": "injected" if code == 0 else "failed",
            "container": container_name,
            "fault": f"latency_{delay_ms}ms",
            "output": out.decode(),
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def inject_crash(container_name: str) -> dict:
    try:
        c = _client.containers.get(container_name)
        c.stop(timeout=2)
        return {"status": "injected", "container": container_name, "fault": "crash"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def inject_resource_exhaustion(container_name: str, cpu_quota: int = 10000) -> dict:
    try:
        c = _client.containers.get(container_name)
        c.update(cpu_quota=cpu_quota)
        return {"status": "injected", "container": container_name,
                "fault": f"cpu_throttle_{cpu_quota}"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def restore_container(container_name: str) -> dict:
    try:
        c = _client.containers.get(container_name)
        if c.status != "running":
            c.start()
        c.exec_run("tc qdisc del dev eth0 root", privileged=True)
        c.update(cpu_quota=0)
        time.sleep(2)
        c.reload()
        return {"status": c.status, "healthy": c.status == "running"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
