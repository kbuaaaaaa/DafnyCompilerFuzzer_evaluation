import json
import re
import subprocess
import requests
import time

# UNWANTED_LABELS = [r'kind: language development speed', r'misc: \[.*\]', r'part: (?!code-generation).*']

def write_code_to_file(code):
    with open ('main.dfy', 'w') as f:
        f.write(code)
    f.close()

def extract_code_from_issue_body(issue):

    issue_body = issue.get('body')
    labels = [label['name'] for label in issue.get('labels', [])]

    code = ""
    if not issue_body:
        return code
    
    if '```dafny' in issue_body and not re.search(r'[dD]afny (resolve|verify|format|doc|measure-complexity|server|test|generate-tests|find-dead-code|audit|merge-coverage-reports)', issue_body) and not re.search(r'VSCode', issue_body):
        code = issue_body.split('```dafny')[1].split('```')[0]
    else:
        print(f"Skipping issue {issue_no} due to no dafny code block or unrelated command")

    return code

if __name__ == "__main__":
    url = f"https://api.github.com/repos/dafny-lang/dafny/issues"
    params = {
        "state": "closed",
        "labels": "kind: bug",
        "per_page": 100,
        "page": 1
    }
    headers = {
        "Authorization": "Bearer redacted"
    }

    all_issues = []
    max_issues = 5000

    while len(all_issues) < max_issues:
        response = requests.get(url, params=params, headers=headers)
        issues = response.json()
        if not issues:
            break
        all_issues.extend(issues)
        if len(all_issues) >= max_issues:
            all_issues = all_issues[:max_issues]
            break
        params['page'] += 1
    
    print(f"Total issues: {len(all_issues)}")
    issues_for_evaluation = []
    for issues in all_issues:
        issue_no = issues.get('number')
        print(f"Processing issue {issue_no}")
        code = extract_code_from_issue_body(issues)
        if not code:
            continue
        write_code_to_file(code)
        subprocess.run(["java", "-jar", "fuzz_d.jar", "validate", "main.dfy"], capture_output=True, text=True)
        process = subprocess.run(["./initial_interestingness_test.sh"], capture_output=True, text=True)
        if process.returncode == 0:   
            issues_for_evaluation.append(issue_no)
        print(f"Successfully processed issue {issue_no}")
    
    with open('evaluation_issues.txt', 'w') as f:
       for issue in issues_for_evaluation:
           f.write(f"{issue}\n")
    f.close()            
            
        