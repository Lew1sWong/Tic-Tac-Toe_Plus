"""Build the playable page.

Usage:
  python3 src/build.py              writes index.html (standalone, works on GitHub Pages)
  python3 src/build.py --body OUT   writes only the page body to OUT (no <html>/<head> shell)
"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent

SHELL_HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""


def body() -> str:
    page = (SRC / "page.html").read_text(encoding="utf-8")
    engine = (SRC / "engine.js").read_text(encoding="utf-8")
    assert "/*__ENGINE__*/" in page
    return page.replace("/*__ENGINE__*/", engine)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--body":
        Path(sys.argv[2]).write_text(body(), encoding="utf-8")
        print("wrote", sys.argv[2])
    else:
        out = ROOT / "index.html"
        out.write_text(SHELL_HEAD + body() + "\n</html>\n", encoding="utf-8")
        print("wrote", out)
