#!/usr/bin/env python3
"""生成经验账本骨架（结构与郭姗账本 1:1），并支持换肤。

用法：
  # 建账本（九板块结构原样生成）
  python3 new_ledger.py --dir ~/WorkBuddy/经验账本 --title "郭姗·经验账本" --owner "郭姗" \
      --category "一、工作服务" --category "二、个人经营" --skin handdrawn --delivery

  # 换肤：只替换内联 CSS，数据与结构一字不动
  python3 new_ledger.py --dir ~/WorkBuddy/经验账本 --switch-skin minimal

结构说明：板块顺序固定为
  头部 → 统计条 → 周记录卡 → 分项目动作时间轴 → 交付工具箱 → 待你拍板 → 风险预警
  → AI建议·只基于事实 → 待归类·等你定位 → 页脚
"""
import argparse
import datetime as dt
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKINS_DIR = HERE.parent / "assets" / "skins"
SKINS = ["handdrawn", "minimal", "business", "dopamine", "tech"]

# 蜡笔图标：填色走皮肤变量，描边走主文字色
MK_PATH = "M3 14 L13 4 L15 6 L5 16 L2 17 Z"


def mk(color_var: str) -> str:
    return (
        f'<svg class="mk" width="18" height="18" viewBox="0 0 18 18">'
        f'<path d="{MK_PATH}" fill="var({color_var})" stroke="var(--ink)" '
        f'stroke-width="1.2" stroke-linejoin="round"/></svg>'
    )


WAVE = (
    '<svg class="wave" width="180" height="10" viewBox="0 0 180 10">'
    '<path d="M2 6 C 12 1, 22 9, 32 5 S 52 2, 62 6 S 82 9, 92 4 S 112 2, 122 6 '
    'S 142 9, 152 4 S 172 2, 178 6" fill="none" stroke="var(--accent)" '
    'stroke-width="3" stroke-linecap="round"/></svg>'
)

REGISTER_TPL = """# {title} · 项目登记表

> 本文件是项目状态的**唯一事实源**；`账本.html` 是阅读视图，两者必须一致。
> 分类框架由{owner}定义，AI 无权增删改类目。

## 分类框架（由{owner}定义，AI 不得擅改）

{categories}

## 元规则

- 状态只认本表，不得根据文件变动自行推断「已完成/已烂尾」
- 阻塞 ≠ 烂尾；状态变更需{owner}确认
- 新增类目须{owner}确认，AI 只提议
- 判断性标签（卡点/教训→规则）需{owner}确认后才打

## 项目清单（含工时起点，工时账据此核算）

| 项目 | 所属类目 | 状态 | 开工日 | 工时状态 | 思路主线 |
|---|---|---|---|---|---|
| | | 待确认 | | 未记 | |

## 待归类（等{owner}定位）

| 产出 | 发现日期 | 疑似归属 | 为什么无法归类 | 状态 |
|---|---|---|---|---|
| | | | | 待定位 |

## 扫描范围（隐私边界）

- 允许扫描：{scan_scope}
- 未列入的路径一律不读取
- 发布到公网为**可选项**，默认关闭，需{owner}显式开启
{created}
"""

DELIVERY_TPL = """# {title} · 交付台账

> 交付层（SOW / 能力卡片 / 工时账 / 报价校准）。个人复盘用途可关闭本层。
> 阅读视图见 `账本.html` 的「交付工具箱」板块。

## 四条铁律

1. **开工前有 SOW**：独立订单开工前先填范围与验收标准（含阶段0 思路对齐）
2. **完工当天写能力卡片**：不攒到月底回忆
3. **开工即记工时**：开工当天建工时账行，用 `calc_worktime.py` 核算，不靠回忆
4. **md 与 HTML 同步**：改数据源必须同一次刷阅读视图

## 一、SOW 模板（每个独立订单一份）

- **阶段0 思路对齐**：客户想要什么（原始表述）／信息盲区清单（你没想到但必须定的点）／明确不做什么
- **交付范围**：包含（可验收功能点逐条列）＋ 不包含（防无限加需求）
- **里程碑与验收标准**：阶段0 → 原型确认 → 开发完成 → 验收上线，每阶段写"可勾选、可测试"
- **修改轮次**：含 N 轮，超范围走变更计费
- **双方责任**：数据主权归客户；应用层安全（密码加密、越权防护）由开发方负责
- **报价与付款**：模块×人天×费率；签约 50% + 验收 50%
- **运维与售后**：免费缺陷修复期；运维年费单列（备份＋监控告警＋安全补丁）

## 二、能力卡片库（完工当天写）

字段：触发场景／方案骨架／数据模型／核心难点（踩的坑）／可复用资产／**实际工时**／收费参考与接受度／复用评级（A 整套复用 · B 骨架复用 · C 仅经验参考）

| # | 项目 | 类型 | 复用评级 | 卡片状态 |
|---|---|---|---|---|
| 1 | | | 待评 | 待写 |

## 三、工时账（报价校准数据源）

口径：AI 产出时长（单轮封顶 60 分钟）+ 用户 15 分钟内回复计入活跃，超过 30 分钟空档整体剔除为等待。用 `calc_worktime.py` 跑对话记录生成。

| 日期 | 项目 | 模块 | 实际人天 | 备注/坑 |
|---|---|---|---|---|
| | | | | |

**校准规则**：同一模块累计 3 单以上真实工时后，用中位数替换报价系统估值并注释校准季度。

## 四、待研究清单
- [ ]
{created}
"""

