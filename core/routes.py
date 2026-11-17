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
                    return web.json_response({
                        "status": "ok",
                        "path": selected_path,
                        "folder_path": selected_path,
                    })

            if not any(getattr(r, "path", None) == "/stoiqo/open_folder" for r in routes):
                @routes.post("/stoiqo/open_folder")
                async def open_system_folder(request):
                    import sys
                    import subprocess
                    import os
                    data = {}
                    try:
                        if request.can_read_body:
                            data = await request.json()
                    except Exception:
                        pass
                    folder_path = data.get("folder_path", "")
                    if folder_path and os.path.exists(folder_path):
                        norm_path = os.path.normpath(folder_path)
                        if os.path.isfile(norm_path):
                            norm_path = os.path.dirname(norm_path)
                        if sys.platform == "win32":
                            os.startfile(norm_path)
                        elif sys.platform == "darwin":
                            subprocess.Popen(["open", norm_path])
                        else:
                            subprocess.Popen(["xdg-open", norm_path])
                        return web.json_response({"success": True, "path": norm_path})
                    return web.json_response({"success": False, "error": "Folder not found"}, status=404)
    except Exception as exc:
        print(f"[STOIQO] Notice: route registration deferred: {exc}")


