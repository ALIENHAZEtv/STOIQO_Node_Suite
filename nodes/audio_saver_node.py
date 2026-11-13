"""
[STOIQO] Pro Audio Saver & Metadata Hub Node
High-fidelity audio exporter for YuE 2, Suno, and AI music workflows.
Supports lossless WAV (16/24-bit), FLAC, and high-bitrate MP3, dynamic tokens,
sidecar lyrics (.txt) and JSON production manifests, fully synchronized with workspace/outputs/audio.
"""

import os
import json
import re
import shutil
import subprocess
import logging
from datetime import datetime
import numpy as np
import torch

logger = logging.getLogger("STOIQO")

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
        resolved = resolved.replace("%genre%", re.sub(r"[<>:\"/\\|?*]", "_", str(meta.get("genre") or "")).strip())
        resolved = resolved.replace("%style%", re.sub(r"[<>:\"/\\|?*]", "_", str(meta.get("style") or "")).strip())
        resolved = resolved.replace("%seed%", str(meta.get("seed") or "seed"))

    resolved = re.sub(r"[<>:\"|?*]", "_", resolved)
    return resolved


def _save_audio_stream(file_path, audio_np, sample_rate, ext, sub_type, title="", genre="", style="", bpm=120):
    """
    Multi-engine audio exporter supporting lossless 16/24-bit WAV, FLAC, and CBR 320k MP3.
    Engine hierarchy:
    1. FFmpeg (Subprocess) - Bitrate-perfect 320k MP3 & lossless FLAC with embedded ID3 metadata tags.
    2. SoundFile (libsndfile) - High-fidelity 16/24-bit PCM WAV, lossless FLAC, and native MP3.
    3. Torchaudio / PyAV - Intermediate encoding fallback.
    4. SciPy / Wave - Emergency PCM WAV fallback (properly renamed to .wav to prevent corruption).
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    num_channels = audio_np.shape[1] if audio_np.ndim > 1 else 1

    # ── 1. MP3 Export ───────────────────────────────────────────
    if ext == ".mp3":
        # Strategy A: FFmpeg pipe encoding with true 320k CBR and ID3 tags
        if shutil.which("ffmpeg"):
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "f32le",
                    "-ar", str(sample_rate),
                    "-ac", str(num_channels),
                    "-i", "pipe:0",
                    "-b:a", "320k",
                ]
                if title:
                    cmd.extend(["-metadata", f"title={title}"])
                if genre:
                    cmd.extend(["-metadata", f"genre={genre}"])
                if style:
                    cmd.extend(["-metadata", f"comment={style}"])
                cmd.extend(["-metadata", "artist=STOIQO Suite"])
                cmd.append(file_path)

                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.communicate(input=audio_np.tobytes())
                if proc.returncode == 0 and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path, True
            except Exception as e:
                logger.warning(f"[Audio Saver] FFmpeg MP3 encoding fallback: {e}")

        # Strategy B: SoundFile MP3
        try:
            import soundfile as sf
            sf.write(file_path, audio_np, sample_rate, format="MP3")
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path, True
        except Exception:
            pass

    # ── 2. FLAC Export ──────────────────────────────────────────
    elif ext == ".flac":
        # Strategy A: SoundFile lossless FLAC
        try:
            import soundfile as sf
            sf.write(file_path, audio_np, sample_rate, format="FLAC")
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path, True
        except Exception:
            pass

        # Strategy B: FFmpeg lossless FLAC
        if shutil.which("ffmpeg"):
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "f32le",
                    "-ar", str(sample_rate),
                    "-ac", str(num_channels),
                    "-i", "pipe:0",
                    "-c:a", "flac",
                    "-compression_level", "8",
                    file_path,
                ]
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.communicate(input=audio_np.tobytes())
                if proc.returncode == 0 and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path, True
            except Exception:
                pass

    # ── 3. WAV Export (or Safe Fallback for MP3/FLAC) ───────────
    wav_target = file_path if ext == ".wav" else os.path.splitext(file_path)[0] + ".wav"
    if ext != ".wav":
        logger.info(f"[Audio Saver] Notice: Encoded format '{ext}' unavailable; saving as lossless WAV: {wav_target}")

    subtype = "PCM_24" if sub_type == "PCM_24" else "PCM_16"

    # Strategy A: SoundFile WAV
    try:
        import soundfile as sf
        sf.write(wav_target, audio_np, sample_rate, format="WAV", subtype=subtype)
        if os.path.exists(wav_target) and os.path.getsize(wav_target) > 0:
            return wav_target, True
    except Exception:
        pass

    # Strategy B: FFmpeg PCM WAV
    if shutil.which("ffmpeg"):
        try:
            codec = "pcm_s24le" if subtype == "PCM_24" else "pcm_s16le"
            cmd = [
                "ffmpeg", "-y",
                "-f", "f32le",
                "-ar", str(sample_rate),
                "-ac", str(num_channels),
                "-i", "pipe:0",
                "-c:a", codec,
                wav_target,
            ]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.communicate(input=audio_np.tobytes())
            if proc.returncode == 0 and os.path.exists(wav_target) and os.path.getsize(wav_target) > 0:
                return wav_target, True
        except Exception:
            pass

    # Strategy C: SciPy WAV fallback
    try:
        import scipy.io.wavfile as wavfile
        int_audio = (np.clip(audio_np, -1.0, 1.0) * 32767.0).astype(np.int16)
        wavfile.write(wav_target, sample_rate, int_audio)
        if os.path.exists(wav_target) and os.path.getsize(wav_target) > 0:
            return wav_target, True
    except Exception as e:
        logger.warning(f"[Audio Saver] scipy save fallback error: {e}")

    return file_path, False


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
                        "tooltip": "Naming pattern. Supports %date%, %time%, %title%, %bpm%, %genre%, %style%, %counter%",
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
                "genre": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": "Musical genre tags for ID3 metadata and JSON manifest.",
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
        genre="",
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
            try:
                sample_rate = int(audio.get("sample_rate", 44100))
                if sample_rate <= 0:
                    sample_rate = 44100
            except (ValueError, TypeError):
                sample_rate = 44100

            # Normalize tensor layout: ensure [channels, samples]
            if isinstance(waveform, torch.Tensor):
                w_tensor = waveform.detach().cpu().float()
            else:
                w_tensor = torch.from_numpy(np.array(waveform)).float()

            while w_tensor.ndim > 2:
                w_tensor = w_tensor[0]

            if w_tensor.ndim == 1:
                w_tensor = w_tensor.unsqueeze(0)
            elif w_tensor.ndim == 2:
                # If layout is inverted [samples, channels] where samples >> channels, transpose
                if w_tensor.shape[0] > 8 and w_tensor.shape[1] in (1, 2):
                    w_tensor = w_tensor.t()

            num_channels, num_samples = w_tensor.shape
            duration_sec = round(num_samples / float(sample_rate), 2)

            # Transpose to [samples, channels] for numpy exporters
            audio_np = w_tensor.t().numpy()
            audio_np = np.clip(audio_np, -1.0, 1.0)

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

            meta_tokens = {
                "genre": genre,
                "style": style,
                "key": "",
                "seed": "",
            }

            # Determine target folder
            resolved_subfolder = _resolve_audio_tokens(subfolder, title, bpm, meta=meta_tokens)
            target_dir = os.path.join(self.output_dir, resolved_subfolder)
            os.makedirs(target_dir, exist_ok=True)

            # Collision-free counter detection
            has_counter_token = "%counter%" in filename_prefix
            counter = 1
            while True:
                candidate_name = _resolve_audio_tokens(filename_prefix, title, bpm, meta=meta_tokens, counter=counter)
                if not has_counter_token:
                    candidate_name = f"{candidate_name}_{counter:04d}"
                candidate_path = os.path.join(target_dir, f"{candidate_name}{ext}")
                if not os.path.exists(candidate_path):
                    file_path = candidate_path
                    file_name = f"{candidate_name}{ext}"
                    break
                counter += 1

            # Multi-engine audio save
            actual_file_path, success = _save_audio_stream(
                file_path=file_path,
                audio_np=audio_np,
                sample_rate=sample_rate,
                ext=ext,
                sub_type=sub_type,
                title=title,
                genre=genre,
                style=style,
                bpm=bpm,
            )

            if not success or not os.path.exists(actual_file_path):
                raise RuntimeError(f"[STOIQO Pro Audio Saver] Failed to encode and save audio file to {file_path}")

            file_path = actual_file_path
            file_name = os.path.basename(file_path)

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
                "genre": genre.strip(),
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
                    logger.warning(f"[Audio Saver] Warning saving JSON sidecar: {e}")

            if sidecar_metadata in ("Both (.txt lyrics + .json)", "TXT Lyrics (.txt)") and lyrics.strip():
                txt_path = os.path.splitext(file_path)[0] + ".txt"
                try:
                    with open(txt_path, "w", encoding="utf-8") as tf:
                        tf.write(f"=== {title} ===\nBPM: {bpm}\nSTYLE: {style}\n\n{lyrics.strip()}\n")
                except Exception as e:
                    logger.warning(f"[Audio Saver] Warning saving TXT lyrics: {e}")

            meta_dump = json.dumps(sidecar_data, indent=2)

            ui_audio = [
                {
                    "filename": file_name,
                    "subfolder": resolved_subfolder,
                    "type": self.type,
                }
            ]

            logger.info(f"[Audio Saver] Successfully saved '{file_name}' ({size_str}, {duration_sec}s) to {target_dir}")

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