HTML_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<div class="wrap">

  <div class="header card wob1">
    <h1>{title} <span class="paw">✎</span></h1>
    {wave}
    <p>时间轴三层记录：事实（做了什么）→ 思路（当时怎么想）→ 变化（什么触发了转向）｜ 分类框架：{owner}定义，AI 无权增删 ｜ 数据源：项目登记表.md ｜ 每日09:00自动出账（只处理过去24小时增量）</p>
  </div>

  <div class="stats">
    <div class="stat card wob2"><div class="num">0</div><div class="lab">登记项目</div></div>
    <div class="stat card wob3"><div class="num">0</div><div class="lab">待补录</div></div>
    <div class="stat card wob1"><div class="num">0</div><div class="lab">待你拍板</div></div>
    <div class="stat card wob2"><div class="num">0</div><div class="lab">风险预警</div></div>
  </div>

  <h2>{mk1}<span class="uline">周记录卡</span></h2>
  <details open class="card wob2">
    <summary><div class="weekhead"><span class="wt">{week}</span><span class="wr">进行中 · 已记 0 天</span></div></summary>
    <div class="weekbody">
      <p class="hint">每日出账在此累计：当天新增条目、决策数、转向数、能力卡片产出。周日补发全周汇总与上周对比。</p>
    </div>
  </details>

  <h2>{mk2}<span class="uline">分项目动作时间轴（含思路变动）</span></h2>

  <div class="groupt">一、工作服务</div>
  <div class="subt">1）{cat1}</div>
  <div class="dlist">
    <details class="card wob1">
      <summary><span class="pname">（项目名）</span><span style="display:flex;gap:8px;align-items:center;"><span class="latest">--</span><span class="badge b-todo">待补录</span></span></summary>
      <div class="body">
        <div class="mainline"><b>思路主线：</b>（一句话概括本项目思路演进主题，随演进而更新）</div>
        <div class="timeline">
          <div class="tl-item"><div class="tl-meta"><span class="tl-date">MM-DD</span><span class="tag g-adv">推进</span></div><div class="tl-txt">事实层：做了什么（一句话）</div><div class="tl-why"><b>想：</b>思路层：当时怎么想、依据什么判断</div><div class="tl-turn"><b>变：</b>变化层：什么触发了转向（仅思路变动时写）</div></div>
        </div>
        <div class="next"><b>下一步：</b>该项目的下一步动作（行动出口挂在项目卡内，不设全局任务板）</div>
      </div>
    </details>
  </div>
  <div class="subt">2）{cat2}</div>
  <div class="subt">3）{cat3}</div>

  <div class="groupt">二、个人经营</div>
  <div class="subt">1）小工具</div>
  <div class="subt">2）小程序</div>
  <div class="subt">3）品牌与内容</div>

  <h2>{mk3}<span class="uline">交付工具箱</span></h2>
  <p class="hint">数据源：交付台账.md（机器读写）｜ 本板块为阅读视图 ｜ 工时账校准报价引擎的人天基准</p>
  <div class="iron"><b>四条铁律：</b>① 每个订单开工前必须填一份 SOW（先过阶段0 思路对齐）② 每完成一个项目当天写一张能力卡片 ③ <b>开工即记工时</b>——开工当天建行随时回填，不等结项靠回忆 ④ 结项后用工时数据校准报价</div>

  <details open class="card wob1">
    <summary><span class="pname">① SOW 工作说明书模板（每单必配）</span><span style="display:flex;gap:8px;align-items:center;"><span class="badge b-dep">开工前置</span></span></summary>
    <div class="body" style="padding-top:10px;">
      <div class="box card wob3" style="padding:12px 14px;">
        <ol style="padding-left:20px;margin-top:8px;">
          <li style="font-size:13px;margin-bottom:8px;"><b>项目概述</b>：3 句话说清——客户什么问题 → 交付什么 → 上线后谁用</li>
          <li style="font-size:13px;margin-bottom:8px;"><b>交付范围</b>：包含（可验收功能点逐条）＋ 不包含（明确不做什么，防无限加需求）</li>
          <li style="font-size:13px;margin-bottom:8px;"><b>里程碑与验收标准</b>：阶段0 思路对齐（做什么／不做什么／信息盲区清单，确认后锁版）→ 原型确认 → 开发完成 → 验收上线</li>
          <li style="font-size:13px;margin-bottom:8px;"><b>双方责任分工</b>：数据主权归客户；应用层安全由开发方负责</li>
          <li style="font-size:13px;margin-bottom:8px;"><b>报价与付款</b>：模块×人天×费率；签约 50% + 验收 50%</li>
          <li style="font-size:13px;margin-bottom:8px;"><b>运维与售后</b>：免费缺陷修复期；运维年费单列（备份＋监控＋补丁）</li>
          <li style="font-size:13px;"><b>变更管理</b>：超范围需求，书面确认工时费用后再动手</li>
        </ol>
      </div>
    </div>
  </details>

  <details class="card wob2">
    <summary><span class="pname">② 能力卡片库（完工当天写）</span><span style="display:flex;gap:8px;align-items:center;"><span class="badge b-ok">0 已写</span></span></summary>
    <div class="body" style="padding-top:10px;">
      <div class="box card wob3" style="padding:12px 14px;">
        <b style="font-size:13.5px;">卡片模板字段</b>
        <p style="font-size:12.5px;color:var(--ink-2);margin-top:6px;">触发场景 ｜ 方案骨架 ｜ 数据模型 ｜ 核心难点（踩的坑）｜ 可复用资产 ｜ <b>实际工时</b> ｜ 收费参考与客户接受度 ｜ 复用评级（A 整套复用 / B 骨架复用 / C 仅经验参考）</p>
      </div>
      <div class="box card wob1" style="padding:12px 14px;">
        <b style="font-size:13.5px;">卡片索引</b>
        <table class="tb" style="margin-top:8px;">
          <tr><th>项目</th><th>类型</th><th>状态</th></tr>
        </table>
      </div>
    </div>
  </details>

  <details class="card wob3">
    <summary><span class="pname">③ 工时账（报价校准数据源）</span><span style="display:flex;gap:8px;align-items:center;"><span class="badge b-ok">开工即建行</span></span></summary>
    <div class="body" style="padding-top:10px;">
      <div class="box card wob1" style="padding:12px 14px;">
        <table class="tb">
          <tr><th>日期</th><th>项目</th><th>模块</th><th>实际人天</th><th>备注/坑</th></tr>
        </table>
        <p style="font-size:12.5px;color:var(--warn-ink);"><b>核算口径：</b>只计活跃交互——AI 产出 + 用户 ≤15 分钟内的回复/思考；&gt;30 分钟空档按等待剔除，多项目并行不互相计费。工具：<b>scripts/calc_worktime.py</b>，任何对话记录 jsonl 丢给它就出工时。</p>
      </div>
    </div>
  </details>

  <details class="card wob1">
    <summary><span class="pname">④ 报价公式与"报不出价"自查顺序</span><span style="display:flex;gap:8px;align-items:center;"><span class="badge b-iter">报价联动</span></span></summary>
    <div class="body" style="padding-top:10px;">
      <div class="box card wob2" style="padding:12px 14px;">
        <div class="code">报价 = Σ(模块人天 × 费率) × 复杂度系数
      ＋ 部署上线费（首次）
      ＋ 运维年费（建议开发费的 15%~25%/年）

