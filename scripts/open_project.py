#!/usr/bin/env python3
"""开工登记：一句话建项目行 + 工时账行，把"开工即记工时"变成一条命令。

用法：
  python3 open_project.py --dir ~/WorkBuddy/经验账本 --name "OPC 入驻者管理系统" \
      --category "一、工作服务" --module "准入流程系统"

行为：
  1. 在 项目登记表.md 的项目清单追加一行（开工日=今天，工时状态=进行中）
  2. 若存在 交付台账.md，在工时账追加一行（实际人天留空，等 calc_worktime.py 回填）
  3. 打印收尾指令：结项时怎么算工时、怎么写能力卡片

设计原因：铁律③「开工即记工时」之所以经常断，是因为它依赖记性。
把开工登记变成命令 + 空行已在账本里，就不会出现"结项时永远待补"。
"""
import argparse
import datetime as dt
import pathlib
import re
import sys


def append_row(md_path: pathlib.Path, section_hint: str, row: str) -> bool:
    """在指定小节的表格末尾追加一行。找不到小节则返回 False。"""
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if section_hint in ln:
            start = i
            break
    if start is None:
        return False
    # 从小节标题往下找表格的最后一行
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("##"):
            end = j
            break
    insert_at = end
    for j in range(end - 1, start, -1):
        if lines[j].strip():
            insert_at = j + 1
            break
    lines.insert(insert_at, row)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(description="开工登记：建项目行 + 工时账行")
    ap.add_argument("--dir", required=True, help="账本目录")
    ap.add_argument("--name", required=True, help="项目名")
    ap.add_argument("--category", default="", help="所属类目（照登记表写法，如：一、工作服务）")
    ap.add_argument("--module", default="", help="模块名（对齐报价系统模块名，工时校准用）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将写入的内容")
    args = ap.parse_args()

    d = pathlib.Path(args.dir).expanduser()
    reg = d / "项目登记表.md"
    if not reg.exists():
        sys.exit(f"未找到 {reg}，请先运行 new_ledger.py 建账本")

    today = dt.date.today()
    md = today.strftime("%m-%d")
    proj_row = (f"| {args.name} | {args.category or '待归类'} | 进行中 | "
                f"{today.isoformat()} | 工时进行中 | （待写） |")
    work_row = (f"| {md} | **{args.name}** | {args.module or '待填'} | 进行中 | "
                f"开工登记 {today.isoformat()} |")

    if args.dry_run:
        print("将写入 项目登记表.md：\n  " + proj_row)
        dv = d / "交付台账.md"
        if dv.exists():
            print("将写入 交付台账.md：\n  " + work_row)
        return

    ok = append_row(reg, "## 项目清单", proj_row)
    print(("✓ 已登记项目行：" if ok else "⚠ 未找到项目清单小节，请手动补：") + f" {args.name}")

    dv = d / "交付台账.md"
    if dv.exists():
        ok2 = append_row(dv, "## 三、工时账", work_row)
        print(("✓ 已建工时账行（结项时回填人天）" if ok2
               else "⚠ 未找到工时账小节，请手动补一行"))
    else:
        print("· 无交付台账.md，跳过工时账（个人复盘模式无需工时账）")

    print("\n接下来：")
    print(f"  · 把本次对话记录路径记下来（宿主对话目录下的 .jsonl），结项时核算：")
    print(f"      python3 scripts/calc_worktime.py <对话记录.jsonl>")
    print(f"  · 项目期间随时可回填工时，不必等结项")
    print(f"  · 记得同步刷 {d / '账本.html'}（铁律④：md 与 HTML 必须一致）")


if __name__ == "__main__":
    main()
