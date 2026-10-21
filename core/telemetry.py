"""
[STOIQO] Node Execution Telemetry & Performance Tracker
Captures exact wall-clock execution time (ms) and peak CUDA VRAM allocation (GB),
broadcasting metrics via WebSocket and embedding them in ComfyUI node UI payloads.
"""

import time
import torch

try:
    from server import PromptServer
except ImportError:
    PromptServer = None


class NodeTelemetryTimer:
    """
    Context manager to accurately measure execution duration and peak VRAM.
    Usage:
        with NodeTelemetryTimer(node_id=unique_id, node_name="TurboSampler") as timer:
            # execute heavy model inference
            ...
        telemetry = timer.get_stats()
    """

    def __init__(self, node_id=None, node_name="STOIQO_NODE"):
        self.node_id = str(node_id) if node_id is not None else None
        self.node_name = node_name
        self.start_time = 0.0
        self.has_cuda = torch.cuda.is_available()

    def __enter__(self):
        if self.has_cuda:
            try:
                torch.cuda.reset_peak_memory_stats()
            except Exception:
                pass
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def stop(self):
        """Allows manual stopping outside of context manager syntax."""
        return self.get_stats()

    def get_stats(self):
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
        vram_peak_gb = 0.0

        if self.has_cuda:
            try:
                vram_peak_gb = torch.cuda.max_memory_allocated() / (1024.0 ** 3)
                if vram_peak_gb == 0.0:
                    vram_peak_gb = torch.cuda.memory_allocated() / (1024.0 ** 3)
            except Exception:
                vram_peak_gb = 0.0

        stats = {
            "time_ms": round(elapsed_ms, 1),
            "vram_gb": round(vram_peak_gb, 2),
            "node_name": self.node_name,
        }
        if self.node_id:
            stats["node_id"] = self.node_id

        # Broadcast via WebSocket if PromptServer is active
        if PromptServer is not None and hasattr(PromptServer, "instance") and PromptServer.instance:
            try:
                PromptServer.instance.send_sync("stoiqo_node_telemetry", stats)
            except Exception:
                pass

        return stats


class TelemetryResult(dict):
    """
    Hybrid dict/tuple return value for ComfyUI nodes.
    - Behaves as a dict with 'ui' and 'result' for ComfyUI's execution engine.
    - Unpacks as a tuple (matching 'result') for direct Python calls and tests.
    """

    def __iter__(self):
        if "result" in self and isinstance(self["result"], (list, tuple)):
            return iter(self["result"])
        return super().__iter__()

    def __getitem__(self, key):
        if isinstance(key, int) and "result" in self and isinstance(self["result"], (list, tuple)):
            return self["result"][key]
        return super().__getitem__(key)

    def __len__(self):
        if "result" in self and isinstance(self["result"], (list, tuple)):
            return len(self["result"])
        return super().__len__()


def inject_telemetry(result_data, telemetry_stats):
    """
    Injects telemetry statistics into a ComfyUI node execution return dictionary or tuple.
    Returns a TelemetryResult that satisfies both ComfyUI's execution engine (which expects
    a dict with 'ui' and 'result') and direct Python test calls (which expect tuple unpacking).
    """
    if isinstance(result_data, dict):
        res_dict = dict(result_data)
        if "ui" not in res_dict:
            res_dict["ui"] = {}
        res_dict["ui"]["stoiqo_telemetry"] = [telemetry_stats]
        return TelemetryResult(res_dict)

    if isinstance(result_data, (tuple, list)):
        return TelemetryResult({
            "ui": {
                "stoiqo_telemetry": [telemetry_stats],
            },
            "result": tuple(result_data),
        })

    return result_data

