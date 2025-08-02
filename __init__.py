import subprocess
import sys
import os

def run_script(script_name):
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(f"Output of {script_name}:\n{result.stdout}")
    if result.stderr:
        print(f"Errors from {script_name}:\n{result.stderr}")

if __name__ == "__main__":
    run_script("email_download.py")
    run_script("rag_chat.py")