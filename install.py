"""
STOIQO Node Suite — Dependency Installer & Environment Checker
Ensures compatible dependencies without overwriting ComfyUI's torch/CUDA runtime.
"""

import os
import sys
import subprocess

def log(msg):
    print(f"[STOIQO_Node_Suite] {msg}")

def check_torch():
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        cuda_ver = torch.version.cuda if cuda_avail else "N/A"
        log(f"Detected PyTorch {torch.__version__} (CUDA: {cuda_avail}, CUDA Version: {cuda_ver})")
        return True
    except ImportError:
        log("Warning: PyTorch not found in current environment. ComfyUI core environment is expected.")
        return False

def check_bitsandbytes():
    try:
        import bitsandbytes as bnb
        log("bitsandbytes verified successfully.")
        return True
    except Exception as exc:
        log(f"Notice: bitsandbytes check: {exc}")
        if sys.platform == "win32":
            log("Tip: On Windows, if 4-bit quantization fails, install pre-compiled bitsandbytes via:")
            log("     pip install bitsandbytes --prefer-binary")
        return False

def install_requirements():
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_file):
        log("requirements.txt not found, skipping installation.")
        return

    log("Verifying and installing dependencies from requirements.txt...")
    check_torch()

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--prefer-binary", "-r", req_file
        ])
        log("Core dependencies installed/verified successfully.")
    except subprocess.CalledProcessError as err:
        log(f"Warning during dependency installation: {err}")

    check_bitsandbytes()

if __name__ == "__main__":
    install_requirements()
