###############################################################################
#  Scan avatar directories and resolve cover / preview files
###############################################################################

import os
import shutil
import subprocess
import time
from pathlib import Path

COVER_NAMES = ("cover.jpg", "cover.jpeg", "cover.png", "cover.webp")
PREVIEW_NAMES = ("preview.mp4",)
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
PREVIEW_FPS = 25
PREVIEW_SECONDS = 5


def _first_image(directory: Path):
    if not directory.is_dir():
        return None
    for p in sorted(directory.iterdir()):
        if p.suffix.lower() in IMAGE_EXT:
            return str(p)
    return None


def _list_full_imgs(root: Path):
    frames_dir = root / "full_imgs"
    if not frames_dir.is_dir():
        return []
    return sorted(p for p in frames_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXT)


def _has_cover(root: Path) -> bool:
    return any((root / name).is_file() for name in COVER_NAMES)


def _write_cover(dest: Path, source: Path) -> None:
    try:
        import cv2
        img = cv2.imread(str(source))
        if img is not None:
            cv2.imwrite(str(dest), img)
            if dest.is_file():
                return
    except Exception:
        pass
    shutil.copyfile(source, dest)


def _ffmpeg_preview(dest: Path, frames, ffmpeg: str) -> bool:
    list_file = dest.parent / ".preview_concat.txt"
    duration = 1.0 / PREVIEW_FPS
    try:
        with list_file.open("w", encoding="utf-8") as fh:
            for p in frames:
                fh.write(f"file '{p.resolve().as_posix()}'\n")
                fh.write(f"duration {duration}\n")
            fh.write(f"file '{frames[-1].resolve().as_posix()}'\n")
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-an",
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(dest),
            ],
            check=False,
        )
        return proc.returncode == 0 and dest.is_file() and dest.stat().st_size > 0
    except Exception:
        return False
    finally:
        if list_file.exists():
            list_file.unlink()


def _cv2_preview(dest: Path, frames) -> bool:
    try:
        import cv2
    except Exception:
        return False
    imgs = []
    size = None
    for p in frames:
        img = cv2.imread(str(p))
        if img is None:
            continue
        h, w = img.shape[:2]
        if size is None:
            size = (w, h)
        elif (w, h) != size:
            img = cv2.resize(img, size)
        imgs.append(img)
    if not imgs:
        return False
    writer = cv2.VideoWriter(str(dest), cv2.VideoWriter_fourcc(*"mp4v"), PREVIEW_FPS, size)
    if not writer.isOpened():
        return False
    for img in imgs:
        writer.write(img)
    writer.release()
    return dest.is_file() and dest.stat().st_size > 0


def ensure_avatar_media(avatar_root) -> None:
    root = Path(avatar_root)
    if not root.is_dir():
        return
    frames = _list_full_imgs(root)
    if not frames:
        return
    if not _has_cover(root):
        _write_cover(root / "cover.jpg", frames[0])
    preview = root / "preview.mp4"
    if preview.is_file():
        return
    limited = frames[: PREVIEW_FPS * PREVIEW_SECONDS]
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg and _ffmpeg_preview(preview, limited, ffmpeg):
        return
    _cv2_preview(preview, limited)


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
        ensure_avatar_media(child)
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
