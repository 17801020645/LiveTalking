###############################################################################
#  Custom digital-human orders
###############################################################################

import os
import time
from pathlib import Path

from server.platform_auth import json_error, json_ok, require_admin, require_user
from server.platform_catalog import ensure_avatar_media, scan_avatars

MAX_OPEN_ORDERS = 5
MAX_VIDEO = 120 * 1024 * 1024
MAX_IMAGE = 8 * 1024 * 1024
MAX_AUDIO = 20 * 1024 * 1024
VIDEO_EXT = {".mp4", ".webm", ".mov", ".mkv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".aac"}
OPEN_STATUSES = ("submitted", "accepted", "generating")


def _write_dummy_frame(path: Path) -> None:
    import numpy as np
    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), np.zeros((64, 64, 3), dtype=np.uint8))


def _uploads_root(app):
    return Path(app.get("uploads_dir") or os.path.join("data", "uploads", "orders"))


def _order_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "status": row["status"],
        "material_type": row["material_type"],
        "has_video": bool(row["video_path"]),
        "has_image": bool(row["image_path"]),
        "has_audio": bool(row["audio_path"]),
        "script_text": row["script_text"] or "",
        "reject_reason": row["reject_reason"] or "",
        "result_avatar_id": row["result_avatar_id"],
        "task_id": row["task_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


async def _save_upload(field, dest: Path, allowed, max_bytes):
    filename = field.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        raise ValueError(f"不支持的文件类型: {ext}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with open(dest, "wb") as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                f.close()
                dest.unlink(missing_ok=True)
                raise ValueError("文件过大")
            f.write(chunk)
    if size == 0:
        dest.unlink(missing_ok=True)
        raise ValueError("空文件")
    return str(dest)


async def create_my_order(request):
    denied = require_user(request)
    if denied:
        return denied
    user = request["user"]
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT COUNT(*) AS n FROM orders WHERE user_id = ? AND status IN (?, ?, ?)",
        (user["id"], *OPEN_STATUSES),
    ) as cur:
        n = (await cur.fetchone())["n"]
    if n >= MAX_OPEN_ORDERS:
        return json_error("进行中的订单过多，请等待处理完成")

    if not request.content_type or "multipart/form-data" not in request.content_type:
        return json_error("请使用 multipart 上传素材")

    now = time.time()
    cur = await db.execute(
        """
        INSERT INTO orders (user_id, status, material_type, script_text, created_at, updated_at)
        VALUES (?, 'submitted', 'video', '', ?, ?)
        """,
        (user["id"], now, now),
    )
    await db.commit()
    order_id = cur.lastrowid

    dest_dir = _uploads_root(request.app) / str(order_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    material_type = "video"
    script_text = ""
    video_path = image_path = audio_path = None
    try:
        reader = await request.multipart()
        while True:
            part = await reader.next()
            if part is None:
                break
            name = part.name
            if name == "material_type":
                material_type = (await part.text() or "video").strip()
            elif name == "script_text":
                script_text = await part.text() or ""
            elif name == "video" and part.filename:
                video_path = await _save_upload(
                    part, dest_dir / f"video{Path(part.filename).suffix.lower()}", VIDEO_EXT, MAX_VIDEO
                )
            elif name == "image" and part.filename:
                image_path = await _save_upload(
                    part, dest_dir / f"image{Path(part.filename).suffix.lower()}", IMAGE_EXT, MAX_IMAGE
                )
            elif name == "audio" and part.filename:
                audio_path = await _save_upload(
                    part, dest_dir / f"audio{Path(part.filename).suffix.lower()}", AUDIO_EXT, MAX_AUDIO
                )
    except ValueError as e:
        await db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        await db.commit()
        return json_error(str(e))

    if material_type not in ("video", "image_audio"):
        material_type = "video"
    if material_type == "video" and not video_path:
        await db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        await db.commit()
        return json_error("视频模式需要上传视频")
    if material_type == "image_audio" and (not image_path or not audio_path):
        await db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        await db.commit()
        return json_error("图+音频模式需要同时上传图片和音频")

    await db.execute(
        """
        UPDATE orders SET material_type = ?, video_path = ?, image_path = ?, audio_path = ?,
            script_text = ?, updated_at = ? WHERE id = ?
        """,
        (material_type, video_path, image_path, audio_path, script_text, time.time(), order_id),
    )
    await db.commit()
    async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cur:
        row = await cur.fetchone()
    return json_ok(_order_dict(row))


async def list_my_orders(request):
    denied = require_user(request)
    if denied:
        return denied
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
        (request["user"]["id"],),
    ) as cur:
        rows = await cur.fetchall()
    return json_ok({"orders": [_order_dict(r) for r in rows]})


async def admin_list_orders(request):
    denied = require_admin(request)
    if denied:
        return denied
    db = request.app["platform_db"]
    async with db.execute(
        """
        SELECT o.*, u.username AS username
        FROM orders o JOIN users u ON u.id = o.user_id
        ORDER BY o.id DESC
        """
    ) as cur:
        rows = await cur.fetchall()
    out = []
    for r in rows:
        item = _order_dict(r)
        item["username"] = r["username"]
        out.append(item)
    return json_ok({"orders": out})


async def _get_order(db, order_id):
    async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cur:
        return await cur.fetchone()


async def admin_accept_order(request):
    denied = require_admin(request)
    if denied:
        return denied
    order_id = int(request.match_info["order_id"])
    db = request.app["platform_db"]
    row = await _get_order(db, order_id)
    if not row:
        return json_error("订单不存在", status=404)
    if row["status"] != "submitted":
        return json_error("只能接单待处理订单")
    await db.execute(
        "UPDATE orders SET status = ?, admin_id = ?, updated_at = ? WHERE id = ?",
        ("accepted", request["user"]["id"], time.time(), order_id),
    )
    await db.commit()
    return json_ok()


async def admin_reject_order(request):
    denied = require_admin(request)
    if denied:
        return denied
    order_id = int(request.match_info["order_id"])
    try:
        body = await request.json()
    except Exception:
        body = {}
    reason = (body.get("reason") or "").strip()
    if not reason:
        return json_error("请填写驳回原因")
    db = request.app["platform_db"]
    row = await _get_order(db, order_id)
    if not row:
        return json_error("订单不存在", status=404)
    if row["status"] not in ("submitted", "generating", "accepted"):
        return json_error("当前状态不可驳回")
    await db.execute(
        "UPDATE orders SET status = ?, reject_reason = ?, admin_id = ?, updated_at = ? WHERE id = ?",
        ("rejected", reason, request["user"]["id"], time.time(), order_id),
    )
    await db.commit()
    return json_ok()


async def _fulfill_order(app, order_row, avatar_id):
    db = app["platform_db"]
    avatars_dir = app["avatars_dir"]
    await scan_avatars(db, avatars_dir)
    user_id = order_row["user_id"]
    try:
        await db.execute(
            "INSERT INTO subscriptions (user_id, avatar_id, is_published, created_at) VALUES (?, ?, 0, ?)",
            (user_id, avatar_id, time.time()),
        )
    except Exception:
        pass
    await db.execute(
        """
        UPDATE orders SET status = ?, result_avatar_id = ?, reject_reason = '', updated_at = ?
        WHERE id = ?
        """,
        ("completed", avatar_id, time.time(), order_row["id"]),
    )
    await db.commit()


async def admin_generate_order(request):
    denied = require_admin(request)
    if denied:
        return denied
    order_id = int(request.match_info["order_id"])
    try:
        body = await request.json()
    except Exception:
        body = {}
    avatar_id = (body.get("avatar_id") or "").strip()
    model_type = (body.get("model") or "wav2lip").strip()
    if not avatar_id:
        return json_error("缺少 avatar_id")
    db = request.app["platform_db"]
    row = await _get_order(db, order_id)
    if not row:
        return json_error("订单不存在", status=404)
    if row["status"] != "accepted":
        return json_error("只有已接单的订单可以生成")
    if not row["video_path"] or not os.path.isfile(row["video_path"]):
        return json_error("该订单没有视频，无法走现有生成管线")

    async with db.execute("SELECT avatar_id FROM avatars WHERE avatar_id = ?", (avatar_id,)) as cur:
        exists = await cur.fetchone()
    if exists:
        return json_error("avatar_id 已存在")

    if request.app.get("fake_avatar_tasks"):
        dest = Path(request.app["avatars_dir"]) / avatar_id
        dest.mkdir(parents=True, exist_ok=True)
        _write_dummy_frame(dest / "full_imgs" / "00000000.png")
        ensure_avatar_media(dest)
        await db.execute(
            "UPDATE orders SET status = ?, task_id = ?, admin_id = ?, updated_at = ? WHERE id = ?",
            ("generating", "fake", request["user"]["id"], time.time(), order_id),
        )
        await db.commit()
        row = await _get_order(db, order_id)
        await _fulfill_order(request.app, row, avatar_id)
        return json_ok({"task_id": "fake", "avatar_id": avatar_id})

    from server.task_manager import task_manager

    task_params = {
        "video_path": row["video_path"],
        "save_path": request.app["avatars_dir"],
        "img_size": int(body.get("img_size", 256)),
        "nosmooth": False,
        "bbox_shift": 0,
        "extra_margin": 10,
        "parsing_mode": "jaw",
        "version": "v15",
        "face_det_batch_size": 16,
        "pads": [0, 10, 0, 0],
        "order_id": order_id,
    }
    task_id = task_manager.add_task(model_type, avatar_id, task_params)
    await db.execute(
        "UPDATE orders SET status = ?, task_id = ?, admin_id = ?, updated_at = ? WHERE id = ?",
        ("generating", task_id, request["user"]["id"], time.time(), order_id),
    )
    await db.commit()
    return json_ok({"task_id": task_id})


async def handle_generation_task(app, task):
    db = app["platform_db"]
    if task.status == "completed":
        dest = Path(app["avatars_dir"]) / task.avatar_id
        ensure_avatar_media(dest)
        await scan_avatars(db, app["avatars_dir"])
    order_id = (task.params or {}).get("order_id")
    if not order_id:
        return
    row = await _get_order(db, order_id)
    if not row or row["status"] != "generating":
        return
    if task.status == "completed":
        await _fulfill_order(app, row, task.avatar_id)
    elif task.status == "failed":
        await db.execute(
            "UPDATE orders SET status = ?, reject_reason = ?, updated_at = ? WHERE id = ?",
            ("rejected", task.error_msg or "生成失败", time.time(), order_id),
        )
        await db.commit()


def setup_order_routes(app):
    app.router.add_post("/api/v1/me/orders", create_my_order)
    app.router.add_get("/api/v1/me/orders", list_my_orders)
    app.router.add_get("/api/v1/admin/orders", admin_list_orders)
    app.router.add_post("/api/v1/admin/orders/{order_id}/accept", admin_accept_order)
    app.router.add_post("/api/v1/admin/orders/{order_id}/reject", admin_reject_order)
    app.router.add_post("/api/v1/admin/orders/{order_id}/generate", admin_generate_order)
