import asyncio
import os
import subprocess
import shutil

async def reduction(processing=False, output_dir=None, language=None, interpret=False):
    # Reduce the test case
    try:
        print("Reducing...")
        process = await asyncio.create_subprocess_shell("timeout 900 java -jar perses.jar --input-file " + f"{output_dir}main.dfy --test-script " + f"{output_dir}{language}-interestingness_test.sh --output-dir " + f"{output_dir}reduced_{language}/", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        print(f"perses stdout: {stdout.decode()}")
        print(f"perses stderr: {stderr.decode()}") 
        print("Validating the reduced program")
        if interpret:
            process = await asyncio.create_subprocess_shell("java -jar fuzz_d.jar validate " + f"{output_dir}reduced_{language}/main.dfy --interpret --language " + language, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        else:
            process = await asyncio.create_subprocess_shell("java -jar fuzz_d.jar validate " + f"{output_dir}reduced_{language}/main.dfy --language " + language, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        print("Reduction complete")
        return 1
    except asyncio.CancelledError:
        process.terminate()
        print("Reduction cancelled")
        return 0