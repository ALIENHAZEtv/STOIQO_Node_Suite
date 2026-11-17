"""
[STOIQO] Shared HTTP routes.
Registers /stoiqo/browse_folder, /stoiqo/open_folder, and the
Prompt Engine CRUD API endpoints (/stoiqo/api/prompt_engine/*).
Safe to call multiple times.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from .storage import open_native_folder_dialog
    from .image.crud_api import list_definitions, get_definition, save_definition, delete_definition
    from .image.loader import reload_image_definitions, SYSTEM_PERSONAS, PROMPT_TYPES, ARTISTIC_STYLES
except ImportError:
    from storage import open_native_folder_dialog
    from core.image.crud_api import list_definitions, get_definition, save_definition, delete_definition
    from core.image.loader import reload_image_definitions, SYSTEM_PERSONAS, PROMPT_TYPES, ARTISTIC_STYLES


def register_stoiqo_routes():
    """Registers /stoiqo HTTP endpoints with ComfyUI's PromptServer."""
    try:
        from server import PromptServer
        from aiohttp import web

        if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
            routes = PromptServer.instance.routes

            # 1. Native folder picker
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

            # 2. Native OS folder opener
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

            # 3. Prompt Engine CRUD: List definitions
            if not any(getattr(r, "path", None) == "/stoiqo/api/prompt_engine/list" for r in routes):
                @routes.get("/stoiqo/api/prompt_engine/list")
                async def api_list_definitions(request):
                    kind = request.query.get("kind", "styles")
                    items = await asyncio.to_thread(list_definitions, kind)
                    return web.json_response({"status": "ok", "kind": kind, "items": items})

            # 4. Prompt Engine CRUD: Get single definition
            if not any(getattr(r, "path", None) == "/stoiqo/api/prompt_engine/get" for r in routes):
                @routes.get("/stoiqo/api/prompt_engine/get")
                async def api_get_definition(request):
                    kind = request.query.get("kind", "styles")
                    name = request.query.get("name", "")
                    res = await asyncio.to_thread(get_definition, kind, name)
                    status_code = 200 if res.get("status") == "ok" else 404
                    return web.json_response(res, status=status_code)

            # 5. Prompt Engine CRUD: Create / Update definition
            if not any(getattr(r, "path", None) == "/stoiqo/api/prompt_engine/save" for r in routes):
                @routes.post("/stoiqo/api/prompt_engine/save")
                async def api_save_definition(request):
                    data = {}
                    try:
                        if request.can_read_body:
                            data = await request.json()
                    except Exception as e:
                        return web.json_response({"status": "error", "message": f"Invalid JSON: {e}"}, status=400)

                    kind = data.get("kind", "styles")
                    name = data.get("name", "")
                    body = data.get("body", "")
                    frontmatter = data.get("frontmatter", {})
                    original_name = data.get("original_name", "")

                    res = await asyncio.to_thread(save_definition, kind, name, body, frontmatter, original_name)
                    status_code = 200 if res.get("status") == "ok" else 400
                    return web.json_response(res, status=status_code)

            # 6. Prompt Engine CRUD: Delete definition
            if not any(getattr(r, "path", None) == "/stoiqo/api/prompt_engine/delete" for r in routes):
                @routes.post("/stoiqo/api/prompt_engine/delete")
                async def api_delete_definition(request):
                    data = {}
                    try:
                        if request.can_read_body:
                            data = await request.json()
                    except Exception as e:
                        return web.json_response({"status": "error", "message": f"Invalid JSON: {e}"}, status=400)

                    kind = data.get("kind", "styles")
                    name = data.get("name", "")

                    res = await asyncio.to_thread(delete_definition, kind, name)
                    status_code = 200 if res.get("status") == "ok" else 400
                    return web.json_response(res, status=status_code)

            # 7. Prompt Engine CRUD: Force Reload definitions
            if not any(getattr(r, "path", None) == "/stoiqo/api/prompt_engine/reload" for r in routes):
                @routes.post("/stoiqo/api/prompt_engine/reload")
                async def api_reload_definitions(request):
                    await asyncio.to_thread(reload_image_definitions)
                    from .image.loader import SYSTEM_PERSONAS as SP, PROMPT_TYPES as PT, ARTISTIC_STYLES as AS
                    return web.json_response({
                        "status": "ok",
                        "choices": {
                            "system_personas": SP,
                            "prompt_types": PT,
                            "artistic_styles": AS,
                        }
                    })

    except Exception as exc:
        print(f"[STOIQO] Notice: route registration deferred: {exc}")
