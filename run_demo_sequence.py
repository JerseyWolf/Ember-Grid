import subprocess
import sys
import time
from pathlib import Path

PYTHON = sys.executable
SCRIPT = Path(__file__).parent / "query_live.py"
OUTPUT = Path(__file__).parent / "demo_output.txt"
PAUSE = 15

QUERIES = [
    "checkout service OOM kill, container hitting memory limit and restarting repeatedly under load",
    "payment processor returning 500 errors, transactions not completing at checkout",
    "product search returning empty results, search index unresponsive after deployment",
    "inventory sync stalled, stock levels on website not updating after warehouse batch job",
    "store POS system tills unresponsive, cashiers cannot process customer transactions",
    "loyalty service not awarding points after purchase, customer accounts not updating",
    "order fulfilment delays caused by upstream pricing engine latency spike during peak hours",
    "notification service sending duplicate confirmation emails to customers after every order event",
    "supplier integration service dropping EDI purchase orders during XML schema validation",
    "recommendation engine returning identical product suggestions for all users after overnight model retraining",
]


def main():
    lines = []

    for idx, query in enumerate(QUERIES, start=1):
        print(f"\n{'='*60}")
        print(f"Query {idx}/{len(QUERIES)}")
        print(f"{'='*60}\n")

        cmd_str = f'python query_live.py "{query}"'
        print(f"$ {cmd_str}\n")
        lines.append(f"$ {cmd_str}\n\n")

        result = subprocess.run(
            [PYTHON, str(SCRIPT), query],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        lines.append(result.stdout)

        if result.stderr:
            filtered = "\n".join(
                l for l in result.stderr.splitlines()
                if "telemetry" not in l.lower() and "posthog" not in l.lower()
            )
            if filtered.strip():
                print(filtered)
                lines.append(filtered + "\n")

        if idx < len(QUERIES):
            print(f"\n--- sleeping {PAUSE}s ---\n")
            lines.append(f"\n--- sleeping {PAUSE}s ---\n\n")
            time.sleep(PAUSE)

    OUTPUT.write_text("".join(lines), encoding="utf-8")
    print(f"\nSaved to {OUTPUT}")


if __name__ == "__main__":
    main()