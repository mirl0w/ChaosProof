"""
Usage:
  python main.py                          # run on order-service (demo)
  python main.py --service payment-service
  python main.py --setup                  # create Foundry agents (run once)
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="ChaosProof reasoning agent")
    parser.add_argument("--service", default="order-service")
    parser.add_argument("--setup", action="store_true",
                        help="Create agents in Foundry (run once)")
    args = parser.parse_args()

    if args.setup:
        from agents.setup import main as run_setup
        run_setup()
        return

    from orchestrator import run_chaosproof
    result = run_chaosproof(args.service)
    passed = sum(1 for r in result.get("results", []) if r.get("status") == "pass")
    total  = len(result.get("results", []))
    print(f"\n{passed}/{total} experiments passed.")
    sys.exit(0 if passed > 0 else 1)


if __name__ == "__main__":
    main()