复用评级 A 的项目：人天按基准 × 0.5 报（有模板，速度翻倍）
客户自备服务器/账号：部署费下调；代购代维：上调并写入 SOW 责任条款</div>
        <p style="font-size:12.5px;"><b>报不出价时的检查顺序：</b>① 模块拆细了吗 → ② 有没有同类能力卡片 → ③ 工时账有没有历史数据 → 三个都没有：按基准表报 + 注明"估算，原型确认后锁定"</p>
      </div>
    </div>
  </details>

  <details class="card wob2">
    <summary><span class="pname">⑤ 更新发布 SOP（客户服务器升级，固定 7 步）</span><span style="display:flex;gap:8px;align-items:center;"><span class="badge b-run">已固化</span></span></summary>
    <div class="body" style="padding-top:10px;">
      <div class="box card wob1" style="padding:12px 14px;">
        <div class="code"><b># 0</b> 确定测试载体（测试账号／测试申请者／临时库）并写明清理方式；生产数据只读不写
<b># 1</b> 本地打版本包，命名带版本号：app-v1.4.5.zip
<b># 2</b> 上传：scp 包 user@服务器:/home/user/releases/
<b># 3</b> 备份旧版（永远先备份再动手）：
      cp -r /home/user/app /home/user/backup/app-$(date +%m%d-%H%M)
