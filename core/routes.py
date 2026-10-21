"""
[STOIQO] Shared HTTP routes.
Registers the /stoiqo/browse_folder endpoint (native folder picker) used by the Model Loader,
Visual Diff and Folder Iterator nodes. Safe to call multiple times.
"""

try:
    from .storage import open_native_folder_dialog
except ImportError:
    from storage import open_native_folder_dialog


def register_stoiqo_routes():
    """Registers /stoiqo/browse_folder endpoint with ComfyUI's PromptServer."""
    try:
        from server import PromptServer
        from aiohttp import web
        import asyncio

        if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
            routes = PromptServer.instance.routes
            if not any(getattr(r, "path", None) == "/stoiqo/browse_folder" for r in routes):
                @routes.post("/stoiqo/browse_folder")
                async def browse_model_folder(request):
                    data = {}
                    try:
                        if request.can_read_body:
                            data = await request.json()
                    except Exception:
                        pass
                    initial_dir = data.get("initial_dir", "")
                    selected_path = await asyncio.to_thread(open_native_folder_dialog, initial_dir)
                    return web.json_response({"path": selected_path})
    except Exception as exc:
        print(f"[STOIQO] Notice: route registration deferred: {exc}")


