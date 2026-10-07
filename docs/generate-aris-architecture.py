#!/usr/bin/env python3
"""Build a self-contained architecture map from the cloned ARIS catalog."""

from __future__ import annotations

import html
import re
import subprocess
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARIS = ROOT / "aris"
CATALOG = ARIS / "docs" / "SKILLS_CATALOG.md"
OUTPUT = Path(__file__).resolve().parent / "aris-skills-architecture.html"

CATEGORY_NAMES = {
    "🏗️ Workflow Orchestrators": "工作流编排",
    "📚 Literature & Search": "文献与检索",
    "💡 Ideation & Method Design": "选题与方法",
    "🧠 Proof Engineering": "证明工程",
    "🧪 Experiments & Infrastructure": "实验与算力",
    "🛡️ Review, Audit & Assurance": "评审与证据审计",
    "📝 Paper Writing & Figures": "论文与图表",
    "🎤 Talks, Posters & Resubmission": "报告、海报与改投",
    "📜 Patents": "专利",
    "🧰 Meta, Utilities & Integrations": "知识与工具集成",
}

ZH_ROLES = dict(
    line.split("|", 1) for line in """
research-pipeline|串联找题、实验、评审和论文写作
idea-discovery|从研究方向到候选想法、查新和实验方案
idea-discovery-robot|面向机器人与具身智能的找题流程
experiment-bridge|把实验计划变为代码、任务和初始结果
auto-review-loop|评审、修复、补实验、再评审的循环
auto-review-loop-llm|使用兼容 OpenAI 接口的评审模型运行循环
auto-review-loop-minimax|使用 MiniMax 评审的循环变体
paper-writing|从研究叙事到 LaTeX 论文和审计
rebuttal|拆解审稿意见并起草有证据的回复
resubmit-pipeline|在不新增实验的约束下适配新投稿 venue
paper-talk|从论文制作并审计会议报告
research-refine-pipeline|串联方法精炼与实验规划
patent-pipeline|串联现有技术、权利要求、说明书与格式
dse-loop|运行、分析、调参的设计空间探索循环
meta-optimize|从使用记录提出技能改进建议
meta-apply|经人和外部评审通过后应用技能改动
research-lit|汇集多来源文献并整理研究地形图
arxiv|检索、下载和总结 arXiv 论文
semantic-scholar|检索正式发表论文与引文元数据
deepxiv|按摘要、章节逐层阅读开放论文
exa-search|搜索网页并抽取页面内容
web-debug-search|跨技术社区检索调试证据
openalex|检索开放引文图和机构信息
gemini-search|用主题分解与别名扩展发现文献
alphaxiv|快速查看单篇论文及回退来源
comm-lit-review|通信与无线领域专用文献调研
novelty-check|逐项比较研究想法与最接近的已有工作
idea-creator|生成候选研究想法并设计 pilot
research-refine|围绕问题锚点反复精炼方法
experiment-plan|把研究主张变成实验和消融路线图
ablation-planner|根据结果规划必要的消融实验
formula-derivation|整理假设和公式推导链
proof-orchestrator|跨会话管理证明任务与证据
research-implement-feature|按可运行主干逐步实现研究功能
run-experiment|在本地或云端部署实验
monitor-experiment|监控任务并收集结果
analyze-results|统计比较实验结果
experiment-queue|排队运行多配置实验并处理重试
vast-gpu|租用和管理 Vast.ai GPU
serverless-modal|在 Modal 上运行无服务器 GPU 作业
qzcli|管理启智平台 GPU 作业
training-check|检查训练指标和 GPU 异常
system-profile|分析性能瓶颈与资源使用
research-review|获取一次外部模型的深入研究评审
experiment-audit|核查实验代码、结果与评估完整性
result-to-claim|判断结果支持哪些研究主张
paper-claim-audit|用原始结果核对论文数字与比较
citation-audit|核查引文身份、元数据和引用语境
proof-checker|检查证明义务、漏洞和反例
kill-argument|让独立评审提出最强拒稿理由并应答
integrity-forensics|对证据链做投稿前取证式检查
paper-plan|规划论文结构与主张证据矩阵
paper-write|逐节撰写 LaTeX 论文
paper-figure|从实验数据生成图表与表格
figure-spec|把结构化规格确定性渲染为 SVG
paper-illustration|借助 Gemini 生成论文插图
paper-illustration-image2|借助 Codex 图像桥接生成论文插图
mermaid-diagram|生成并验证 Mermaid 图表
pixel-art|为文档和幻灯片生成像素风 SVG
paper-compile|编译 LaTeX 并检查 PDF
auto-paper-improvement-loop|反复审稿、修文和编译
proof-writer|撰写定理和引理的严格证明
writing-systems-papers|系统论文的段落级写作蓝图
grant-proposal|依据想法和文献起草基金申请
paper-slides|生成会议幻灯片、讲稿和备注
slides-polish|逐页审查与修订演讲幻灯片
paper-poster-html|用 HTML/CSS 制作可打印会议海报
paper-poster|旧海报入口，转向 paper-poster-html
invention-structuring|把原始想法整理为发明披露
claims-drafting|起草独立和从属权利要求
embodiment-description|撰写专利实施例
specification-writing|撰写专利说明书
figure-description|撰写专利附图说明
prior-art-search|检索相关专利和学术现有技术
patent-novelty-check|评估专利新颖性与非显而易见性
patent-review|模拟外部审查员批判专利申请
jurisdiction-format|适配中国、美国或欧洲申请格式
research-wiki|跨会话保存论文、想法、实验和主张
wiki-enrich|补充知识库中单篇论文的空白内容
render-html|将研究报告渲染为单文件 HTML
overleaf-sync|同步本地论文与 Overleaf 项目
feishu-notify|通过飞书发送通知或交互消息
interview-cheatsheet|生成机器学习面试复习资料
""".strip().splitlines()
)