<b># 4</b> 解压替换（排除数据库与用户上传目录，防止覆盖客户数据！）：
      unzip -o 包 -d app_new && rsync -a --delete app_new/ app/ \\
        --exclude '*.db' --exclude 'uploads/'
<b># 5</b> 装依赖：pip install -r requirements.txt
<b># 6</b> 重启：sudo systemctl restart 服务名
<b># 7</b> 健康检查不过关 → 删新目录、mv 备份回来、再重启</div>
        <p style="font-size:12.5px;"><b>三条纪律：</b>① 先确定测试载体再动手（比"备份旧版"更靠前：备份解决"改坏了能还原"，解决不了"误改了真数据"）② 更新选客户不用系统的时间段 ③ 每次更新后在台账记一行（日期/版本/变更/有无事故）</p>
      </div>
    </div>
  </details>

  <details class="card wob3">
    <summary><span class="pname">⑥ 待研究清单</summary><span style="display:flex;gap:8px;align-items:center;"><span class="badge b-todo">待启动</span></span></summary>
    <div class="body" style="padding-top:10px;">
      <div class="box card wob1" style="padding:12px 14px;">
        <ul style="padding-left:20px;">
          <li style="font-size:13px;margin-bottom:6px;">日志体系：journalctl 常用姿势 + 应用日志落文件 + 崩溃告警</li>
          <li style="font-size:13px;margin-bottom:6px;">自动备份：数据库每日 dump + 异地备份</li>
          <li style="font-size:13px;">监控告警：uptime 探活 + 消息推送</li>
        </ul>
      </div>
    </div>
  </details>

  <h2>{mk4}<span class="uline">待你拍板（0）</span></h2>
  <div class="box card wob1">
    <p style="font-size:12.5px;color:var(--ink-4);margin-bottom:10px;">本期 +0 / -0。<b>⚠ 连续 3 期未动</b>= 已升级进风险预警，需逐项拍板或明确搁置。</p>
    <ol></ol>
  </div>

  <h2>{mk5}<span class="uline">风险预警（0）</span></h2>
  <div class="box card wob2">
    <ul></ul>
  </div>

  <h2>{mk6}<span class="uline">AI建议 · 只基于事实</span></h2>
  <div class="box card wob3">
    <ul class="advice">
      <li><span class="tag2 t-blue">冷启动</span><span class="act">本期尚未出账。首次出账后，每条建议必须给出事实依据（来自登记表/扫描结果/时间轴），直接指出问题，可执行。</span><span class="fact">依据：项目登记表项目清单为空 ｜ 严禁捧杀、严禁敷衍、严禁无依据表扬；本期无纠正项时写明"本期未发现需纠正项"，不凑数。</span></li>
    </ul>
  </div>

  <h2>{mk6}<span class="uline">待归类 · 等你定位（AI 不强行归类，只提议）</span></h2>
  <div class="box card wob2">
    <table class="tb">
      <tr><th>事项</th><th>事实依据</th><th>为什么无法归类</th></tr>
    </table>
  </div>

  <div class="footer">
    分类框架：{owner}定义（AI 无权增删改类目）｜ 时间轴三层：事实→思路→变化，思路无法确认的标"思路待补" ｜ 数据源：项目登记表.md（本页为阅读视图，两者必须一致）<br>
    每日09:00自动出账（只处理过去24小时增量），周日补发全周汇总 ｜ 无法归类的条目，AI必须先问再做主
  </div>

