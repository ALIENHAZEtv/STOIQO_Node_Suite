"""
[STOIQO] Universal Webhook Notifier & Pipeline Exporter Node
A pure-Python, zero-dependency ComfyUI node for dispatching real-time notifications
to Discord, Slack, Telegram, n8n, or any HTTP REST webhook, alongside saving local JSON manifests.
"""

import json
import os
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

try:
    import folder_paths
except ImportError:
    folder_paths = None

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


class StoiqoWebhookNotifierNode:
    """
    [STOIQO] Webhook Notifier & Pipeline Exporter
    Universal notification hub for ComfyUI. Dispatches generation results, parameters,
    and completion alerts to Discord, Slack, Telegram, or custom webhooks, while
    exporting structured JSON metadata.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "service_format": (
                    [
                        "Generic JSON POST",
                        "Discord Webhook Embed",
                        "Slack Incoming Webhook",
                        "Telegram Bot API",
                    ],
                    {
                        "default": "Discord Webhook Embed",
                        "tooltip": "Formatting preset for the outgoing notification payload.",
                    },
                ),
                "webhook_url": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "tooltip": "Webhook target URL (e.g. Discord channel webhook, Slack webhook, or HTTP REST endpoint).",
                    },
                ),
                "title": (
                    "STRING",
                    {
                        "default": "ComfyUI Generation Complete",
                        "tooltip": "Notification title or subject header.",
                    },
                ),
                "message": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "Generation finished successfully.",
                        "tooltip": "Custom message or caption to include in the notification.",
                    },
                ),
                "save_json_manifest": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Save a local timestamped JSON manifest file with full execution parameters.",
                    },
                ),
                "manifest_subfolder": (
                    "STRING",
                    {
                        "default": "stoiqo_manifests",
                        "tooltip": "Subfolder inside ComfyUI output directory to store JSON manifests.",
                    },
                ),
            },
            "optional": {
                "pipe": ("*", {"tooltip": "Optional pipeline bus to extract prompt, seed, model, and metadata."}),
                "images": ("IMAGE", {"tooltip": "Optional image tensor for metadata extraction and pass-through."}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "tooltip": "Optional generation seed."}),
                "telegram_chat_id": (
                    "STRING",
                    {"default": "", "tooltip": "Target Chat ID if using Telegram Bot API."},
                ),
                "timeout_seconds": (
                    "INT",
                    {"default": 10, "min": 2, "max": 60, "tooltip": "Network request timeout in seconds."},
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("*", "IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("pipe", "images", "status", "json_payload")
    FUNCTION = "dispatch_notification"
    CATEGORY = "STOIQO/Pipeline"
    OUTPUT_NODE = True

    def dispatch_notification(
        self,
        service_format: str,
        webhook_url: str,
        title: str,
        message: str,
        save_json_manifest: bool = True,
        manifest_subfolder: str = "webhook_manifests",
        pipe=None,
        images=None,
        seed: int = 0,
        telegram_chat_id: str = "",
        timeout_seconds: int = 10,
        unique_id=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="WebhookNotifier") as timer:
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            iso_timestamp = datetime.now().isoformat()

            # Extract metadata from pipe if available
            extracted_prompt = ""
            extracted_seed = seed
            model_info = "Unknown"

            if pipe is not None and isinstance(pipe, dict):
                extracted_prompt = (
                    pipe.get("positive_prompt")
                    or pipe.get("positive")
                    or pipe.get("text")
                    or ""
                )
                if not isinstance(extracted_prompt, str):
                    extracted_prompt = str(extracted_prompt)

                if extracted_seed == 0 and "seed" in pipe and isinstance(pipe["seed"], int):
                    extracted_seed = pipe["seed"]

                if "model" in pipe and pipe["model"] is not None:
                    model_info = type(pipe["model"]).__name__

            # Build metadata manifest payload
            manifest_data = {
                "timestamp": iso_timestamp,
                "title": title,
                "message": message,
                "seed": extracted_seed,
                "prompt": extracted_prompt,
                "model_type": model_info,
                "node_id": str(unique_id) if unique_id else None,
            }

            if images is not None and hasattr(images, "shape"):
                manifest_data["image_dimensions"] = {
                    "batch_size": int(images.shape[0]),
                    "height": int(images.shape[1]),
                    "width": int(images.shape[2]),
                    "channels": int(images.shape[3]) if len(images.shape) > 3 else 1,
                }

            json_manifest_str = json.dumps(manifest_data, indent=2, ensure_ascii=False)

            # Local manifest file saving
            saved_manifest_path = ""
            if save_json_manifest:
                try:
                    if folder_paths is not None and hasattr(folder_paths, "get_output_directory"):
                        base_output = folder_paths.get_output_directory()
                    else:
                        base_output = os.path.join(os.getcwd(), "output")

                    target_dir = os.path.join(base_output, manifest_subfolder.strip("/\\"))
                    os.makedirs(target_dir, exist_ok=True)

                    filename = f"manifest_{int(time.time())}_{extracted_seed}.json"
                    file_path = os.path.join(target_dir, filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(json_manifest_str)
                    saved_manifest_path = file_path
                except Exception as ex:
                    print(f"[STOIQO Webhook] Warning: Failed to save JSON manifest: {ex}")

            # Prepare Webhook Payload
            status_parts = []
            if saved_manifest_path:
                status_parts.append(f"Manifest saved ({os.path.basename(saved_manifest_path)})")

            clean_url = webhook_url.strip() if webhook_url else ""
            if clean_url:
                parsed = urlparse(clean_url)
                if parsed.scheme.lower() not in ("http", "https"):
                    err_msg = f"Webhook URL rejected: scheme '{parsed.scheme}' not allowed. Only http/https supported."
                    status_parts.append(err_msg)
                    print(f"[STOIQO Webhook] {err_msg}")
                    final_status = " | ".join(status_parts) if status_parts else "Rejected"
                    return inject_telemetry(
                        (pipe, images, final_status, json_manifest_str),
                        timer.get_stats(),
                    )

                try:
                    req_payload = None
                    headers = {"User-Agent": "STOIQO-ComfyUI-Suite/1.0"}

                    if service_format == "Discord Webhook Embed":
                        headers["Content-Type"] = "application/json"
                        embed_fields = [
                            {"name": "Seed", "value": f"`{extracted_seed}`", "inline": True},
                            {"name": "Timestamp", "value": timestamp_str, "inline": True},
                        ]
                        if extracted_prompt:
                            embed_fields.append({
                                "name": "Prompt",
                                "value": extracted_prompt[:1000] + ("..." if len(extracted_prompt) > 1000 else ""),
                                "inline": False,
                            })

                        req_payload = json.dumps({
                            "username": "ComfyUI (STOIQO)",
                            "avatar_url": "https://raw.githubusercontent.com/Comfy-Org/ComfyUI_frontend/main/assets/favicon.ico",
                            "embeds": [{
                                "title": title,
                                "description": message,
                                "color": 0x06B6D4,  # STOIQO Cyan
                                "fields": embed_fields,
                                "footer": {"text": "STOIQO Universal Pipeline"},
                                "timestamp": iso_timestamp,
                            }]
                        }).encode("utf-8")

                    elif service_format == "Slack Incoming Webhook":
                        headers["Content-Type"] = "application/json"
                        req_payload = json.dumps({
                            "text": f"*{title}*\n{message}\n*Seed:* `{extracted_seed}`\n*Time:* {timestamp_str}"
                        }).encode("utf-8")

                    elif service_format == "Telegram Bot API":
                        headers["Content-Type"] = "application/json"
                        # For Telegram: URL is https://api.telegram.org/bot<token>/sendMessage
                        tg_text = f"*{title}*\n\n{message}\n\n*Seed:* `{extracted_seed}`\n*Timestamp:* {timestamp_str}"
                        if extracted_prompt:
                            tg_text += f"\n*Prompt:* {extracted_prompt[:300]}"
                        req_payload = json.dumps({
                            "chat_id": telegram_chat_id.strip(),
                            "text": tg_text,
                            "parse_mode": "Markdown",
                        }).encode("utf-8")

                    else:
                        # Generic JSON POST
                        headers["Content-Type"] = "application/json"
                        req_payload = json_manifest_str.encode("utf-8")

                    # Dispatch HTTP Request
                    req = urllib.request.Request(clean_url, data=req_payload, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                        code = response.getcode()
                        status_parts.append(f"Webhook dispatched (HTTP {code})")

                except urllib.error.HTTPError as http_err:
                    err_msg = f"Webhook HTTP Error {http_err.code}"
                    status_parts.append(err_msg)
                    print(f"[STOIQO Webhook] {err_msg}: {http_err.reason}")
                except Exception as req_err:
                    err_msg = f"Webhook Failed ({type(req_err).__name__})"
                    status_parts.append(err_msg)
                    print(f"[STOIQO Webhook] Network exception: {req_err}")
            else:
                if not save_json_manifest:
                    status_parts.append("Idle (No webhook URL and manifest saving disabled)")

            final_status = " | ".join(status_parts) if status_parts else "OK"
            telemetry = timer.get_stats()

            return inject_telemetry(
                (pipe, images, final_status, json_manifest_str),
                telemetry,
            )
