import os
import subprocess
from glob import glob

import os
import glob

if __name__ == '__main__':
    files = glob.glob('data/*')
    sorted_files = sorted(files, key=os.path.getctime)[::-1][:100]
    current_directory = os.getcwd()
    
    for path in sorted_files:
        if os.path.exists(f"{path}/output.txt"):
            continue
        
        
        os.chdir(os.path.join(current_directory, path))
        subprocess.run(['whisper', "output.mp3", '--model', 'medium', '--language', 'Chinese'])
        os.chdir(current_directory)