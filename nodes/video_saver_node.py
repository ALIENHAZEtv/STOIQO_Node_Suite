"""
[STOIQO] Pro Video Saver & Frame Exporter Node
High-efficiency video exporter for MiniMax Video (Hailuo / Video-01) and video pipelines.
Encodes image frame sequences into MP4 (H.264), WebM, or animated GIF with motion prompt sidecars,
framerate configuration (24/30/60 fps), and zero canvas clutter.
"""

import os
import json
import re
import subprocess
from datetime import datetime
import numpy as np
import torch
from PIL import Image

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


try:
    import folder_paths
except ImportError:
    import tempfile

    class _MockFolderPaths:
        @staticmethod
        def get_output_directory():
            return "./output"
        @staticmethod
        def get_temp_directory():
            return tempfile.gettempdir()
    folder_paths = _MockFolderPaths()


def _resolve_video_tokens(pattern, width, height, fps, counter=1):
    now = datetime.now()
    resolved = pattern

    resolved = resolved.replace("%date%", now.strftime("%Y-%m-%d"))
    resolved = resolved.replace("%time%", now.strftime("%H%M%S"))
    resolved = resolved.replace("%year%", now.strftime("%Y"))
    resolved = resolved.replace("%month%", now.strftime("%m"))
    resolved = resolved.replace("%day%", now.strftime("%d"))
    resolved = resolved.replace("%width%", str(width))
    resolved = resolved.replace("%height%", str(height))
    resolved = resolved.replace("%fps%", f"{int(fps)}fps")
    resolved = resolved.replace("%counter%", f"{counter:04d}")

    resolved = re.sub(r"[<>:\"|?*]", "_", resolved)
    return resolved


