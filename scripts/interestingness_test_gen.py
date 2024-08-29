import os
import re

def escape_for_grep(s):
    # Escape only the special characters for grep
    return re.sub(r'([\\.*+?^${}()|\[\]])', r'\\\1', s)

def generate_interestingness_test(test_folder, interpret, bug, language):
    # Script to be generated
    test_script = os.path.join(test_folder, f"{language}-interestingness_test.sh")
    # Create the script file and make it executable
    with open(test_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write("java -jar /compfuzzci/fuzz_d.jar validate main.dfy --language {}\n".format(language))
        
        if language != "miscompilation":
            for err in bug:
                f.write("if grep -q \'{}\' fuzz-d.log; then\n".format(escape_for_grep(err)))
                f.write("    echo 1\n")
                f.write("    exit 1\n")
                f.write("fi\n")
        else:
            f.write("if grep -q \'{}\' fuzz-d.log; then\n".format(escape_for_grep("Different output: true")))
            f.write("    echo 1\n")
            f.write("    exit 1\n")
            f.write("fi\n")
        f.write("echo 0\n")
        f.write("exit 0\n")
    f.close()
    # Make the script executable
    os.chmod(test_script, 0o755)
    return