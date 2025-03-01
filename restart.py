# Restart.py
import os
import sys

if __name__ == "__main__":
    # Get the original script file to run
    script_to_run = sys.argv[1] if len(sys.argv) > 1 else __file__
    args = sys.argv[2:]  # Remaining arguments
    os.execv(sys.executable, [sys.executable, script_to_run] + args)