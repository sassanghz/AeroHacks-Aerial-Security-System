from pathlib import Path

def latest_image(folder: str) -> str | None:
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
    files = [
        p for p in Path(folder).iterdir()
        if p.is_file() and p.suffix.lower() in image_exts
    ]

    if not files:
        return None

    latest = max(files, key=lambda p: p.stat().st_mtime)
    return str(latest)