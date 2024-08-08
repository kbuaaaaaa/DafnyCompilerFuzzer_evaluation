import json
import subprocess
import requests
import time

if __name__ == "__main__":
    with open('evaluation_issues.txt', 'r') as file:
        all_issues = file.readlines()
    all_issues = [issue.strip().split(' ') for issue in all_issues]

    for issue in all_issues:
        issue_number = issue[0]
        print(f"Processing issue: {issue_number}")
        
        owner = "CompFuzzCI"
        repo = "DafnyCompilerFuzzer"
        workflow_id = "build_image.yaml"
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer redacted"
        }
        payload = {
            "ref": "main",
            "inputs": {
                "commit": f"{issue[2]}"
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 204:
            print("Workflow dispatched successfully.")
        else:
            print(f"Failed to dispatch workflow {response}")

        time.sleep(360)
    
        with open('processing_task_definition_local.json', 'r') as file:
            content = file.read()

        content = content.replace('issue_no', str(issue_number))
        content = content.replace('COMMIT', issue[2])
        
        with open('processing_task_definition_local_temp.json', 'w') as file:
            file.write(content)
        command = f"aws ecs register-task-definition --cli-input-json file://processing_task_definition_local_temp.json"
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        response = result.stdout.strip()
        response_json = json.loads(response)

        command = f"aws ecs run-task --cluster compfuzzci --task-definition {response_json['taskDefinition']['taskDefinitionArn']}"
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)