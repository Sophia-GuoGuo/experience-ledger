#!/usr/bin/env python3
"""核算一段对话的"活跃交互工时"——只算真在干活的时间，等待与空档剔除。

用法：
  python3 calc_worktime.py <对话记录.jsonl> [...]
  python3 calc_worktime.py <对话记录.jsonl> --json
  python3 calc_worktime.py --dir <对话记录目录> --keyword 入驻

口径（与经验账本铁律一致）：
  - AI 产出时长：从用户消息到该轮最后一条 AI/工具事件的间隔，单轮封顶 --cap 分钟（默认 60）
  - 用户活跃：用户 15 分钟（--user-active）内的回复计入活跃
  - 等待剔除：超过 --gap 分钟（默认 30）的空档整体计为等待，不计入工时
  - 消息识别：过滤 <system-reminder>、<cb_summary>、<task-notification> 等非人工指令
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

NOISE_PREFIX = (
    "<system-reminder", "<cb_summary", "<conversation_history_summary",
    "<task-notification", "<user-prompt-submit-hook", "<command-name",
)

try:
    import re
    QUERY_RE = re.compile(r"<user_query>(.*?)</user_query>", re.S)
except Exception:  # pragma: no cover
    QUERY_RE = None


def parse_ts(v):
    """返回毫秒时间戳。兼容三种写法：毫秒整数、秒整数、ISO 字符串。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        v = float(v)
        return v if v > 1e11 else v * 1000
    if not isinstance(v, str):
        return None
    try:
        return dt.datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp() * 1000
    except ValueError:
        return None


def user_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            c.get("text", "") for c in content
            if isinstance(c, dict) and c.get("type") in ("input_text", "text")
        )
    return ""