def plain(markdown: str) -> str:
    markdown = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", markdown)
    return markdown.replace("**", "").replace("`", "").strip()


def link(name: str, label: str | None = None, css: str = "") -> str:
    label = html.escape(label or name)
    return f'<a class="{css}" href="https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/main/skills/{html.escape(name)}/SKILL.md" title="打开 {html.escape(name)}/SKILL.md">{label}</a>'


groups: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
section = None
row = re.compile(r"^\| \[`/([^`]+)`\]\(\.\./skills/[^)]+\) \| (.*?) \| (.*?) \|$")
for raw in CATALOG.read_text().splitlines():
    if raw.startswith("## "):
        section = raw[3:].strip()
    match = row.match(raw)
    if match:
        name, role, requires = match.groups()
        groups.setdefault(section, []).append(
            {"name": name, "role": plain(role), "requires": plain(requires)}
        )

skills = [item for group in groups.values() for item in group]
names = {item["name"] for item in skills}
source_names = {path.parent.name for path in (ARIS / "skills").glob("*/SKILL.md")}
assert names == source_names, (sorted(source_names - names), sorted(names - source_names))
assert names == set(ZH_ROLES), (sorted(names - set(ZH_ROLES)), sorted(set(ZH_ROLES) - names))
assert len(skills) == 83
commit = subprocess.check_output(["git", "-C", str(ARIS), "rev-parse", "--short", "HEAD"], text=True).strip()
mirror_counts = {
    dirname: len(list((ARIS / "skills" / dirname).glob("*/SKILL.md")))
    for dirname in ("skills-codex", "skills-codex-claude-review", "skills-codex-gemini-review")
}


def sequence(items: list[str], *, ordered: bool = True) -> str:
    marker = "→" if ordered else "·"
    separator = f'<span class="seq-arrow" aria-hidden="true">{marker}</span>'
    return separator.join(link(item, css="seq-link") for item in items)


stages = [
    (
        "W1 · 找题与方案",
        "idea-discovery",
        "方向 → 候选想法、查新、pilot、实验计划",
        ["research-lit", "idea-creator", "novelty-check", "research-review", "research-refine-pipeline"],
        "refine-pipeline = research-refine → experiment-plan",
    ),
    (
        "W1.5 · 实验桥接",
        "experiment-bridge",
        "实验计划 → 可运行代码与初始结果",
        ["run-experiment", "monitor-experiment"],
        "含代码审查与最小 sanity check",
    ),
    (
        "W2 · 迭代评审",
        "auto-review-loop",
        "评审 → 修复/补实验 → 分析 → 再评审",
        ["novelty-check", "run-experiment", "analyze-results", "monitor-experiment"],
        "自身执行外部评审；这些技能按修复需求启用，另有 LLM / MiniMax 后端变体",
    ),
    (
        "W3 · 论文写作",
        "paper-writing",
        "研究叙事 → LaTeX、PDF 与投稿审计",
        ["paper-plan", "paper-figure", "paper-write", "paper-compile", "auto-paper-improvement-loop"],
        "图示方式可选；另有主张、引用、证明审计",
    ),
]

