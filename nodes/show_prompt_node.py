"""
[STOIQO] Show Prompt Node
Display node for previewing generated prompt strings directly on the ComfyUI canvas.
Features live token streaming, batch pagination, word/character/token telemetry, and 1-click clipboard actions.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from ..core import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core import NodeTelemetryTimer, inject_telemetry


class StoiqoShowPromptNode:
    """
    [STOIQO] Show Prompt Node
    Displays generated prompts, tags, negative prompts, or arbitrary text strings
    directly on the ComfyUI canvas with batch pagination, character/word counters,
    estimated token metrics, and instant clipboard export.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "forceInput": True,
                        "tooltip": "Prompt text or list of prompt strings to inspect and pass through.",
                    },
                ),
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "display"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def display(self, text):
        with NodeTelemetryTimer(node_name="ShowPrompt") as timer:
            display_list = []
            if isinstance(text, list):
                for item in text:
                    if isinstance(item, list):
                        display_list.extend([str(x) for x in item if x is not None])
                    elif item is not None:
                        display_list.append(str(item))
            elif text is not None:
                display_list.append(str(text))

            if not display_list:
                display_list = [""]

            # Compute detailed metrics per item
            stats = []
            for item in display_list:
                words = len(item.split())
                chars = len(item)
                est_tokens = max(1, int(words * 1.33)) if words > 0 else 0
                stats.append({
                    "chars": chars,
                    "words": words,
                    "tokens": est_tokens,
                })

            total_chars = sum(s["chars"] for s in stats)
            total_words = sum(s["words"] for s in stats)
            count = len(display_list)

            ui_payload = {
                "text": display_list,
                "count": [count],
                "stats": stats,
                "summary": [f"{count} item{'s' if count != 1 else ''} • {total_chars} chars • {total_words} words"],
            }

            return inject_telemetry(
                {
                    "ui": ui_payload,
                    "result": (display_list,),
                },
                timer.get_stats(),
            )
