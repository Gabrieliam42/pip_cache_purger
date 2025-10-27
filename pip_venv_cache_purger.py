# Script Developer: Gabriel Mihai Sandu
# GitHub Profile: https://github.com/Gabrieliam42

import os
import sys
import shutil
import subprocess
import platform

def clean_broken_distributions(venv_root):
    if platform.system() == "Windows":
        site_packages = os.path.join(venv_root, "Lib", "site-packages")
    else:
        site_packages = os.path.join(
            venv_root, "lib",
            f"python{sys.version_info.major}.{sys.version_info.minor}",
            "site-packages"
        )

    if os.path.isdir(site_packages):
        for entry in os.listdir(site_packages):
            if entry.startswith("~"):
                path = os.path.join(site_packages, entry)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        print(f"Deleted broken directory: {path}")
                    else:
                        os.remove(path)
                        print(f"Deleted broken file: {path}")
                except Exception as e:
                    print(f"Failed to delete {path}: {e}")

def find_and_activate_venv():
    cwd = os.getcwd()
    for root, dirs, files in os.walk(cwd):
        if 'Scripts' in dirs or 'bin' in dirs:
            scripts_path = os.path.join(root, 'Scripts' if platform.system() == 'Windows' else 'bin')
            required_files = {'activate.bat' if platform.system() == 'Windows' else 'activate'}

            if required_files.issubset(set(os.listdir(scripts_path))):
                print(f"Virtual environment found at: {root}")
                clean_broken_distributions(root)

                if platform.system() == 'Windows':
                    activate_command = (
                        f'cmd /k ""{os.path.join(scripts_path, "activate.bat")}" '
                        f'&& python.exe -m pip install --upgrade pip '
                        f'&& pip check '
                        f'&& pip cache purge"'
                    )
                else:
                    activate_command = (
                        f'source "{os.path.join(scripts_path, "activate")}" && '
                        f'python3 -m pip install --upgrade pip && '
                        f'pip check && '
                        f'pip cache purge'
                    )

                subprocess.run(
                    activate_command,
                    shell=True,
                    executable='/bin/bash' if platform.system() != 'Windows' else None
                )
                return

    print("No virtual environment found.")

if __name__ == "__main__":
    find_and_activate_venv()