stage_html = []
for i, (title, name, desc, steps, note) in enumerate(stages):
    step_label = "条件关联能力" if i == 2 else "主要调用链"
    stage_html.append(
        f'''<article class="stage stage-{i+1}">
          <div class="stage-kicker">{html.escape(title)}</div>
          <h3>{link(name)}</h3>
          <p>{html.escape(desc)}</p>
          <div class="stage-steps"><span class="relation-label">{step_label}</span>{sequence(steps, ordered=i != 2)}</div>
          <small>{html.escape(note)}</small>
        </article>'''
    )
main_flow = '<div class="flow-arrow" aria-hidden="true">→</div>'.join(stage_html)

catalog_html = []
for original, items in groups.items():
    zh = CATEGORY_NAMES[original]
    cards = []
    for item in items:
        name = item["name"]
        cards.append(
            f'''<article class="skill-item" data-search="{html.escape((name + ' ' + ZH_ROLES[name] + ' ' + item['role']).lower(), quote=True)}">
              <div class="skill-name">{link(name, '/' + name)}</div>
              <p>{html.escape(ZH_ROLES[name])}</p>
              <details><summary>原仓库说明与依赖</summary><p>{html.escape(item['role'])}</p><p><strong>外部依赖：</strong>{html.escape(item['requires'])}</p></details>
            </article>'''
        )
    catalog_html.append(
        f'''<section class="catalog-group" id="group-{len(catalog_html)+1}">
          <h3>{html.escape(zh)} <span>{len(items)}</span></h3>
          <div class="skill-grid">{''.join(cards)}</div>
        </section>'''
    )

page = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ARIS Skills 架构图</title>
<style>
  :root {{ color-scheme: light dark; --bg:#f5f7fb; --surface:#fff; --ink:#162238; --sub:#516078; --line:#d8deea; --accent:#2859c5; --soft:#eaf0ff; --green:#dff3e9; --orange:#fff0d7; --purple:#eee8ff; --pink:#fbe8ee; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg:#101722; --surface:#182232; --ink:#f0f4fb; --sub:#acb9cc; --line:#334158; --accent:#8fb1ff; --soft:#202f50; --green:#17372d; --orange:#3e321f; --purple:#2f2549; --pink:#402732; }} }}
  * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.55 system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; }}
  a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
  .wrap {{ max-width:1600px; margin:auto; padding:34px 34px 80px; }}
  header {{ display:flex; gap:20px; justify-content:space-between; align-items:end; flex-wrap:wrap; border-bottom:1px solid var(--line); padding-bottom:24px; }}
  h1 {{ font-size:clamp(28px,3vw,42px); line-height:1.15; margin:0 0 10px; letter-spacing:-.02em; }}
  header p, .intro {{ margin:0; color:var(--sub); max-width:850px; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:8px; }} .badge {{ background:var(--soft); color:var(--ink); padding:5px 10px; border-radius:999px; font-size:12px; font-weight:650; white-space:nowrap; }}
  h2 {{ margin:36px 0 8px; font-size:22px; }} .section-note {{ color:var(--sub); margin:0 0 18px; }}
  .entry {{ background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:14px 18px; margin-top:22px; display:flex; align-items:center; gap:16px; flex-wrap:wrap; }}
  .entry strong {{ font-size:17px; }} .entry span {{ color:var(--sub); }} .entry em {{ font-style:normal; margin-left:auto; color:var(--sub); font-size:13px; }}
  .flow {{ display:grid; grid-template-columns:minmax(0,1fr) 22px minmax(0,1fr) 22px minmax(0,1fr) 22px minmax(0,1fr); align-items:stretch; gap:10px; }}
  .flow-arrow {{ color:var(--sub); align-self:center; justify-self:center; font-size:28px; font-weight:700; }}
  .stage {{ min-width:0; padding:18px; background:var(--surface); border:1px solid var(--line); border-top:5px solid var(--accent); border-radius:14px; }}
  .stage-1 {{ border-top-color:#3974cb; }} .stage-2 {{ border-top-color:#389b76; }} .stage-3 {{ border-top-color:#ba8434; }} .stage-4 {{ border-top-color:#a163a5; }}
  .stage-kicker {{ font-weight:750; font-size:12px; letter-spacing:.03em; color:var(--sub); }} .stage h3 {{ margin:6px 0 7px; font-size:19px; overflow-wrap:anywhere; }} .stage p {{ margin:0 0 14px; min-height:44px; }}
  .stage-steps {{ display:flex; flex-wrap:wrap; align-items:center; gap:4px; font-size:12px; line-height:1.8; }} .seq-link {{ color:var(--ink); background:var(--soft); border-radius:5px; padding:1px 5px; white-space:nowrap; }} .seq-arrow {{ color:var(--sub); padding:0 2px; }}
  .relation-label {{ display:block; flex-basis:100%; color:var(--sub); font-size:11px; font-weight:700; }}
  .stage small {{ color:var(--sub); display:block; margin-top:11px; }}
  .branches {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-top:16px; }}
  .branch {{ background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:15px; }} .branch:nth-child(1) {{ background:var(--green); }} .branch:nth-child(2) {{ background:var(--orange); }} .branch:nth-child(3) {{ background:var(--purple); }} .branch:nth-child(4) {{ background:var(--pink); }}
  .branch h3 {{ margin:0 0 6px; font-size:15px; }} .branch p {{ margin:0; color:var(--sub); font-size:13px; }} .branch .links {{ margin:8px 0; display:flex; flex-wrap:wrap; gap:5px 9px; font-size:13px; }}
  .foundation {{ margin-top:16px; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }} .layer {{ border:1px dashed var(--line); padding:13px 16px; border-radius:11px; }} .layer strong {{ display:block; margin-bottom:4px; }} .layer p {{ color:var(--sub); margin:0; font-size:13px; }}
  .legend {{ margin:15px 0 0; font-size:13px; color:var(--sub); }}
  .catalog-toolbar {{ display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin:15px 0 20px; }} input {{ font:inherit; background:var(--surface); color:var(--ink); border:1px solid var(--line); border-radius:9px; padding:10px 13px; width:min(460px,100%); }} #match-count {{ color:var(--sub); font-size:13px; }}
  .catalog-group {{ margin:25px 0 0; }} .catalog-group h3 {{ border-bottom:1px solid var(--line); padding-bottom:7px; font-size:17px; }} .catalog-group h3 span {{ color:var(--sub); font-size:13px; font-weight:500; margin-left:6px; }}
  .skill-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:9px; }} .skill-item {{ min-width:0; background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:11px 13px; }}
  .skill-name {{ font-weight:700; overflow-wrap:anywhere; }} .skill-item p {{ margin:5px 0 0; font-size:13px; }} .skill-item details {{ margin-top:7px; color:var(--sub); font-size:12px; }} .skill-item summary {{ cursor:pointer; }} .skill-item details p {{ font-size:12px; }}
  footer {{ margin-top:42px; border-top:1px solid var(--line); padding-top:18px; color:var(--sub); font-size:13px; }}
  @media(max-width:1150px) {{ .flow {{ grid-template-columns:1fr 24px 1fr; }} .flow .stage:nth-of-type(3) {{ grid-column:1; }} .flow .stage:nth-of-type(4) {{ grid-column:3; }} .flow-arrow:nth-of-type(2) {{ display:none; }} .branches {{ grid-template-columns:repeat(2,1fr); }} }}
  @media(max-width:760px) {{ .wrap {{ padding:22px 16px 55px; }} .flow {{ display:flex; flex-direction:column; }} .flow-arrow {{ transform:rotate(90deg); }} .branches,.foundation,.skill-grid {{ grid-template-columns:1fr; }} .stage p {{ min-height:0; }} }}
</style>
</head>
<body>
<main class="wrap">
<header>
  <div><h1>ARIS Skills 架构图</h1><p>从总编排到独立技能的阅读地图。实线顺序表示主工作流；支线和底座表示可选或跨阶段能力。点击技能名称可打开本地 <code>SKILL.md</code>。</p></div>
  <div class="meta"><a class="badge" href="aris-workflow-stages.html">逐阶段看具体工作流 →</a><span class="badge">源码 {html.escape(commit)}</span><span class="badge">83 个顶层技能</span><span class="badge">Codex 镜像 {mirror_counts['skills-codex']}</span><span class="badge">评审适配 {mirror_counts['skills-codex-claude-review']} + {mirror_counts['skills-codex-gemini-review']}</span></div>
</header>

<section aria-labelledby="overview"><h2 id="overview">主线：研究方向到论文</h2><p class="section-note">四段由 {link('research-pipeline')} 串联。最后的论文写作在该总流程里由 <code>AUTO_WRITE</code> 控制，也能独立调用。</p>
  <div class="entry"><strong>{link('research-pipeline')}</strong><span>统一编排、传递参数、记录阶段状态和断点恢复</span><em>W1 → W1.5 → W2 → W3</em></div>
  <div class="flow" style="margin-top:14px">{main_flow}</div>
  <p class="legend">图中的子步骤是主要编排关系，简化了条件分支。尤其是数据源、绘图方式、评审后端和投稿审计会按配置与材料条件启用；点击技能可核对原始规则。</p>
