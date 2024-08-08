import subprocess
#Run this in Dafny dir
def get_previous_commit(commit_hash):
    try:
        # Get the previous commit hash using git log
        result = subprocess.run(
            ["git", "log", "--reverse", "--pretty=%H", f"{commit_hash}^..{commit_hash}"],
            capture_output=True,
            text=True,
            check=True
        )
        # Split the result to get the previous commit hash
        commits = result.stdout.strip().split('\n')
        if len(commits) > 1:
            return commits[0]  # The first commit in the list is the previous commit
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error finding previous commit for {commit_hash}: {e}")
        return None

def process_commits(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open('previous_commits.txt', 'w') as output_file:
        for line in lines:
            issue_no, commit_hash = line.strip().split(', ')
            previous_commit = get_previous_commit(commit_hash)
            if previous_commit:
                output_file.write(f"{issue_no}, {commit_hash}, {previous_commit}\n")
            else:
                output_file.write(f"{issue_no}, {commit_hash}, None\n")

# Example usage
process_commits('evaluation_issues_closed.txt')