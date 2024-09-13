import os
import subprocess
import sys
import boto3

if __name__ == "__main__":
    file_folder=sys.argv[1]

    s3 = boto3.resource('s3')

    #download the file
    subprocess.run(["aws", "s3", "cp", f"{file_folder}", f"/compfuzzci", "--recursive"], check=True)
    subprocess.run(["chmod", "+x", "/compfuzzci/interestingness_test.sh"], check=True)
    # Read branch, language, main_commit, hashed bug
    with open("/compfuzzci/data.txt", 'r') as f:
        branch = f.readline().strip()
        language = f.readline().strip()
        main_commit = f.readline().strip()
        branch_commit = f.readline().strip()
        hashed_bug = f.readline().strip()
        processing = f.readline().strip()

    os.makedirs("bisection", exist_ok=True)
    # Create an empty text file in the "bisection" folder
    with open("bisection/commit_order.txt", 'w') as file_obj:
        pass

    location = branch
    # Get the location of the bug
    print("Checking if bug is on master")
    if subprocess.call(["./bisect_script.sh", main_commit]):
        print("Bug is on master")
        location = "master"
    else:
        print("Bug is on branch")

    first_bad_commit = "undetermined"
    manual_investigation = False
    if location == "master":
        #This is the last point that fuzz-d program guarantee to work
        last_good_commit = "8a5a5945d6eefc552bdc39a3868dd34bb38a49d4"
        result = subprocess.call(["./bisect_script.sh", last_good_commit])
        if result:
            print("Bug needs manual investigation")
            manual_investigation = True
                
        if not manual_investigation:
            subprocess.run(["git", "checkout", main_commit], check=True, cwd='dafny')
            # Get the latest commit on the current branch
            print("Bisecting on master")
            # Start the bisect process
            subprocess.run(["git", "bisect", "start", main_commit, last_good_commit, "--no-checkout"], check=True, cwd='dafny')

            # Start the subprocess
            process = subprocess.Popen(
                ["git", "bisect", "run", "/compfuzzci/bisect_script.sh"],
                cwd='dafny',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Read and print the output in real time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if ' is the first bad commit' in output:
                        first_bad_commit = output.replace(' is the first bad commit', '')
                    print(output.strip())

            # Capture the remaining output (if any)
            stderr = process.communicate()[1]
            if stderr:
                print(stderr.strip())

            return_code = process.returncode

    elif language == "miscompilation" and first_bad_commit == "undetermined":
        subprocess.run(["git", "checkout", branch_commit], check=True, cwd='dafny')
        last_good_commit = "8a5a5945d6eefc552bdc39a3868dd34bb38a49d4"
        print("Bug is introduced in the branch")
        print(f"Bisecting on {location}")
        # Start the bisect process
        subprocess.run(["git", "bisect", "start", branch_commit, last_good_commit, "--no-checkout"], check=True, cwd='dafny')
                            
        # Start the subprocess
        process = subprocess.Popen(
            ["git", "bisect", "run", "/compfuzzci/bisect_script.sh"],
            cwd='dafny',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Read and print the output in real time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                if ' is the first bad commit' in output:
                    first_bad_commit = output.replace(' is the first bad commit', '')
                print(output.strip())

        # Capture the remaining output (if any)
        stderr = process.communicate()[1]
        if stderr:
            print(stderr.strip())

    with open("bisect_result.txt", 'w') as file_obj:
        file_obj.write(f"{location}\n")
        file_obj.write(f"{first_bad_commit}\n")

    subprocess.run(["aws", "s3", "cp", "bisect_result.txt", f"{file_folder}bisect_result.txt"], check=True)