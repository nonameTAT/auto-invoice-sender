import subprocess
import sys


def run_workflow():
    scripts = ["invoice_generator.py", "send_invoice.py"]

    for script in scripts:
        print(f"--- Running: {script} ---")
        try:
            # Use sys.executable to run with the same Python interpreter
            subprocess.run([sys.executable, script], check=True)
            print(f"✅ {script} finished\n")

        except subprocess.CalledProcessError:
            print(f"❌ Workflow stopped: {script} failed.")
            # Skip the remaining steps
            break
        except FileNotFoundError:
            print(f"❌ Error: file not found: {script}")
            break


if __name__ == "__main__":
    run_workflow()
