import subprocess
import time
from subprocess import PIPE
import signal

def run_code(code, timeout=20):
    with open('./temp_code.py', 'w', encoding='utf-8') as f:
        f.write(code)
    try:
        process = subprocess.Popen(['python', 'temp_code.py'], 
                                 stdout=PIPE, 
                                 stderr=PIPE)
        start_time = time.time()
        while process.poll() is None:
            if time.time() - start_time > timeout:
                process.kill()
                return None, "TimeoutError: Code execution exceeded {} seconds".format(timeout)
            time.sleep(0.1)
        stdout, stderr = process.communicate()
        if stderr:
            return None, stderr.decode('utf-8')
        return stdout.decode('utf-8'), None
    except Exception as e:
        return None, str(e)
if __name__ == "__main__":
    code = "print('Hello, World!')"
    output, error = run_code(code)
    if error:
        print("Error:", error)
    else:
        print("Output:", output)