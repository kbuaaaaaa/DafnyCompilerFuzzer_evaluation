import asyncio
import subprocess
import time
import sys
from threading import Thread

from match_error import match_error
from process_bug import process_bug_handler

# Set a default duration in seconds (1800 seconds for 30 minutes)
default_duration = 1800

# Set the commit, commit before, and duration
main_commit = sys.argv[1]
duration = int(sys.argv[2]) if sys.argv[2] else default_duration
branch = sys.argv[3]
start_time = time.time()

if __name__ == "__main__":
    current_branch_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd='dafny').decode().strip()
    while (time.time() - start_time) < duration:
        # Fuzz until we hit an interesting case
        print("Fuzzing...")
        output = subprocess.run(["timeout", "60", "java", "-jar", "fuzz_d.jar", "fuzz"], capture_output=True, text=True)
        if output.returncode == 0:
            output_dir = output.stdout.split(': ')[-1].strip()
            uuid = output_dir.split('/')[-1]
            bugs = match_error(f"{output_dir}/fuzz-d.log")
            # Figure out if we can validate with interpreter
            interpret = True
            result = subprocess.call(["java", "-jar", "fuzz_d.jar", "interpret", output_dir + "/main.dfy"])
            if result == 1:
                interpret = False
                subprocess.call(["java", "-jar", "fuzz_d.jar", "validate", output_dir + "/main.dfy"])

            threads = []
            for language, bug in bugs.items():
                if bug:
                    t = Thread(target=process_bug_handler, args=(output_dir, language, bug, branch, interpret, main_commit, current_branch_commit, False, "None"))
                    threads.append(t)
                    t.start()

            # Wait for all threads to finish
            for t in threads:
                t.join()
        else:
            print("Fuzz-d crashed")

    sys.exit(0)
