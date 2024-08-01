import os

def generate_interestingness_test(test_folder, interpret, hashed_bug, language):
    # Script to be generated
    test_script = os.path.join(test_folder, f"{language}-interestingness_test.sh")
    # Create the script file and make it executable
    with open(test_script, 'w') as f:
        f.write('#!/bin/bash\n')
        if interpret == "true":
            f.write("java -jar /compfuzzci/fuzz_d.jar validate main.dfy --interpret\n")
        else:
            f.write("java -jar /compfuzzci/fuzz_d.jar validate main.dfy\n")
        
        f.write("output=$(python3 /compfuzzci/match_error.py fuzz-d.log {})\n".format(language))
        f.write("if [ \"$output\" == \"{}\" ]; then\n".format(hashed_bug))
        f.write("    exit 0\n")
        f.write("fi\n")
        f.write("exit 1\n")
    f.close()
    # Make the script executable
    os.chmod(test_script, 0o755)
    return