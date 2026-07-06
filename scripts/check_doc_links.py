"""Check markdown links in docs/ resolve to existing files."""
from __future__ import annotations
import re, sys
from pathlib import Path


def _is_internal(link: str) -> bool:
    return not link.startswith(("http://", "https://", "mailto:", "#", "ftp://"))


def check_links(docs_dir: str = "docs") -> dict:
    root = Path(docs_dir)
    if not root.exists():
        return {"error": f"Not found: {docs_dir}"}
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken = []
    checked = 0
    for md in sorted(root.rglob("*.md")):
        for text, link in pattern.findall(md.read_text(encoding="utf-8", errors="replace")):
            if not _is_internal(link):
                continue
            target = link.split("#")[0]
            if not target:
                continue
            rp = (md.parent / target).resolve()
            if not rp.exists():
                broken.append({"file": str(md.relative_to(root.parent)), "link": link, "text": text})
        checked += 1
    return {"checked": checked, "broken": broken, "count": len(broken)}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-errors", type=int, default=0,
                        help="Exit 3 only if broken count exceeds this")
    parser.add_argument("--warn-only", action="store_true",
                        help="Print broken links but always exit 0")
    args = parser.parse_args()

    result = check_links()
    if "error" in result:
        print(result["error"], file=sys.stderr); return 2
    print(f"Files: {result['checked']}, Broken: {result['count']}")
    for b in result["broken"]:
        print(f"  ❌ {b['file']}: '{b['text']}' -> {b['link']}")
    if args.warn_only:
        return 0
    if result["count"] > args.max_errors:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
