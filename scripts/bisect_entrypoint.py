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

    if processing == "False":  
        location = branch
        # Get the location of the bug
        if subprocess.call(["./bisect_script.sh", main_commit]):
            location = "master"
    else:
        location = "master"

    first_bad_commit = "undetermined"
    if location == "master":
        #This is the last point that fuzz-d program guarantee to work
        last_good_commit = "ad1a7bdd0018a0f248647b547d48eef83d6b9435"
        manual_investigation = False
        result = subprocess.call(["./bisect_script.sh", last_good_commit])
        if result:
            print("Bug needs manual investigation")
            manual_investigation = True
                
        if not manual_investigation:
            subprocess.run(["git", "checkout", "master"], check=True, cwd='dafny')
            # Get the latest commit on the current branch
            latest_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd='dafny').decode().strip()
            print("Bisecting on master")
            # Start the bisect process
            subprocess.run(["git", "bisect", "start", latest_commit, last_good_commit, "--no-checkout"], check=True, cwd='dafny')

            # Run the bisect script and capture the first bad commit
            result = subprocess.run(["git", "bisect", "run", "/compfuzzci/bisect_script.sh"], cwd='dafny', capture_output=True, text=True)
            output = result.stdout.strip()
            first_bad_commit = next((line.replace(' is the first bad commit', '') for line in output.split('\n') if 'is the first bad commit' in line), None)
            return_code = result.returncode
            if return_code:
                print("Bisect failed")
                first_bad_commit = "undetermined"
            print(f"First bad commit: {first_bad_commit}")

    elif language == "miscompilation" and first_bad_commit == "undetermined":
            subprocess.run(["git", "checkout", branch_commit], check=True, cwd='dafny')
            last_good_commit = subprocess.check_output(["git", "rev-list", "--max-parents=0", "HEAD"], cwd='dafny').decode().strip()

            print(f"Bisecting on {location}")
            # Start the bisect process
            subprocess.run(["git", "bisect", "start", branch_commit, last_good_commit, "--no-checkout"], check=True, cwd='dafny')
                        
            # Run the bisect script and capture the first bad commit
            result = subprocess.run(["git", "bisect", "run", "/compfuzzci/bisect_script.sh"], cwd='dafny', capture_output=True, text=True)
            output = result.stdout.strip()
            first_bad_commit = next((line.replace(' is the first bad commit', '') for line in output.split('\n') if 'is the first bad commit' in line), None)
            return_code = result.returncode
            if return_code:
                print("Bisect failed")
                first_bad_commit = "undetermined"
            print(f"First bad commit: {first_bad_commit}")


    with open("bisect_result.txt", 'w') as file_obj:
        file_obj.write(f"{location}\n")
        file_obj.write(f"{first_bad_commit}\n")

    subprocess.run(["aws", "s3", "cp", "bisect_result.txt", f"{file_folder}bisect_result.txt"], check=True)