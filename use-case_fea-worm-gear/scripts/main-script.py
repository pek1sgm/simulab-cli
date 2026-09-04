import subprocess
import sys
from pathlib import Path


def run_script(script_name):
    script_path = Path(__file__).parent / script_name
    print(f"\n--- {script_name} ---")
    subprocess.run([sys.executable, str(script_path)], cwd=script_path.parent)


if __name__ == "__main__":
    run_script("data_collector.py")
    run_script("caecar_report_fetcher.py")
    run_script("windchill_report_link_fetcher.py")
