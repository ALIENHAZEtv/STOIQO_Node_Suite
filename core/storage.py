"""
[STOIQO] Prompt Generator Engine — File Storage & Artifact Management
Handles directory resolution, saving .txt captions, .json metadata manifests,
and tracing upstream ComfyUI prompt graphs to detect original filenames.
"""

import os
import json
import folder_paths


def resolve_output_dir(output_dir):
    """Resolves output directory relative to ComfyUI's standard output folder."""
    if not output_dir or not output_dir.strip():
        return folder_paths.get_output_directory()
    clean_dir = output_dir.strip()
    if os.path.isabs(clean_dir):
        return clean_dir
    norm = os.path.normpath(clean_dir).lstrip(".\\/")
    if norm.lower().startswith("output"):
        norm = norm[6:].lstrip(".\\/")
    if not norm:
        return folder_paths.get_output_directory()
    return os.path.join(folder_paths.get_output_directory(), norm)


def save_artifacts(
    stem,
    caption="",
    tags="",
    negative="",
    meta=None,
    output_dir="",
    save_txt=False,
    save_json_metadata=False,
    is_dual_active=False,
    is_audit_active=False,
    save_negative=True,
    **kwargs,
):
    """Saves .txt prompt files and .json metadata manifests for LoRA training."""
    caption = caption or kwargs.get("prompt", "")
    tags = tags or kwargs.get("clip_l", "") or kwargs.get("t5_caption", "")
    negative = negative or kwargs.get("negative_prompt", "")
    should_save_json = save_json_metadata or kwargs.get("save_json", False)

    resolved_dir = resolve_output_dir(output_dir)
    os.makedirs(resolved_dir, exist_ok=True)

    if save_txt:
        txt_path = os.path.join(resolved_dir, f"{stem}.txt")
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as fh:
            fh.write(caption)
        if tags:
            tags_txt_path = os.path.join(resolved_dir, f"{stem}_tags.txt")
            os.makedirs(os.path.dirname(tags_txt_path), exist_ok=True)
            with open(tags_txt_path, "w", encoding="utf-8") as fh:
                fh.write(tags)
        if (is_audit_active or save_negative) and negative.strip():
            neg_txt_path = os.path.join(resolved_dir, f"{stem}_neg.txt")
            os.makedirs(os.path.dirname(neg_txt_path), exist_ok=True)
            with open(neg_txt_path, "w", encoding="utf-8") as fh:
                fh.write(negative)
        print(f"[STOIQO] Saved: {txt_path}")

    if should_save_json and meta:
        json_path = os.path.join(resolved_dir, f"{stem}.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=4)
        print(f"[STOIQO] Saved: {json_path}")


def get_original_filename(prompt, unique_id, input_key="image"):
    """
    Traces upstream in the ComfyUI execution graph (through Reroutes up to 6 hops)
    to identify the source filename of the connected image.
    """
    try:
        if not prompt or not unique_id:
            return None
        this_node = prompt.get(str(unique_id))
        if not this_node:
            return None
        image_link = this_node.get("inputs", {}).get(input_key)
        if not (isinstance(image_link, list) and image_link):
            return None

        curr_node_id = str(image_link[0])
        for _ in range(6):
            if not curr_node_id or curr_node_id not in prompt:
                break
            source_node = prompt.get(curr_node_id, {})
            inputs = source_node.get("inputs", {})
            filename = (
                inputs.get("image")
                or inputs.get("image_path")
                or inputs.get("path")
                or inputs.get("filename")
            )
            if isinstance(filename, str) and filename.strip():
                return os.path.splitext(os.path.basename(filename.strip()))[0]

            next_link = None
            for key in ("*", "image", "images", "input"):
                val = inputs.get(key)
                if isinstance(val, list) and val:
                    next_link = str(val[0])
                    break
            if not next_link or next_link == curr_node_id:
                break
            curr_node_id = next_link
    except Exception as exc:
        print(f"[STOIQO] Could not resolve original filename for '{input_key}': {exc}")
    return None


def open_native_folder_dialog(initial_dir=""):
    """
    Opens a native operating system folder browser dialog.
    On Windows, invokes PowerShell System.Windows.Forms.FolderBrowserDialog.
    Returns the absolute path selected by the user, or empty string if cancelled.
    """
    import sys
    import subprocess

    if sys.platform == "win32":
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$f.Description = 'Select Model Folder'; "
            "$f.ShowNewFolderButton = $false; "
        )
        if initial_dir and os.path.isdir(initial_dir):
            clean_init = initial_dir.replace("'", "''")
            ps_script += f"$f.SelectedPath = '{clean_init}'; "
        ps_script += "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.SelectedPath }"
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if res.returncode == 0:
                selected = res.stdout.strip()
                if selected and os.path.isdir(selected):
                    return os.path.abspath(selected)
        except Exception as e:
            print(f"[STOIQO] Native folder dialog notice: {e}")
    elif sys.platform == "darwin":
        try:
            cmd = "osascript -e 'POSIX path of (choose folder with prompt \"Select Model Folder\")'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                selected = res.stdout.strip()
                if selected and os.path.isdir(selected):
                    return os.path.abspath(selected)
        except Exception as e:
            print(f"[STOIQO] Native folder dialog notice: {e}")
    elif sys.platform.startswith("linux"):
        try:
            res = subprocess.run(
                ["zenity", "--file-selection", "--directory", "--title=Select Model Folder"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if res.returncode == 0:
                selected = res.stdout.strip()
                if selected and os.path.isdir(selected):
                    return os.path.abspath(selected)
        except Exception:
            pass
    return ""


def build_dataset_manifest(
    caption="",
    tags="",
    negative="",
    tags_list=None,
    is_dual_active=False,
    is_audit_active=False,
    prompt_type="",
    artistic_style="",
    system_prompt_preset="",
    system_prompt_mode="",
    trigger_word="",
    shuffle_tags=False,
    seed=42,
    temperature=0.6,
    top_p=0.9,
    repetition_penalty=1.1,
    model_repo="",
    attention_mode="",
    batch_mode="",
    **kwargs,
):
    """
    Single Source of Truth (SSOT) for generating Kohya_ss / AI-Toolkit compliant JSON metadata.
    """
    caption = caption or kwargs.get("prompt", "")
    tags = tags or kwargs.get("clip_l", "")
    negative = negative or kwargs.get("negative_prompt", "")

    clean_tw = trigger_word.strip().rstrip(",").strip() if trigger_word else ""
    manifest = {
        "caption": caption,
        "tags": tags,
        "negative": negative,
        # Backward-compatibility keys for external tools (Kohya_ss, AI-Toolkit)
        "prompt": caption,
        "clip_l": tags,
        "clip_l_prompt": tags,
        "t5_prompt": caption if is_dual_active else tags,
        "negative_prompt": negative,
        "is_dual_prompt": is_dual_active,
        "is_artifact_audit": is_audit_active,
        "prompt_type": prompt_type,
        "artistic_style": artistic_style,
        "system_prompt_preset": system_prompt_preset,
        "system_prompt_mode": system_prompt_mode,
        "trigger_word": clean_tw,
        "tags_list": tags_list if tags_list else [],
        "shuffled": shuffle_tags,
        "seed": seed,
        "temperature": temperature,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty,
        "model_repo": model_repo,
        "attention_mode": attention_mode,
        "batch_mode": batch_mode,
    }
    manifest.update(kwargs)
    return manifest