</section>

<section aria-labelledby="branches-title"><h2 id="branches-title">并行支线与后续产物</h2><p class="section-note">这些是从想法或论文分出的路线，不属于每次主流程必经阶段。</p>
  <div class="branches">
    <article class="branch"><h3>从已验证想法分出</h3><div class="links">{link('grant-proposal')} {link('patent-pipeline')}</div><p>基金申请是独立产物；专利线先查现有技术，再起草、评审和适配法域。</p><details><summary>展开专利链</summary><div class="stage-steps">{sequence(['prior-art-search','patent-novelty-check','invention-structuring','claims-drafting','specification-writing','patent-review','jurisdiction-format'])}</div></details></article>
    <article class="branch"><h3>论文之后</h3><div class="links">{link('rebuttal')} {link('resubmit-pipeline')} {link('paper-talk')} {link('paper-poster-html')}</div><p>回应审稿、跨 venue 改投、制作会议报告或海报，按事件单独启动。</p></article>
    <article class="branch"><h3>理论与领域专线</h3><div class="links">{link('proof-orchestrator')} {link('proof-writer')} {link('proof-checker')} {link('dse-loop')} {link('idea-discovery-robot')}</div><p>证明可跨会话推进；体系结构与机器人各有领域化路线。</p></article>
    <article class="branch"><h3>改进 ARIS 自身</h3><div class="links">{link('meta-optimize')} <span aria-hidden="true">→</span> {link('meta-apply')}</div><p>前者分析日志并提出补丁；后者经人和独立评审通过后应用。</p></article>
  </div>
</section>

<section aria-labelledby="layers-title"><h2 id="layers-title">贯穿所有阶段的底座</h2>
  <div class="foundation">
    <div class="layer"><strong>知识与呈现</strong><p>{link('research-wiki')} 保存论文、想法、实验和主张的关系；{link('render-html')} 把报告转换成可读视图。</p></div>
    <div class="layer"><strong>执行者与审稿者</strong><p>主技能驱动执行；外部模型、评审适配或确定性校验负责不同质量关口。Codex 镜像是平台版本，不是额外研究阶段。</p></div>
    <div class="layer"><strong>契约与工具</strong><p><a href="https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/tree/main/skills/shared-references/">shared-references/</a> 定义跨技能规则；<a href="https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/tree/main/tools/">tools/</a> 放 API、状态和校验脚本；<a href="https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/tree/main/mcp-servers/">mcp-servers/</a> 接外部模型。</p></div>
  </div>
</section>

<section aria-labelledby="catalog-title"><h2 id="catalog-title">全部 83 个顶层技能</h2><p class="section-note">按原仓库 <a href="https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/main/docs/SKILLS_CATALOG.md">SKILLS_CATALOG.md</a> 分组；中文作用是一句话导览，展开可读原仓库的英文说明及外部依赖。</p>
  <div class="catalog-toolbar"><input id="skill-search" type="search" placeholder="搜索技能名、作用或英文说明…" aria-label="搜索技能"><span id="match-count">显示 83 / 83</span></div>
  {''.join(catalog_html)}
</section>

<footer>来源：本地 ARIS 仓库 <code>{html.escape(commit)}</code> 的 <a href="https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/main/AGENT_GUIDE.md">AGENT_GUIDE.md</a>、<a href="https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/main/docs/SKILLS_CATALOG.md">SKILLS_CATALOG.md</a> 与各 <code>SKILL.md</code>。主树 83 个技能；<code>skills-codex/</code> 的 83 个镜像及 Claude/Gemini 审稿覆盖层共 106 个文件，已单独计数，不重复画成科研阶段。</footer>
</main>
<script>
const input = document.getElementById('skill-search');
const cards = [...document.querySelectorAll('.skill-item')];
const groups = [...document.querySelectorAll('.catalog-group')];
input.addEventListener('input', () => {{
  const query = input.value.trim().toLocaleLowerCase();
  let shown = 0;
  for (const card of cards) {{
    const visible = !query || card.dataset.search.includes(query);
    card.hidden = !visible;
    if (visible) shown++;
  }}
  for (const group of groups) {{
    group.hidden = ![...group.querySelectorAll('.skill-item')].some(card => !card.hidden);
  }}
  document.getElementById('match-count').textContent = `显示 ${{shown}} / ${{cards.length}}`;
}});
</script>
</body>
</html>
'''

OUTPUT.write_text(page)
print(f"Wrote {OUTPUT} ({len(skills)} skills, {len(page):,} bytes)")