class StoiqoVideoSaverNode:
    """
    [STOIQO] Pro Video Saver & Frame Exporter
    Encodes tensor frame batches from MiniMax Video into high-bitrate MP4 or WebM files,
    complete with sidecar motion prompts and playback sync for ComfyUI and external video players.
    """

    FORMAT_OPTIONS = [
        "MP4 (H.264)",
        "WebM (VP9)",
        "GIF (Animated)",
    ]

    SIDECAR_OPTIONS = [
        "Both (.json + .txt)",
        "JSON Metadata (.json)",
        "TXT Prompt (.txt)",
        "None",
    ]

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": (
                    "IMAGE",
                    {
                        "tooltip": "Batch of video frames as image tensor [B, H, W, C].",
                    },
                ),
                "fps": (
                    "FLOAT",
                    {
                        "default": 24.0,
                        "min": 1.0,
                        "max": 120.0,
                        "step": 1.0,
                        "tooltip": "Playback framerate. 24.0 fps is the cinematic standard for MiniMax Video.",
                    },
                ),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "%date%_minimax_%fps%",
                        "tooltip": "Naming pattern. Supports %date%, %time%, %fps%, %width%, %height%, %counter%",
                    },
                ),
                "format": (
                    cls.FORMAT_OPTIONS,
                    {
                        "default": cls.FORMAT_OPTIONS[0],
                        "tooltip": "Export container and codec.",
                    },
                ),
                "quality": (
                    "INT",
                    {
                        "default": 85,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Encoding quality (higher = larger file and sharper motion gradients).",
                    },
                ),
            },
            "optional": {
                "subfolder": (
                    "STRING",
                    {
                        "default": "StoiqoVideos/%date%",
                        "tooltip": "Destination folder inside workspace outputs.",
                    },
                ),
                "motion_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Camera kinematics and physical motion prompt used for MiniMax generation.",
                    },
                ),
                "sidecar_metadata": (
                    cls.SIDECAR_OPTIONS,
                    {
                        "default": cls.SIDECAR_OPTIONS[0],
                        "tooltip": "Generate companion motion prompt and technical metadata files.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("images", "file_path", "filename", "metadata_json")
    FUNCTION = "save_video_pro"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def save_video_pro(
        self,
        images,
        fps=24.0,
        filename_prefix="%date%_minimax_%fps%",
        format="MP4 (H.264)",
        quality=85,
        subfolder="StoiqoVideos/%date%",
        motion_prompt="",
        sidecar_metadata="Both (.json + .txt)",
        prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="VideoSaver") as timer:
            if not isinstance(images, torch.Tensor) or images.ndim != 4:
                raise ValueError("[STOIQO Pro Video Saver] Invalid frames input: expected 4D tensor [B, H, W, C]")


        num_frames, h, w, c = images.shape
        duration_sec = round(float(num_frames) / max(1.0, float(fps)), 2)

        if "WebM" in format:
            ext = ".webm"
        elif "GIF" in format:
            ext = ".gif"
        else:
            ext = ".mp4"

        resolved_subfolder = _resolve_video_tokens(subfolder, w, h, fps)
        target_dir = os.path.join(self.output_dir, resolved_subfolder)
        os.makedirs(target_dir, exist_ok=True)

        pattern_base = _resolve_video_tokens(filename_prefix, w, h, fps, counter=1)
        base_clean = pattern_base.replace("%counter%", "")
        existing = [f for f in os.listdir(target_dir) if f.startswith(base_clean) and f.endswith(ext)]
        counter = len(existing) + 1

        raw_filename = _resolve_video_tokens(filename_prefix, w, h, fps, counter=counter)
        if "%counter%" not in filename_prefix:
            raw_filename = f"{raw_filename}_{counter:04d}"

        file_name = f"{raw_filename}{ext}"
        file_path = os.path.join(target_dir, file_name)

        # Convert tensor to uint8 numpy frames [B, H, W, C]
        frames_np = (255.0 * images.cpu().numpy()).clip(0, 255).astype(np.uint8)

        # Video Encoding Pipeline
        encoded = False

        # Attempt 1: imageio with pyav or ffmpeg plugin
        if not encoded:
            try:
                import imageio
                if ext == ".mp4":
                    writer = imageio.get_writer(
                        file_path,
                        fps=fps,
                        codec="libx264",
                        quality=max(1, min(10, int(quality / 10))),
                        pixelformat="yuv420p",
                    )
                elif ext == ".webm":
                    writer = imageio.get_writer(
                        file_path,
                        fps=fps,
                        codec="libvpx-vp9",
                        pixelformat="yuv420p",
                    )
                elif ext == ".gif":
                    writer = imageio.get_writer(file_path, duration=1000.0 / max(1.0, float(fps)))
                else:
                    writer = imageio.get_writer(file_path, fps=fps)

                for idx in range(num_frames):
                    writer.append_data(frames_np[idx])
                writer.close()
                encoded = True
            except Exception as e:
                print(f"[STOIQO Video Saver] imageio encoding fallback: {e}")

        # Attempt 2: OpenCV cv2 VideoWriter
        if not encoded and ext == ".mp4":
            try:
                import cv2
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out_writer = cv2.VideoWriter(file_path, fourcc, float(fps), (int(w), int(h)))
                for idx in range(num_frames):
                    bgr = cv2.cvtColor(frames_np[idx], cv2.COLOR_RGB2BGR)
                    out_writer.write(bgr)
                out_writer.release()
                encoded = True
            except Exception as e:
                print(f"[STOIQO Video Saver] cv2 encoding fallback: {e}")

        # Attempt 3: PIL Animated GIF / WebP fallback
        if not encoded:
            try:
                pil_frames = [Image.fromarray(frames_np[i]) for i in range(num_frames)]
                frame_duration_ms = int(1000.0 / max(1.0, float(fps)))
                if ext != ".gif":
                    file_name = os.path.splitext(file_name)[0] + ".gif"
                    file_path = os.path.splitext(file_path)[0] + ".gif"
                pil_frames[0].save(
                    file_path,
                    save_all=True,
                    append_images=pil_frames[1:],
                    duration=frame_duration_ms,
                    loop=0,
                )
                encoded = True
            except Exception as e:
                print(f"[STOIQO Video Saver] PIL fallback failed: {e}")

        file_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        size_mb = file_bytes / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{file_bytes / 1024:.1f} KB"

        sidecar_data = {
            "filename": file_name,
            "width": w,
            "height": h,
            "total_frames": num_frames,
            "fps": fps,
            "duration_seconds": duration_sec,
            "file_size": size_str,
            "format": format,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "motion_prompt": motion_prompt.strip(),
        }

        if sidecar_metadata in ("Both (.json + .txt)", "JSON Metadata (.json)"):
            json_path = os.path.splitext(file_path)[0] + ".json"
            try:
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(sidecar_data, jf, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[STOIQO Video Saver] Warning saving JSON sidecar: {e}")

        if sidecar_metadata in ("Both (.json + .txt)", "TXT Prompt (.txt)") and motion_prompt.strip():
            txt_path = os.path.splitext(file_path)[0] + ".txt"
            try:
                with open(txt_path, "w", encoding="utf-8") as tf:
                    tf.write(f"=== MINIMAX VIDEO MOTION PROMPT ===\nFPS: {fps}\nFRAMES: {num_frames}\n\n{motion_prompt.strip()}\n")
            except Exception as e:
                print(f"[STOIQO Video Saver] Warning saving TXT prompt: {e}")

        meta_dump = json.dumps(sidecar_data, indent=2)

        ui_output = [
            {
                "filename": file_name,
                "subfolder": resolved_subfolder,
                "type": self.type,
                "format": ext.lstrip("."),
                "fps": float(fps),
                "total_frames": int(num_frames),
                "duration": float(duration_sec),
                "width": int(w),
                "height": int(h),
            }
        ]

        print(f"[STOIQO] Pro Video Saver: Successfully exported '{file_name}' ({num_frames} frames @ {fps} fps, {duration_sec}s, {size_str})")

        return inject_telemetry({
            "ui": {
                "gifs": ui_output if ext == ".gif" else [],
                "videos": ui_output if ext != ".gif" else [],
                "images": ui_output,
            },
            "result": (
                images,
                file_path,
                file_name,
                meta_dump,
            ),
        }, timer.get_stats())

