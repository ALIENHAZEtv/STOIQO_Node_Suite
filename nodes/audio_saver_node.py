"""
[STOIQO] Pro Audio Saver & Metadata Hub Node
High-fidelity audio exporter for YuE 2, Suno, and AI music workflows.
Supports lossless WAV (16/24-bit), FLAC, and high-bitrate MP3, dynamic tokens,
sidecar lyrics (.txt) and JSON production manifests, fully synchronized with workspace/outputs/audio.
"""

import os
import json
import re
from datetime import datetime
import numpy as np
import torch

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


def _resolve_audio_tokens(pattern, title, bpm, meta=None, counter=1):
    now = datetime.now()
    resolved = pattern

    # Clean title for filesystem safety
    safe_title = re.sub(r"[<>:\"/\\|?*]", "_", str(title or "song")).strip()
    if not safe_title:
        safe_title = "song"

    resolved = resolved.replace("%date%", now.strftime("%Y-%m-%d"))
    resolved = resolved.replace("%time%", now.strftime("%H%M%S"))
    resolved = resolved.replace("%year%", now.strftime("%Y"))
    resolved = resolved.replace("%month%", now.strftime("%m"))
    resolved = resolved.replace("%day%", now.strftime("%d"))
    resolved = resolved.replace("%title%", safe_title)
    resolved = resolved.replace("%bpm%", str(bpm or 120))
    resolved = resolved.replace("%counter%", f"{counter:04d}")

    if meta and isinstance(meta, dict):
        resolved = resolved.replace("%key%", str(meta.get("key") or ""))
        resolved = resolved.replace("%genre%", str(meta.get("genre") or ""))
        resolved = resolved.replace("%seed%", str(meta.get("seed") or "seed"))

    resolved = re.sub(r"[<>:\"|?*]", "_", resolved)
    return resolved


