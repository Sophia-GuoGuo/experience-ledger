#!/usr/bin/env python3
"""扫描指定范围内的增量文件变动，按工作空间分组，输出候选入账清单。

用法：
  python3 scan_changes.py --root ~/WorkBuddy --since-hours 24
  python3 scan_changes.py --root ~/WorkBuddy --since-hours 720 --md          # 附带对话记录变动
  python3 scan_changes.py --root ~/WorkBuddy --since-hours 24 --json       # 机器可读输出

设计约束：
- 只读，不修改任何文件
- 只报告变动，**不做归类判断、不做质量评价**（定性由账本主人确认）
- 超出 --root 的路径一律不读取（隐私边界）
"""
import argparse
import datetime as dt
import json
import os
import pathlib

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".DS_Store",
    "dist", "build", ".next", ".cache", ".idea", ".vscode", "site-packages",
}
DOC_EXT = {
    ".md", ".txt", ".html", ".htm", ".docx", ".xlsx", ".csv", ".pptx",
    ".py", ".js", ".ts", ".json", ".jsonl", ".yaml", ".yml",
}


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def scan(root: pathlib.Path, since: float):
    groups: dict[str, list] = {}
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git")]
        for fn in filenames:
            if fn in SKIP_DIRS or fn.startswith("."):
                continue
            fp = pathlib.Path(dirpath) / fn
            try:
                st = fp.stat()
            except OSError:
                continue
            if st.st_mtime < since:
                continue
            if fp.suffix.lower() not in DOC_EXT:
                continue
            rel = fp.relative_to(root)
            group = str(rel.parts[0]) if len(rel.parts) > 1 else "（根目录）"
            groups.setdefault(group, []).append(
                {
                    "path": str(rel),
                    "mtime": dt.datetime.fromtimestamp(st.st_mtime).strftime("%m-%d %H:%M"),
                    "size": human(st.st_size),
                }
            )
            total += 1
    return groups, total


def main():
    ap = argparse.ArgumentParser(description="扫描增量文件变动，生成候选入账清单")
    ap.add_argument("--root", required=True, help="扫描根目录（隐私边界，超出此路径不读取）")
    ap.add_argument("--since-hours", type=float, default=24, help="回看小时数，默认 24")
    ap.add_argument("--top", type=int, default=12, help="每组最多列出文件数")
    ap.add_argument("--conversations", default="", help="对话记录目录（可选），用于发现新增对话")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    root = pathlib.Path(args.root).expanduser()
    if not root.exists():
        raise SystemExit(f"目录不存在：{root}")

    since = dt.datetime.now().timestamp() - args.since_hours * 3600
    groups, total = scan(root, since)

    convs = []
    if args.conversations:
        cdir = pathlib.Path(args.conversations).expanduser()
        if cdir.exists():
            for f in sorted(cdir.rglob("*.jsonl")):
                try:
                    if f.stat().st_mtime >= since:
                        convs.append(
                            {
                                "path": str(f),
                                "mtime": dt.datetime.fromtimestamp(
                                    f.stat().st_mtime
                                ).strftime("%m-%d %H:%M"),
                                "size": human(f.stat().st_size),
                            }
                        )
                except OSError:
                    continue

    if args.json:
        print(
            json.dumps(
                {"root": str(root), "since_hours": args.since_hours,
                 "total": total, "groups": groups, "conversations": convs},
                ensure_ascii=False, indent=2,
            )
        )
        return

    print(f"# 增量扫描结果")
    print(f"根目录：{root}")
    print(f"时间窗：过去 {args.since_hours:g} 小时")
    print(f"变动文件：{total} 个，覆盖 {len(groups)} 个分组")
    if convs:
        print(f"新增对话记录：{len(convs)} 个")
    print()

    if not groups and not convs:
        print("本时间窗内无变动。→ 账本本期待记「本期无新增」，不要凑数写内容。")
        return

    for g, files in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"## {g}（{len(files)}）")
        for f in sorted(files, key=lambda x: x["mtime"], reverse=True)[: args.top]:
            print(f"  {f['mtime']}  {f['path']}  ({f['size']})")
        if len(files) > args.top:
            print(f"  …… 另有 {len(files) - args.top} 个")
        print()

    if convs:
        print("## 新增对话记录")
        for c in convs[: args.top * 3]:
            print(f"  {c['mtime']}  {c['path']}  ({c['size']})")
        print()
    print("提示：以上仅为变动事实。未归类的产出列入「待归类」交账主定位，")
    print("      不得强行归类；判断性标签（卡点/教训）需主人确认后再打。")


if __name__ == "__main__":
    main()
