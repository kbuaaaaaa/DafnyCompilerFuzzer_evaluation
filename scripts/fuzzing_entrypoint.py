import os
import subprocess
import time
import sys
from threading import Thread

from match_error import match_error
from process_bug import process_bug_handler



# Set the commit, commit before, and duration
branch_commit = sys.argv[1]
main_commit = sys.argv[2]
duration = 60 * 60 * 2
branch = sys.argv[3]
start_time = time.time()

if __name__ == "__main__":
    time_interval = "30"
    repetition = os.environ.get('REPETITION')
    commit_check = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd="dafny").stdout.strip()
    print(f"Current HEAD commit: {commit_check}")
    while (time.time() - start_time) < duration:
        if (time.time() - start_time) > (90*60):
            time_interval = "120"
        elif (time.time() - start_time) > (60*60):
            time_interval = "90"
        elif (time.time() - start_time) > (30*60):
            time_interval = "60"
        # Fuzz until we hit an interesting case
        print("Fuzzing...")
        output = subprocess.run(["timeout", "60", "java", "-jar", "fuzz_d.jar", "fuzz"], capture_output=True, text=True)
        if output.returncode == 0:
            output_dir = output.stdout.split(': ')[-1].strip()
            time_passed = int(time.time() - start_time)
            subprocess.run(["aws", "s3", "cp", f"{output_dir}/main.dfy", f"s3://compfuzzci/evaluation/all_test/{branch_commit}/{time_interval}/{repetition}/{output_dir}/main.dfy"], check=True)
            subprocess.run(["aws", "s3", "cp", f"{output_dir}/fuzz-d.log", f"s3://compfuzzci/evaluation/all_test/{branch_commit}/{time_interval}/{repetition}/{output_dir}/{time_passed}.log"], check=True)
            uuid = output_dir.split('/')[-1]
            bugs = match_error(f"{output_dir}/fuzz-d.log")
            print(bugs)
            interpret = False

            threads = []
            for language, bug in bugs.items():
                if bug:
                    t = Thread(target=process_bug_handler, args=(output_dir, language, bug, branch, interpret, main_commit, branch_commit, False, "None", time_interval, repetition))
                    threads.append(t)
                    t.start()

            # Wait for all threads to finish
            for t in threads:
                t.join()
            if output_dir:
                subprocess.run(["rm", "-rf", output_dir])
        else:
            print("Fuzz-d crashed or timed out")

    sys.exit(0)
