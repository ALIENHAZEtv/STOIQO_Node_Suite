"""
STOIQO Suite — Automated Build & Release Manager
Compiles frontend bundle, generates clean standalone @release package,
and optionally synchronizes with ComfyUI runtime custom_nodes without pollution.
"""

import os
import sys
import shutil
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELEASE_BASE = os.path.join(PROJECT_ROOT, "@release")
RELEASE_DIR = os.path.join(RELEASE_BASE, "STOIQO_Node_Suite")
COMFY_TARGET = os.environ.get(
    "COMFYUI_CUSTOM_NODES",
    os.environ.get(
        "EXC_COMFYUI_CUSTOM_NODES",
        os.path.normpath(
            os.path.join(PROJECT_ROOT, "..", "..", "ExCathedra", "engines", "comfyui", "ComfyUI", "custom_nodes", "STOIQO_Node_Suite")
            if os.path.isdir(os.path.join(PROJECT_ROOT, "..", "..", "ExCathedra", "engines", "comfyui", "ComfyUI", "custom_nodes"))
            else os.path.join(PROJECT_ROOT, "..", "ComfyUI", "custom_nodes", "STOIQO_Node_Suite")
        ),
    ),
)


def run_command(cmd, cwd):
    print(f"[BUILD] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=cwd, shell=True)
    if res.returncode != 0:
        print(f"[ERROR] Command failed with code {res.returncode}")
        sys.exit(res.returncode)


def copy_clean_tree(src, dst):
    """Copies directory tree excluding __pycache__, .git, and temporary files."""
    os.makedirs(dst, exist_ok=True)
    copied_count = 0
    for root, dirs, files in os.walk(src):
        # Exclude pycache and hidden dirs
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]

        rel_dir = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel_dir) if rel_dir != "." else dst
        os.makedirs(dest_dir, exist_ok=True)

        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo") or file.startswith("."):
                continue
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_dir, file)
            shutil.copy2(src_file, dst_file)
            copied_count += 1
    return copied_count


def build_release(deploy=False):
    print("=" * 60)
    print(" STOIQO-Comfyui-Nodes — Release Pipeline")
    print("=" * 60)

    # 1. Compile JS bundle with esbuild
    print("\n>>> 1. Building JS bundle via npm...")
    run_command(["npm", "run", "build"], cwd=PROJECT_ROOT)

    # 2. Reset @release/STOIQO-Comfyui-Nodes
    print(f"\n>>> 2. Preparing clean release directory: {RELEASE_DIR}")
    if os.path.exists(RELEASE_DIR):
        shutil.rmtree(RELEASE_DIR)
    os.makedirs(RELEASE_DIR, exist_ok=True)

    # 3. Copy Production Python & Metadata files
    total_files = 0

    print(">>> 3. Copying core modules...")
    total_files += copy_clean_tree(os.path.join(PROJECT_ROOT, "core"), os.path.join(RELEASE_DIR, "core"))

    print(">>> 4. Copying node definitions...")
    total_files += copy_clean_tree(os.path.join(PROJECT_ROOT, "nodes"), os.path.join(RELEASE_DIR, "nodes"))

    print(">>> 5. Copying compiled JS bundle...")
    os.makedirs(os.path.join(RELEASE_DIR, "js"), exist_ok=True)
    bundle_src = os.path.join(PROJECT_ROOT, "js", "stoiqo_suite.js")
    if os.path.exists(bundle_src):
        shutil.copy2(bundle_src, os.path.join(RELEASE_DIR, "js", "stoiqo_suite.js"))
        total_files += 1
    else:
        print("[WARNING] Compiled js/stoiqo_suite.js not found!")

    # Root metadata files
    root_files = ["__init__.py", "requirements.txt", "install.py", "README.md", ".gitignore", "LICENSE", "pyproject.toml"]
    for rf in root_files:
        src_path = os.path.join(PROJECT_ROOT, rf)
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(RELEASE_DIR, rf))
            total_files += 1

    # Calculate release payload size
    total_bytes = 0
    for root, _, files in os.walk(RELEASE_DIR):
        for f in files:
            total_bytes += os.path.getsize(os.path.join(root, f))
    size_kb = total_bytes / 1024
    size_mb = size_kb / 1024
    size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{size_kb:.1f} KB"

    print("\n" + "-" * 60)
    print("✓ RELEASE GENERATED SUCCESSFULLY!")
    print(f"  Target: {RELEASE_DIR}")
    print(f"  Files:  {total_files}")
    print(f"  Size:   {size_str}")
    print("-" * 60)

    # 4. Optional Non-Destructive Deploy to ComfyUI
    if deploy:
        print("\n>>> DEPLOY: Synchronizing release into ComfyUI runtime...")
        print(f"    Destination: {COMFY_TARGET}")
        if not os.path.exists(COMFY_TARGET):
            os.makedirs(COMFY_TARGET, exist_ok=True)

        deployed_count = copy_clean_tree(RELEASE_DIR, COMFY_TARGET)
        print(f"✓ [DEPLOY OK] {deployed_count} files synchronized to ComfyUI custom_nodes!")
    else:
        print("\n[NOTE] To automatically sync with ComfyUI, run: npm run release:deploy")
        print("       Otherwise, you can manually copy the folder from @release anytime.")


if __name__ == "__main__":
    should_deploy = "--deploy" in sys.argv
    build_release(deploy=should_deploy)
