"""
[STOIQO] Show Prompt Node
Display node for previewing generated prompt strings directly on the ComfyUI canvas.
"""

class StoiqoShowPromptNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"text": ("STRING", {"forceInput": True})}}

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "display"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO/Prompt Engine"

    def display(self, text):
        if isinstance(text, list):
            display_list = []
            for item in text:
                if isinstance(item, list):
                    display_list.extend([str(x) for x in item])
                elif item is not None:
                    display_list.append(str(item))
            return {"ui": {"text": display_list}, "result": (display_list,)}
        text_str = str(text) if text is not None else ""
        return {"ui": {"text": [text_str]}, "result": ([text_str],)}
