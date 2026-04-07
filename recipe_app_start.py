import os
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))

subprocess.Popen(
    ["powershell", "-NoExit", "-Command", "python recipe_app.py"],
    cwd=script_dir
)