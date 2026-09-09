###############################################################################
#  Scan avatar directories and resolve cover / preview files
###############################################################################

import os
import time
from pathlib import Path

COVER_NAMES = ("cover.jpg", "cover.jpeg", "cover.png", "cover.webp")
PREVIEW_NAMES = ("preview.mp4",)


def _first_image(directory: Path):
    if not directory.is_dir():
        return None
    for p in sorted(directory.iterdir()):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            return str(p)
    return None


def resolve_media(avatars_dir: str, avatar_id: str):
    root = Path(avatars_dir) / avatar_id
    cover = None
    preview = None
    if root.is_dir():
        for name in COVER_NAMES:
            candidate = root / name
            if candidate.is_file():
                cover = str(candidate)
                break
        if cover is None:
            cover = _first_image(root / "full_imgs") or _first_image(root)
        for name in PREVIEW_NAMES:
            candidate = root / name
            if candidate.is_file():
                preview = str(candidate)
                break
    status = "ready" if root.is_dir() else "missing"
    return cover, preview, status


async def scan_avatars(db, avatars_dir: str):
    root = Path(avatars_dir)
    if not root.is_dir():
        return 0
    now = time.time()
    seen = []
    count = 0
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        avatar_id = child.name
        if avatar_id.startswith("."):
            continue
        seen.append(avatar_id)
        cover, preview, status = resolve_media(avatars_dir, avatar_id)
        async with db.execute("SELECT avatar_id FROM avatars WHERE avatar_id = ?", (avatar_id,)) as cur:
            exists = await cur.fetchone()
        if exists:
            await db.execute(
                "UPDATE avatars SET cover_path = ?, preview_path = ?, status = ? WHERE avatar_id = ?",
                (cover, preview, status, avatar_id),
            )
        else:
            await db.execute(
                """
                INSERT INTO avatars (avatar_id, name, cover_path, preview_path, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (avatar_id, avatar_id, cover, preview, status, now),
            )
            count += 1
    async with db.execute("SELECT avatar_id FROM avatars") as cur:
        rows = await cur.fetchall()
    known = {r["avatar_id"] for r in rows}
    for avatar_id in known - set(seen):
        await db.execute("UPDATE avatars SET status = ? WHERE avatar_id = ?", ("missing", avatar_id))
    await db.commit()
    return count


def avatar_public_dict(row, request):
    avatar_id = row["avatar_id"]
    cover_url = None
    preview_url = None
    if row["cover_path"] and os.path.isfile(row["cover_path"]):
        cover_url = f"/api/v1/media/avatars/{avatar_id}/cover"
    if row["preview_path"] and os.path.isfile(row["preview_path"]):
        preview_url = f"/api/v1/media/avatars/{avatar_id}/preview"
    keys = set(row.keys())
    return {
        "avatar_id": avatar_id,
        "name": row["name"],
        "status": row["status"],
        "cover_url": cover_url,
        "preview_url": preview_url,
        "is_published": bool(row["is_published"]) if "is_published" in keys else False,
    }