def extract(path: pathlib.Path):
    """从多种可能的 jsonl 结构中尽力提取事件流。"""
    events = []
    for line in path.open(encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = d.get("type")
        if t != "message":
            if t in ("function_call", "function_call_result"):
                ts = parse_ts(d.get("timestamp"))
                if ts:
                    events.append((ts, "tool", ""))
            continue
        ts = parse_ts(d.get("timestamp"))
        if not ts:
            continue
        msg = d.get("message") if isinstance(d.get("message"), dict) else d
        role = msg.get("role")
        content = msg.get("content")
        if role == "user":
            s = user_text(content).strip()
            if not s:
                continue
            # 优先取被 <user_query> 包裹的真实指令（宿主会把系统提醒包在前面）
            if QUERY_RE:
                m = QUERY_RE.search(s)
                if m:
                    s = m.group(1).strip()
            elif s.startswith("<system-reminder"):
                tail = s.split("</system-reminder>")[-1].strip()
                if not tail or tail.startswith("<"):
                    continue
                s = tail
            if not s or s.startswith(NOISE_PREFIX) or s.startswith("<user_query>"):
                continue
            if s.startswith("<system-reminder"):
                tail = s.split("</system-reminder>")[-1].strip()
                if not tail or tail.startswith("<"):
                    continue
                s = tail
            events.append((ts, "user", s[:60].replace("\n", " ")))
        elif role == "assistant":
            events.append((ts, "ai", ""))
    events.sort(key=lambda x: x[0])
    return events


def analyze(events, gap_min, user_active_min, cap_min):
    gap = gap_min * 60 * 1000
    user_active = user_active_min * 60 * 1000
    cap = cap_min * 60 * 1000

    turns, cur = [], None
    for ts, kind, txt in events:
        if kind == "user":
            if cur:
                turns.append(cur)
            cur = {"t0": ts, "last": ts, "txt": txt}
        elif cur is not None:
            cur["last"] = max(cur["last"], ts)
    if cur:
        turns.append(cur)
    if not turns:
        return None

    sessions = []
    for t in turns:
        if sessions and t["t0"] - sessions[-1]["last"] < gap:
            s = sessions[-1]
            s["last"] = max(s["last"], t["last"])
            s["turns"].append(t)
        else:
            sessions.append({"t0": t["t0"], "last": t["last"], "turns": [t]})

    total_ai = total_user = total_wait = 0.0
    for s in sessions:
        ai = u = 0.0
        for i, t in enumerate(s["turns"]):
            ai += min(t["last"] - t["t0"], cap)
            if i + 1 < len(s["turns"]):
                g = s["turns"][i + 1]["t0"] - t["last"]
                if g <= user_active:
                    u += g
                else:
                    total_wait += g
        total_ai += ai
        total_user += u
    return {
        "first": events[0][0], "last": events[-1][0],
        "turns": len(turns), "sessions": len(sessions),
        "ai_ms": total_ai, "user_ms": total_user, "wait_ms": total_wait,
        "first_text": turns[0]["txt"], "last_text": turns[-1]["txt"],
        "session_list": sessions,
    }


def fmt(ms):
    return dt.datetime.fromtimestamp(ms / 1000).strftime("%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser(description="核算对话的活跃交互工时（等待时间不计）")
    ap.add_argument("files", nargs="*", help="对话记录 .jsonl 文件")
    ap.add_argument("--dir", help="对话记录目录，与 --keyword 配合使用")
    ap.add_argument("--keyword", default="", help="按关键词筛选对话记录文件内容")
    ap.add_argument("--gap", type=float, default=30, help="会话空档阈值（分钟），默认 30")
    ap.add_argument("--user-active", type=float, default=15, help="用户活跃回复阈值（分钟），默认 15")
    ap.add_argument("--cap", type=float, default=60, help="单轮 AI 产出封顶（分钟），默认 60")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    files = [pathlib.Path(f) for f in args.files]
    if args.dir:
        d = pathlib.Path(args.dir).expanduser()
        for f in sorted(d.rglob("*.jsonl")):
            if not args.keyword or args.keyword in f.read_text(
                encoding="utf-8", errors="ignore"
            )[:200000]:
                files.append(f)
    files = [f for f in files if f.exists()]
    if not files:
        sys.exit("未找到可核算的对话记录文件（.jsonl）")

    results = []
    for f in files:
        ev = extract(f)
        r = analyze(ev, args.gap, args.user_active, args.cap)
        if r:
            r["file"] = str(f)
            results.append(r)

    if not results:
        print("未解析出可核算的交互（对话记录可能为空或格式不符）")
        return

    if args.json:
        for r in results:
            r.pop("session_list")
            print(json.dumps(r, ensure_ascii=False))
        return

    print("| 对话记录 | 轮次 | 会话段 | AI产出 | 你在线 | 活跃合计 | 剔除等待 |")
    print("|---|---|---|---|---|---|---|")
    for r in sorted(results, key=lambda x: -(x["ai_ms"] + x["user_ms"])):
        active = r["ai_ms"] + r["user_ms"]
        print(
            f"| {pathlib.Path(r['file']).name[:28]} | {r['turns']} | {r['sessions']} | "
            f"{r['ai_ms']/3600000:.1f}h | {r['user_ms']/3600000:.1f}h | "
            f"**{active/3600000:.1f}h** | {r['wait_ms']/3600000:.1f}h |"
        )

    print()
    for r in sorted(results, key=lambda x: -(x["ai_ms"] + x["user_ms"]))[:3]:
        active = (r["ai_ms"] + r["user_ms"]) / 3600000
        print(f"— {pathlib.Path(r['file']).name}")
        print(f"  跨度 {fmt(r['first'])} → {fmt(r['last'])}，{r['turns']} 轮 / {r['sessions']} 段")
        print(f"  活跃合计 {active:.1f} 小时（约 {active/8:.2f} 人天，按 8h/人天）")
        print(f"  首轮：{r['first_text']}")
        print(f"  末轮：{r['last_text']}")
        print()

    print("口径：AI 产出（单轮封顶 %g 分钟）+ 你 %g 分钟内的回复计入活跃，"
          "超过 %g 分钟的空档整体剔除为等待。" % (args.cap, args.user_active, args.gap))


if __name__ == "__main__":
    main()