</div>
</body>
</html>
"""


def load_css(skin: str) -> str:
    if skin not in SKINS:
        sys.exit(f"未知皮肤：{skin}（可选：{'/'.join(SKINS)}）")
    base = (SKINS_DIR / "base.css").read_text(encoding="utf-8")
    theme = (SKINS_DIR / f"{skin}.css").read_text(encoding="utf-8")
    return base + "\n" + theme


def switch_skin(html_path: pathlib.Path, skin: str) -> None:
    """只替换 <style> 内的 CSS 与页脚皮肤标注，数据与结构类名一字不动。"""
    html = html_path.read_text(encoding="utf-8")
    start = html.index("<style>") + len("<style>")
    end = html.index("</style>")
    head, body = html[:start], html[end:]
    for s in SKINS:
        body = body.replace(f"皮肤：{s}", f"皮肤：{skin}")
    html_path.write_text(head + "\n" + load_css(skin) + "\n" + body, encoding="utf-8")
    print(f"✓ 已换肤为 {skin}（数据与结构未改动）")


def main():
    ap = argparse.ArgumentParser(description="生成经验账本骨架（九板块结构）")
    ap.add_argument("--dir", required=True, help="账本目录")
    ap.add_argument("--title", default="经验账本", help="账本名称")
    ap.add_argument("--owner", default="我", help="账本主人")
    ap.add_argument("--skin", default="handdrawn", choices=SKINS, help="皮肤")
    ap.add_argument("--category", action="append", default=[], help="二级分类，可重复")
    ap.add_argument("--scan-scope", default="（待安装向导确认）", help="允许扫描的路径")
    ap.add_argument("--delivery", action="store_true", help="生成交付台账.md")
    ap.add_argument("--switch-skin", choices=SKINS, help="对已有账本换肤")
    ap.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = ap.parse_args()

    d = pathlib.Path(args.dir).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    iso = today.isoformat()
    created = f"\n<!-- 建账：{iso} -->\n"

    if args.switch_skin:
        html_path = d / "账本.html"
        if not html_path.exists():
            sys.exit(f"未找到 {html_path}，无法换肤")
        switch_skin(html_path, args.switch_skin)
        return

    cats = args.category or ["（待定义）", "（待定义2）", "（待定义3）"]
    while len(cats) < 3:
        cats.append("（待定义）")
    cats_md = "\n".join(f"- {i+1}. {c}" for i, c in enumerate(cats))

    reg = d / "项目登记表.md"
    if reg.exists() and not args.force:
        print(f"· 已存在 {reg}，跳过（加 --force 可覆盖）")
    else:
        reg.write_text(
            REGISTER_TPL.format(title=args.title, owner=args.owner,
                                categories=cats_md, scan_scope=args.scan_scope,
                                created=created),
            encoding="utf-8",
        )
        print(f"✓ {reg}")

    if args.delivery:
        dv = d / "交付台账.md"
        if dv.exists() and not args.force:
            print(f"· 已存在 {dv}，跳过")
        else:
            dv.write_text(DELIVERY_TPL.format(title=args.title, created=created),
                          encoding="utf-8")
            print(f"✓ {dv}")

    # 周序号：以周一起算
    week = today.isocalendar()[1]
    week_start = today - dt.timedelta(days=today.weekday())
    html = d / "账本.html"
    if html.exists() and not args.force:
        print(f"· 已存在 {html}，跳过（如需换肤请用 --switch-skin）")
    else:
        html.write_text(
            HTML_TPL.format(
                title=args.title, owner=args.owner, css=load_css(args.skin),
                wave=WAVE, mk1=mk("--mk-1"), mk2=mk("--mk-2"), mk3=mk("--mk-3"),
                mk4=mk("--mk-4"), mk5=mk("--mk-5"), mk6=mk("--mk-6"),
                week=f"第 {week} 周 ｜ {week_start.strftime('%m-%d')} ~ {(week_start + dt.timedelta(days=6)).strftime('%m-%d')}",
                cat1=cats[0], cat2=cats[1], cat3=cats[2],
            ),
            encoding="utf-8",
        )
        print(f"✓ {html}")

    print("\n下一步：")
    print("  1. 走安装向导（references/install-guide.md）：分类框架 / 扫描范围 / 出账时间 / 皮肤")
    print("  2. 冷启动回填：扫描历史变动与对话，起草登记表与首批时间轴")
    print("  3. 今后每有项目开工，跑 scripts/open_project.py 建工时行（开工即记工时）")
    print(f"  4. 打开 {html} 查看（本地单文件，双击即可）")


if __name__ == "__main__":
    main()