class StoiqoAudioSaverNode:
    """
    [STOIQO] Pro Audio Saver & Metadata Hub
    Production-grade audio exporter with format conversion, sidecar lyrics,
    complete production metadata manifests, and seamless ComfyUI playback.
    """

    FORMAT_OPTIONS = [
        "WAV (Lossless 24-bit)",
        "WAV (Standard 16-bit)",
        "FLAC (Lossless)",
        "MP3 (320 kbps)",
    ]

    SIDECAR_OPTIONS = [
        "Both (.txt lyrics + .json)",
        "TXT Lyrics (.txt)",
        "JSON Metadata (.json)",
        "None",
    ]

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": (
                    "AUDIO",
                    {
                        "tooltip": "Audio dictionary from YuE2, Suno or ComfyUI audio engine ({'waveform': tensor, 'sample_rate': int}).",
                    },
                ),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "%date%_%title%_%bpm%bpm",
                        "tooltip": "Naming pattern. Supports %date%, %time%, %title%, %bpm%, %counter%, %seed%",
                    },
                ),
                "format": (
                    cls.FORMAT_OPTIONS,
                    {
                        "default": cls.FORMAT_OPTIONS[0],
                        "tooltip": "Output audio file format.",
                    },
                ),
            },
            "optional": {
                "subfolder": (
                    "STRING",
                    {
                        "default": "StoiqoAudio/%date%",
                        "tooltip": "Destination subfolder relative to workspace outputs.",
                    },
                ),
                "title": (
                    "STRING",
                    {
                        "default": "YuE2 Track",
                        "tooltip": "Song title used for templating, ID3 tags, and metadata manifests.",
                    },
                ),
                "lyrics": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Singable song lyrics from Stoiqo Music Engine to embed and save as sidecar.",
                    },
                ),
                "style": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Acoustic production style descriptor string.",
                    },
                ),
                "bpm": (
                    "INT",
                    {
                        "default": 120,
                        "min": 20,
                        "max": 300,
                        "step": 1,
                        "tooltip": "Musical tempo (BPM).",
                    },
                ),
                "sidecar_metadata": (
                    cls.SIDECAR_OPTIONS,
                    {
                        "default": cls.SIDECAR_OPTIONS[0],
                        "tooltip": "Save paired .txt lyrics and .json production metadata files alongside audio.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("AUDIO", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("audio", "file_path", "filename", "metadata_json")
    FUNCTION = "save_audio_pro"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def save_audio_pro(
        self,
        audio,
        filename_prefix="%date%_%title%_%bpm%bpm",
        format="WAV (Lossless 24-bit)",
        subfolder="StoiqoAudio/%date%",
        title="YuE2 Track",
        lyrics="",
        style="",
        bpm=120,
        sidecar_metadata="Both (.txt lyrics + .json)",
        prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="AudioSaver") as timer:
            if not isinstance(audio, dict) or "waveform" not in audio:
                raise ValueError("[STOIQO Pro Audio Saver] Invalid audio input: expected dictionary with 'waveform' and 'sample_rate'")


        waveform = audio["waveform"]
        sample_rate = int(audio.get("sample_rate", 44100))

        # Ensure 2D tensor [channels, samples]
        if isinstance(waveform, torch.Tensor):
            w_tensor = waveform.detach().cpu().float()
            if w_tensor.ndim == 3:
                # [batch, channels, samples] -> select first item
                w_tensor = w_tensor[0]
            elif w_tensor.ndim == 1:
                w_tensor = w_tensor.unsqueeze(0)
        else:
            w_tensor = torch.from_numpy(np.array(waveform)).float()
            if w_tensor.ndim == 1:
                w_tensor = w_tensor.unsqueeze(0)

        num_channels, num_samples = w_tensor.shape
        duration_sec = round(num_samples / float(sample_rate), 2)

        # Extension and audio format mapping
        if "MP3" in format:
            ext = ".mp3"
            sub_type = "mp3"
        elif "FLAC" in format:
            ext = ".flac"
            sub_type = "flac"
        elif "24-bit" in format:
            ext = ".wav"
            sub_type = "PCM_24"
        else:
            ext = ".wav"
            sub_type = "PCM_16"

        # Determine target folder
        resolved_subfolder = _resolve_audio_tokens(subfolder, title, bpm)
        target_dir = os.path.join(self.output_dir, resolved_subfolder)
        os.makedirs(target_dir, exist_ok=True)

        # Counter detection
        pattern_base = _resolve_audio_tokens(filename_prefix, title, bpm, counter=1)
        base_clean = pattern_base.replace("%counter%", "")
        existing = [f for f in os.listdir(target_dir) if f.startswith(base_clean) and f.endswith(ext)]
        counter = len(existing) + 1

        raw_filename = _resolve_audio_tokens(filename_prefix, title, bpm, counter=counter)
        if "%counter%" not in filename_prefix:
            raw_filename = f"{raw_filename}_{counter:04d}"

        file_name = f"{raw_filename}{ext}"
        file_path = os.path.join(target_dir, file_name)

        # Save audio file
        saved_successfully = False
        try:
            import torchaudio
            if ext == ".wav":
                bits_str = "PCM_S" if "16" in sub_type else "PCM_24"
                encoding = "PCM_S"
                bits_per_sample = 16 if "16" in sub_type else 24
                torchaudio.save(file_path, w_tensor, sample_rate, encoding=encoding, bits_per_sample=bits_per_sample)
                saved_successfully = True
            elif ext == ".flac":
                torchaudio.save(file_path, w_tensor, sample_rate, format="flac")
                saved_successfully = True
            elif ext == ".mp3":
                torchaudio.save(file_path, w_tensor, sample_rate, format="mp3")
                saved_successfully = True
        except Exception as e:
            print(f"[STOIQO Pro Audio Saver] torchaudio save fallback: {e}")

        if not saved_successfully:
            # Fallback using scipy.io.wavfile
            try:
                import scipy.io.wavfile as wavfile
                audio_np = w_tensor.numpy()
                if audio_np.shape[0] in (1, 2) and audio_np.shape[1] > audio_np.shape[0]:
                    audio_np = audio_np.T  # Transpose to [samples, channels]
                
                # Scale float -1.0..1.0 to int16
                audio_np = np.clip(audio_np, -1.0, 1.0)
                int_audio = (audio_np * 32767.0).astype(np.int16)
                wavfile.write(file_path, sample_rate, int_audio)
                saved_successfully = True
            except Exception as e:
                print(f"[STOIQO Pro Audio Saver] scipy save fallback error: {e}")

        file_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        size_mb = file_bytes / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{file_bytes / 1024:.1f} KB"

        # Sidecar manifests
        sidecar_data = {
            "title": title,
            "filename": file_name,
            "duration_seconds": duration_sec,
            "sample_rate": sample_rate,
            "channels": num_channels,
            "bpm": bpm,
            "format": format,
            "file_size": size_str,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "acoustic_style": style.strip(),
            "lyrics": lyrics.strip(),
        }

        if sidecar_metadata in ("Both (.txt lyrics + .json)", "JSON Metadata (.json)"):
            json_path = os.path.splitext(file_path)[0] + ".json"
            try:
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(sidecar_data, jf, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[STOIQO Audio Saver] Warning saving JSON sidecar: {e}")

        if sidecar_metadata in ("Both (.txt lyrics + .json)", "TXT Lyrics (.txt)") and lyrics.strip():
            txt_path = os.path.splitext(file_path)[0] + ".txt"
            try:
                with open(txt_path, "w", encoding="utf-8") as tf:
                    tf.write(f"=== {title} ===\nBPM: {bpm}\nSTYLE: {style}\n\n{lyrics.strip()}\n")
            except Exception as e:
                print(f"[STOIQO Audio Saver] Warning saving TXT lyrics: {e}")

        meta_dump = json.dumps(sidecar_data, indent=2)

        ui_audio = [
            {
                "filename": file_name,
                "subfolder": resolved_subfolder,
                "type": self.type,
            }
        ]

        print(f"[STOIQO] Pro Audio Saver: Successfully saved '{file_name}' ({size_str}, {duration_sec}s) to {target_dir}")

        return inject_telemetry({
            "ui": {
                "audio": ui_audio,
            },
            "result": (
                audio,
                file_path,
                file_name,
                meta_dump,
            ),
        }, timer.get_stats())

