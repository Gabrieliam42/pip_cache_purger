# Script Developer: Gabriel Mihai Sandu
# GitHub Profile: https://github.com/Gabrieliam42

import os
import sys
import ctypes
import shutil
import subprocess
import traceback
import platform

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def relaunch_as_admin():
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    res = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    if int(res) <= 32:
        raise RuntimeError(f"ShellExecuteW failed with code {res}")
    os._exit(0)

def clear_directory_contents(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"[!] Directory not found: {path}")
        return
    for name in os.listdir(path):
        full = os.path.join(path, name)
        try:
            if os.path.isfile(full) or os.path.islink(full):
                os.remove(full)
                print(f"[FILE] Deleted: {full}")
            elif os.path.isdir(full):
                shutil.rmtree(full)
                print(f"[DIR]  Deleted: {full}")
        except Exception as e:
            print(f"[ERR]  {full}: {e}")

def remove_matching_dirs_under(root_path, dir_names):
    for dirpath, dirs, _ in os.walk(root_path, topdown=False):
        for d in list(dirs):
            if d.lower() in dir_names:
                target = os.path.join(dirpath, d)
                try:
                    shutil.rmtree(target)
                    print(f"[CACHE] Removed: {target}")
                except Exception as e:
                    print(f"[ERR] {target}: {e}")

def clean_broken_distributions(root_path):
    if not os.path.isdir(root_path):
        return
    if platform.system() == "Windows":
        site_packages = os.path.join(root_path, "Lib", "site-packages")
    else:
        site_packages = os.path.join(
            root_path, "lib",
            f"python{sys.version_info.major}.{sys.version_info.minor}",
            "site-packages"
        )
    if not os.path.isdir(site_packages):
        return
    print(f"[CLEAN BROKEN] Checking: {site_packages}")
    for entry in os.listdir(site_packages):
        if entry.startswith("~"):
            path = os.path.join(site_packages, entry)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"[CLEAN BROKEN] Deleted broken directory: {path}")
                else:
                    os.remove(path)
                    print(f"[CLEAN BROKEN] Deleted broken file: {path}")
            except Exception as e:
                print(f"[ERR] Failed to delete {path}: {e}")

def run_pip_cache_purge_with_python(python_exe):
    if not os.path.isfile(python_exe):
        print(f"[!] python.exe not found in {os.path.dirname(python_exe)}")
        return
    print(f"[CMD] Running pip cache purge for {python_exe}")
    try:
        proc = subprocess.Popen(
            [python_exe, "-m", "pip", "cache", "purge"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True
        )
        try:
            stdout, stderr = proc.communicate(timeout=60)
            if stdout.strip():
                print(stdout.strip())
            if stderr.strip():
                print(stderr.strip())
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"[TIMEOUT] pip cache purge took too long for {python_exe}")
    except Exception as e:
        print(f"[ERR] pip purge failed for {python_exe}: {e}")

def main():
    if not is_admin():
        try:
            relaunch_as_admin()
        except Exception as e:
            print(f"Failed to relaunch as admin: {e}")
            sys.exit(1)
        sys.exit(0)

    print("=== Starting cache cleanup ===")

    user_cache = os.path.join(os.environ["LOCALAPPDATA"], "pip", "cache")
    py_installs = [
        r"C:\Program Files\Python310",
        r"C:\Program Files\Python311",
        r"C:\Program Files\Python312",
        r"C:\Program Files\Python313",
        r"C:\Program Files\Python314",
    ]
    conda_installs = [
        r"C:\ProgramData\miniforge3",
        r"C:\ProgramData\miniconda3",
        r"C:\ProgramData\anaconda3",
    ]

    print(f"\n[USER CACHE] {user_cache}")
    clear_directory_contents(user_cache)

    roaming_python = os.path.join(os.environ["APPDATA"], "Python")
    if os.path.exists(roaming_python):
        print(f"\n[ROAMING PYTHON CACHE ROOT] {roaming_python}")
        for root, dirs, _ in os.walk(roaming_python):
            for d in dirs:
                if d.lower() in {"cache", "__pycache__"}:
                    target = os.path.join(root, d)
                    try:
                        shutil.rmtree(target)
                        print(f"[ROAMING] Removed: {target}")
                    except Exception as e:
                        print(f"[ERR] {target}: {e}")
    else:
        print(f"[!] Roaming Python directory not found: {roaming_python}")

    for p in py_installs:
        print(f"\n[PYTHON INSTALL] {p}")
        if not os.path.exists(p):
            print(f"[!] Directory not found: {p}")
            continue
        python_exe = os.path.join(p, "python.exe")
        run_pip_cache_purge_with_python(python_exe)
        remove_matching_dirs_under(p, {"cache", "__pycache__"})
        clean_broken_distributions(p)

    for c in conda_installs:
        print(f"\n[CONDA INSTALL] {c}")
        if not os.path.exists(c):
            print(f"[!] Directory not found: {c}")
            continue
        cache_paths = [
            os.path.join(c, "pkgs"),
            os.path.join(c, "conda-bld"),
            os.path.join(c, "conda-meta"),
            os.path.join(c, "envs", "cache"),
            os.path.join(c, "cache"),
        ]
        for cp in cache_paths:
            if os.path.exists(cp):
                print(f"[CLEAN] Removing cache path: {cp}")
                clear_directory_contents(cp)
                try:
                    shutil.rmtree(cp)
                    print(f"[DIR] Removed: {cp}")
                except Exception:
                    pass
        remove_matching_dirs_under(c, {"cache", "__pycache__"})
        clean_broken_distributions(c)

    if getattr(sys, "frozen", False):
        try:
            print("\n[CURRENT PYTHON] Frozen EXE detected. Using system-registered Python.")
            proc = subprocess.Popen(
                ["python", "-m", "pip", "cache", "purge"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True
            )
            try:
                stdout, stderr = proc.communicate(timeout=60)
                if stdout.strip():
                    print(stdout.strip())
                if stderr.strip():
                    print(stderr.strip())
            except subprocess.TimeoutExpired:
                proc.kill()
                print("[TIMEOUT] pip cache purge via system Python took too long.")
        except FileNotFoundError:
            print("[ERR] No system-registered Python found in PATH. Skipping purge.")
        except Exception as e:
            print(f"[ERR] pip purge failed for system Python: {e}")
    else:
        print(f"\n[CURRENT PYTHON] {sys.executable}")
        run_pip_cache_purge_with_python(sys.executable)

    print("\n=== Cache cleanup complete ===")
    print("All operations finished.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Unhandled exception:")
        traceback.print_exc()
    finally:
        try:
            os.system("cmd /k")
        except Exception:
            pass
