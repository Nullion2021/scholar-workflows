# `research-lit` 中文阅读版

译自 ARIS 的 [原始 SKILL.md](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/blob/main/skills/research-lit/SKILL.md)。命令、参数名、路径和可执行代码块沿用原文；此文件供阅读与评估，未作为可调用 skill 安装。代码块中的英文注释和提示词也沿用原文，以便逐行对照。

```yaml
name: research-lit
description: 检索和分析研究论文、寻找相关工作、总结关键观点。用户要求“找论文”“相关工作”“文献综述”“这篇论文讲什么”，或需要理解学术论文时使用。
argument-hint: "[论文主题或网址]"
allowed-tools: Bash(*), Read, Glob, Grep, WebSearch, WebFetch, Write, Agent, mcp__zotero__*, mcp__obsidian-vault__*
```

# 研究文献综述

研究主题：`$ARGUMENTS`

## 常量

- **PAPER_LIBRARY**：用户的本地 PDF 论文库，按以下顺序检查：
  1. 当前项目的 `papers/`
  2. 当前项目的 `literature/`
  3. 用户在 `CLAUDE.md` 的 `## Paper Library` 下指定的路径
- **MAX_LOCAL_PAPERS = 20**：最多扫描 20 篇本地 PDF，每篇读取前三页。超过上限时，优先处理文件名与主题更相关的论文。
- **SOURCES = `all`**：要检索的文献来源。可选值：`zotero`、`obsidian`、`local`、`web`、`semantic-scholar`、`deepxiv`、`exa`、`gemini`、`openalex`、`all`。完整来源表和选择规则见下文“数据来源”。
- **ARXIV_DOWNLOAD = false**：设为 `true` 时，检索后将最相关的 3–5 篇 arXiv 论文 PDF 下载至 PAPER_LIBRARY。默认 `false` 时只通过 arXiv API 获取标题、摘要、作者等元数据，不下载文件。
- **ARXIV_MAX_DOWNLOAD = 5**：开启下载时，最多下载的 PDF 数量。

> 💡 参数覆盖示例：
> - `/research-lit "topic" — paper library: ~/my_papers/`：自定义本地 PDF 路径
> - `/research-lit "topic" — sources: zotero, local`：只查 Zotero 和本地 PDF
> - `/research-lit "topic" — sources: web`：只查网页，不查本地资料
> - `/research-lit "topic" — sources: web, semantic-scholar`：额外查 Semantic Scholar 的正式发表论文，如 IEEE、ACM 论文
> - `/research-lit "topic" — sources: all, deepxiv`：在默认来源之外加入 DeepXiv
> - `/research-lit "topic" — arxiv download: true`：下载最相关的 arXiv PDF
> - `/research-lit "topic" — arxiv download: true, max download: 10`：最多下载 10 篇

## 数据来源

该 skill 按**优先级顺序**检查多个来源。来源都是可选的；未配置或未请求的来源会跳过。

### 来源选择

从 `$ARGUMENTS` 解析 `— sources:` 指令：

- **指定了 `— sources:`**：只查列出的来源，以逗号分隔。有效值为 `zotero`、`obsidian`、`local`、`web`、`semantic-scholar`、`deepxiv`、`exa`、`gemini`、`openalex`、`all`。
- **未指定**：默认 `all`，按优先级查询可用的默认来源。`semantic-scholar`、`deepxiv`、`exa`、`gemini`、`openalex` **不包含在** `all` 中，必须显式列出。

示例：

```
/research-lit "diffusion models"                                    → all (default, no S2)
/research-lit "diffusion models" — sources: all                     → all (default, no S2)
/research-lit "diffusion models" — sources: zotero                  → Zotero only
/research-lit "diffusion models" — sources: zotero, web             → Zotero + web
/research-lit "diffusion models" — sources: local                   → local PDFs only
/research-lit "topic" — sources: obsidian, local, web               → skip Zotero
/research-lit "topic" — sources: web, semantic-scholar              → web + S2 API (IEEE/ACM venue papers)
/research-lit "topic" — sources: deepxiv                            → DeepXiv only
/research-lit "topic" — sources: all, deepxiv                       → default sources + DeepXiv
/research-lit "topic" — sources: all, semantic-scholar              → all + S2 API
/research-lit "topic" — sources: exa                               → Exa only (broad web + content extraction)
/research-lit "topic" — sources: all, exa                          → default sources + Exa web search
/research-lit "topic" — sources: gemini                            → Gemini only (AI-powered broad discovery)
/research-lit "topic" — sources: all, gemini                       → default sources + Gemini discovery
/research-lit "topic" — sources: gemini, semantic-scholar           → Gemini + S2 (broad discovery + venue metadata)
/research-lit "topic" — sources: openalex                          → OpenAlex only (open citation graph + institutions)
/research-lit "topic" — sources: semantic-scholar, openalex         → S2 + OpenAlex (complementary metadata)
```

### 来源表

| 优先级 | 来源 | ID | 可用性判断 | 提供的信息 |
|---|---|---|---|---|
| 1 | **Zotero**（经 MCP） | `zotero` | 尝试调用任一 `mcp__zotero__*` 工具；不可用则跳过 | 分类、标签、批注、PDF 高亮、BibTeX、语义搜索 |
| 2 | **Obsidian**（经 MCP） | `obsidian` | 尝试调用任一 `mcp__obsidian-vault__*` 工具；不可用则跳过 | 研究笔记、论文摘要、带标签的参考资料、双链 |
| 3 | **本地 PDF** | `local` | `Glob: papers/**/*.pdf, literature/**/*.pdf` | PDF 原文的前三页 |
| 4 | **网页搜索** | `web` | WebSearch 始终可用 | arXiv、Semantic Scholar、Google Scholar |
| 5 | **Semantic Scholar API** | `semantic-scholar` | 找到 `$S2_FETCHER`，其标准文件名为 `semantic_scholar_fetch.py`，参见集成规范第 2 节 | IEEE、ACM、Springer 等发表论文的结构化元数据，包括引用数、发表场所、简要总结。只有通过 `— sources: semantic-scholar` 等参数显式请求才运行 |
| 6 | **DeepXiv CLI** | `deepxiv` | 找到 `$DEEPXIV_FETCHER`（`deepxiv_fetch.py`），且系统存在 `deepxiv` 命令 | 分级获取论文：搜索、简述、开头、指定章节、热门论文、网页搜索。仅在显式请求时运行 |
| 7 | **Exa Search** | `exa` | 找到 `$EXA_FETCHER`（`exa_search.py`）；由脚本处理 `exa-py` SDK 和 API 密钥 | 带内容提取的广域网页搜索，可覆盖博客、文档、新闻、公司页面及论文。仅在显式请求时运行 |
| 8 | **Gemini**（MCP 或 CLI） | `gemini` | 可用 `mcp__gemini-cli__ask-gemini` 工具，或安装了 `gemini` CLI | 将主题拆成子问题、别名和变体，扩大文献发现范围。优先使用 MCP，失败后尝试 CLI；仅在显式请求时运行 |
| 9 | **OpenAlex** | `openalex` | 找到 `$OPENALEX_FETCHER`（`openalex_fetch.py`），且 Python 可导入 `requests` | 开放引用图谱、机构、资助与跨学科元数据；仅在显式请求时运行 |

> **降级运行**：未配置 MCP 服务器时，仍可使用本地 PDF 和网页搜索。Zotero 与 Obsidian 是附加来源。

## 工作流程

### 步骤 0a：搜索 Zotero 文献库（如可用）

未配置 Zotero MCP 时，跳过整个步骤。尝试调用 Zotero 搜索工具；若成功：

1. **按主题检索**：找出匹配研究主题的论文。
2. **查看分类**：检查是否已有与主题相关的分类或文件夹。
3. **提取批注**：对高度相关的论文，读取 PDF 高亮和笔记，这些内容体现用户的关注点。
4. **导出 BibTeX**：获取相关论文的引文信息，供后续 `/paper-write` 使用。
5. **汇总结果**：对每条相关记录提取标题、作者、年份、发表场所、用户批注与高亮、标签和所在分类。

> 📚 Zotero 批注能体现用户亲自标出的重点，因此比通用摘要更能反映用户关心的问题。

### 步骤 0b：搜索 Obsidian 笔记库（如可用）

未配置 Obsidian MCP 时，跳过整个步骤。尝试调用 Obsidian 搜索工具；若成功：

1. **搜索笔记库**：寻找与主题相关的笔记。
2. **查看标签**：寻找相关标签，如 `#diffusion-models`、`#paper-review`。
3. **阅读研究笔记**：提取用户自己的摘要与见解。
4. **沿链接查找**：跟进指向其他相关笔记的双链。
5. **汇总结果**：记录标题、路径、用户摘要与见解、笔记链接，以及论文网址、阅读状态、评分等 frontmatter 元数据。

> 📝 Obsidian 笔记记录了用户已经形成的理解，有助于把握其研究视角。

### 步骤 0c：扫描本地论文库

在线检索前，先检查用户是否已有相关论文：

1. **定位论文库**：在 PAPER_LIBRARY 所列路径查找 PDF。

```
   Glob: papers/**/*.pdf, literature/**/*.pdf
   ```

2. **与 Zotero 去重**：如果步骤 0a 找到了论文，则按文件名或标题跳过已覆盖的本地 PDF。
3. **按相关性过滤**：用文件名和首页内容与研究主题匹配，跳过明显无关的论文。
4. **总结相关论文**：对最多 MAX_LOCAL_PAPERS 篇 PDF，读取前三页（标题、摘要、引言），提取标题、作者、年份、核心贡献和主题相关性，并标记直接相关与间接相关。
5. **建立本地基础**：整理“你已拥有的论文”部分，再用外部检索补缺。

> 📚 本地收藏足够丰富时，外部搜索可以集中于尚未覆盖的部分。
>
> ⚠️ **若三个 PAPER_LIBRARY 路径都没有命中，须先告知用户**，再继续。否则，使用 Zotero、Mendeley 等管理 PDF 的用户可能误以为 `— sources: all` 已覆盖自己的论文库。输出原文指定的警告：
>
> `WARN: local contributed nothing — no PDFs found in papers/, literature/, or a configured paper library. To include yours, add a "## Paper Library" heading to CLAUDE.md followed by the directory path.`
>
> 然后继续步骤 1。

### 步骤 1：外部检索

- 使用 WebSearch 查找该主题的近期论文。
- 检查 arXiv、Semantic Scholar、Google Scholar。
- 除非研究基础性工作，否则优先关注近两年的论文。
- **去重**：跳过已在 Zotero、Obsidian 或本地论文库中发现的论文。

**arXiv API 检索**：未指定 `— sources:`，或参数包含 `web`、`all` 时运行。默认不下载论文；arXiv API 属于优先级 4 的网页来源。

**D2 策略的来源记录（由编排模型负责）**：执行者须在上下文中维护“成功参与的来源”列表。对于依赖脚本的来源（arXiv、Semantic Scholar、DeepXiv、Exa、OpenAlex），只有脚本路径找到且调用退出码为 0，才算来源参与；即使返回空结果，只要调用成功也计入。对于 Zotero、Obsidian、本地 PDF、WebSearch、Gemini 等非脚本来源，按步骤 1 末尾的规则单独判定。没有被 `— sources:` 请求的来源不计入。步骤 1 结束、下载 PDF 之前，如果参与来源为零，则报告 D2 聚合为空并停止。各代码块可能在不同 shell 中执行，因此在模型上下文中记录参与来源，不能依赖跨代码块共享的 shell 变量。参见[集成规范第 2 节](../../aris/skills/shared-references/integration-contract.md)。

按标准路径查找 `$ARXIV_FETCHER`。它遵循 D2 策略：调用失败时警告并继续聚合其他来源，不因单个来源失败而中止整个检索。

```bash
# Canonical strict-safe resolver (see shared-references/integration-contract.md §2).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .aris/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
ARXIV_FETCHER=".aris/tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER="tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && ARXIV_FETCHER="$ARIS_REPO/tools/arxiv_fetch.py"; }
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER=""

if [ -n "$ARXIV_FETCHER" ]; then
  # Search arXiv API for structured results (title, abstract, authors, categories).
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  if python3 "$ARXIV_FETCHER" search "QUERY" --max 10; then
    echo "D2 contribution: arxiv (helper invocation exit 0)" >&2
  else
    echo "WARN: arxiv_fetch.py invocation failed; D2 aggregate continues with WebSearch results." >&2
  fi
else
  echo "WARN: arxiv_fetch.py not resolved; falling back to WebSearch for arXiv hits." >&2
fi
```

> **记录要求**：收集各来源代码块输出的 `D2 contribution: …` 行，供步骤 1 末尾判断参与来源。WebSearch 只有在被请求且实际调用时才计入，须另行记录；末尾的标准规则与此保持一致。

找不到 `$ARXIV_FETCHER` 时，使用 WebSearch 搜索 arXiv。

arXiv API 可返回标题、摘要、完整作者列表、类别和日期等结构化元数据。将它与 WebSearch 结果合并、去重。

**Semantic Scholar API 检索**：仅在 `sources` 包含 `semantic-scholar` 时运行，查找 arXiv 以外的正式发表论文。

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .aris/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
# Resolve $S2_FETCHER (Policy D2 — warn-and-skip on missing).
S2_FETCHER=".aris/tools/semantic_scholar_fetch.py"
[ -f "$S2_FETCHER" ] || S2_FETCHER="tools/semantic_scholar_fetch.py"
[ -f "$S2_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && S2_FETCHER="$ARIS_REPO/tools/semantic_scholar_fetch.py"; }
[ -f "$S2_FETCHER" ] || S2_FETCHER=""

if [ -n "$S2_FETCHER" ]; then
  # Search for published CS/Engineering papers with quality filters.
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  if python3 "$S2_FETCHER" search "QUERY" --max 10 \
      --fields-of-study "Computer Science,Engineering" \
      --publication-types "JournalArticle,Conference"; then
    echo "D2 contribution: semantic_scholar (helper invocation exit 0)" >&2
  else
    echo "WARN: semantic_scholar_fetch.py invocation failed; D2 aggregate continues with remaining sources." >&2
  fi
fi
```

找不到 `$S2_FETCHER` 时直接跳过；D2 聚合继续处理其他来源。

**为何使用 Semantic Scholar？** 许多 IEEE/ACM 期刊论文没有 arXiv 版本。S2 能补充这些正式发表论文，并提供引用数和发表场所信息。

**arXiv 与 S2 去重**：先匹配 arXiv ID，即 S2 的 `externalIds.ArXiv` 字段。

- 同一论文两处都有时，查看 S2 的 `venue`/`publicationVenue`。如果已在期刊或会议发表（如 IEEE TWC、JSAC），采用 S2 的发表场所、引用数、DOI 元数据，同时保留 arXiv PDF 下载链接。
- 如果 S2 条目尚无发表场所，保留 arXiv 版本。
- 没有 `externalIds.ArXiv` 的 S2 结果，是这一来源补充的无 arXiv 版本论文。

**DeepXiv 检索**：仅在 `sources` 包含 `deepxiv` 时运行，用 DeepXiv 适配器逐层获取内容。

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .aris/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
# Resolve $DEEPXIV_FETCHER (Policy D2 — warn-and-skip on missing).
DEEPXIV_FETCHER=".aris/tools/deepxiv_fetch.py"
[ -f "$DEEPXIV_FETCHER" ] || DEEPXIV_FETCHER="tools/deepxiv_fetch.py"
[ -f "$DEEPXIV_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && DEEPXIV_FETCHER="$ARIS_REPO/tools/deepxiv_fetch.py"; }
[ -f "$DEEPXIV_FETCHER" ] || DEEPXIV_FETCHER=""

if [ -n "$DEEPXIV_FETCHER" ] && command -v deepxiv >/dev/null 2>&1; then
  # Wrap each adapter call so set -e doesn't abort the SKILL.
  if python3 "$DEEPXIV_FETCHER" search "QUERY" --max 10; then
    echo "D2 contribution: deepxiv (helper invocation exit 0)" >&2

    # Then deepen only for the most relevant papers (sub-calls don't change D2 aggregate count):
    python3 "$DEEPXIV_FETCHER" paper-brief ARXIV_ID \
      || echo "WARN: deepxiv_fetch.py paper-brief failed; skipping deepen step." >&2
    python3 "$DEEPXIV_FETCHER" paper-head ARXIV_ID \
      || echo "WARN: deepxiv_fetch.py paper-head failed; skipping deepen step." >&2
    python3 "$DEEPXIV_FETCHER" paper-section ARXIV_ID "Experiments" \
      || echo "WARN: deepxiv_fetch.py paper-section failed; skipping deepen step." >&2
  else
    echo "WARN: deepxiv_fetch.py search invocation failed; D2 aggregate continues with remaining sources." >&2
  fi
fi
```

找不到 `$DEEPXIV_FETCHER` 或系统没有 `deepxiv` CLI 时，跳过该来源并继续其余来源。

**为何使用 DeepXiv？** 广泛检索后，可以先看论文简述和结构，再按需深入具体章节，减少一次性加载全文的上下文开销。

**与 arXiv、S2 去重**：

- 先按 arXiv ID 匹配，再按 DOI，最后按规范化标题。
- DeepXiv 与 arXiv 指向同一预印本时，保留一条标准论文记录，并把 `deepxiv` 记为补充来源。
- DeepXiv 与 S2 的正式发表论文重叠时，最终表格优先采用 S2 的发表场所和引用元数据，同时保留有用的 DeepXiv 章节笔记。

**Exa 检索**：仅在 `sources` 包含 `exa` 时运行，用 Exa 在广域网页搜索并提取内容。

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .aris/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
# Resolve $EXA_FETCHER (Policy D2 — warn-and-skip on missing).
EXA_FETCHER=".aris/tools/exa_search.py"
[ -f "$EXA_FETCHER" ] || EXA_FETCHER="tools/exa_search.py"
[ -f "$EXA_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && EXA_FETCHER="$ARIS_REPO/tools/exa_search.py"; }
[ -f "$EXA_FETCHER" ] || EXA_FETCHER=""

if [ -n "$EXA_FETCHER" ]; then
  # Search for research papers with highlights.
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  exa_contributed=false
  if python3 "$EXA_FETCHER" search "QUERY" --max 10 --category "research paper" --content highlights; then
    exa_contributed=true
  else
    echo "WARN: exa_search.py research-paper invocation failed; D2 aggregate continues." >&2
  fi
  # Search for broader web content (blogs, docs, news)
  if python3 "$EXA_FETCHER" search "QUERY" --max 10 --content highlights; then
    exa_contributed=true
  else
    echo "WARN: exa_search.py broad-web invocation failed; D2 aggregate continues." >&2
  fi
  [ "$exa_contributed" = "true" ] && echo "D2 contribution: exa (at least one invocation exit 0)" >&2
fi
```

找不到 `$EXA_FETCHER` 或 `exa-py` SDK 不可用时，跳过该来源并继续其余来源。

**为何使用 Exa？** 它能搜索博客、文档、新闻、公司页面等更广的网页，并随结果提取较丰富的正文内容，补充学术数据库与普通 WebSearch。

**与 arXiv、S2、DeepXiv 去重**：

- 先按 URL，再按规范化标题匹配。
- Exa 找到已由 arXiv 或 S2 收录的论文时，优先采用这些来源的结构化元数据。
- 非学术域名的博客、文档和新闻是 Exa 的补充价值。

**Gemini 检索**：仅在 `sources` 包含 `gemini` 时运行，用于扩展文献发现范围。

**优先级 1：Gemini MCP**。优先调用 `mcp__gemini-cli__ask-gemini`，并传入原文所示检索提示词：

```
mcp__gemini-cli__ask-gemini({
  prompt: 'You are a research literature scout. Search comprehensively for papers on: "QUERY"

IMPORTANT CONSTRAINTS:
1. Search from MULTIPLE angles — decompose the topic into sub-problems, aliases, neighboring tasks, and common benchmark/settings variants.
2. Prefer papers that are genuinely relevant, not merely keyword-adjacent.
3. Include top venues, journals, surveys, recent preprints, and papers with code when available.
4. Focus on papers from 2022 onward unless older foundational work is necessary.

For EACH paper found, provide ALL of the following:
- Title: [exact title]
- Authors: [full author list]
- Year: [publication year]
- Venue: [exact conference/journal name + year, or "arXiv preprint"]
- arXiv ID: [format 2401.12345, or "N/A"]
- DOI: [if available, or "N/A"]
- Code URL: [GitHub/GitLab link if available, or "No code"]
- Summary: [one-sentence core contribution]

Find at least 15 papers.',
  model: 'auto-gemini-3'
})
```

**优先级 2：Gemini CLI 回退**。MCP 不可用时，使用 Bash 执行 `gemini -p "...same prompt..." 2>/dev/null`，超时设为 120 秒。

两者都不可用时，跳过该来源，继续其他来源。

**为何使用 Gemini？** 它会把主题拆解为子问题，探索别名、相邻任务和评测设置的变体，寻找单纯关键词查询可能漏掉的论文。

**与 arXiv、S2、DeepXiv、Exa 去重**：

- 先匹配 arXiv ID，再匹配 DOI，最后匹配规范化标题。
- 与 S2 重叠时，引用数和发表场所优先采用 S2 数据；与 arXiv 重叠时，优先采用 arXiv 的结构化元数据。
- Gemini 的独特作用是发现其他关键词检索来源未找到的论文。
- **不要采用 Gemini 报告的引用数**；需要引用数时使用 S2。

**OpenAlex 检索**：仅在 `sources` 包含 `openalex` 时运行，用其 API 获取更全面的学术元数据。

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .aris/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
# Resolve $OPENALEX_FETCHER (Policy D2 — warn-and-skip on missing).
OPENALEX_FETCHER=".aris/tools/openalex_fetch.py"
[ -f "$OPENALEX_FETCHER" ] || OPENALEX_FETCHER="tools/openalex_fetch.py"
[ -f "$OPENALEX_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && OPENALEX_FETCHER="$ARIS_REPO/tools/openalex_fetch.py"; }
[ -f "$OPENALEX_FETCHER" ] || OPENALEX_FETCHER=""

# Preflight: skip OpenAlex silently if the helper is unresolved OR the
# `requests` Python package is missing. Both checks must pass before
# the script is invoked, so users without `requests` installed never see
# a stack trace from a default `/research-lit` run.
if [ -z "$OPENALEX_FETCHER" ] || ! python3 -c "import requests" >/dev/null 2>&1; then
  echo "OpenAlex source not available (openalex_fetch.py unresolved or 'requests' module missing); skipping." >&2
else
  # Search for papers with comprehensive metadata.
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  if python3 "$OPENALEX_FETCHER" search "QUERY" --max 10 \
      --year "2022-" \
      --type article \
      --sort relevance; then
    echo "D2 contribution: openalex (helper invocation exit 0)" >&2
  else
    echo "WARN: openalex_fetch.py invocation failed; D2 aggregate continues with remaining sources." >&2
  fi
fi
```

找不到 `openalex_fetch.py` 或缺少 `requests` 模块时，跳过该来源并继续其余来源。

**为何使用 OpenAlex？** 它提供无需 API 密钥的开放引用图谱、作者机构、资助信息和跨学科主题元数据。

**与 arXiv、S2、DeepXiv、Exa、Gemini 去重**：

- 优先按 DOI 匹配，再按 arXiv ID，最后按规范化标题。
- 与 S2 重叠时，引用数和 CS/AI 论文的发表场所优先采用 S2；机构和资助信息采用 OpenAlex，合并成更完整的记录。
- 与 arXiv 重叠时，保留 arXiv 的 PDF 链接和论文元数据，同时补充 OpenAlex 的引用、机构信息。
- OpenAlex 的独特价值是机构、资助、主题分类及跨学科覆盖。

**D2 聚合的最终检查**（参见集成规范第 2 节）：

编排模型读取各 Bash 代码块的 `D2 contribution: <name>` 日志，在上下文中维护参与来源列表。此外：

- 步骤 0a 返回非空 Zotero 结果时，计入 `zotero`。
- 步骤 0b 返回非空 Obsidian 结果时，计入 `obsidian`。
- 步骤 0c 找到至少一篇相关本地 PDF 时，计入 `local`。
- WebSearch 被请求且实际调用时，计入 `web`。`— sources: all` 只包含默认开启的 Zotero、Obsidian、本地 PDF、WebSearch；Semantic Scholar、DeepXiv、Exa、Gemini、OpenAlex 必须显式添加。WebSearch 即使返回空结果，只要实际调用也计入。
- Gemini MCP 或 CLI 至少返回一篇论文时，计入 `gemini`。

如果参与来源列表为空，报告：

> **错误：D2 聚合为空。** 所有被请求的来源都未找到、未调用、调用失败，或（对于 MCP、本地 PDF、Gemini）未返回可用结果。请扩展 `— sources:` 列表，例如 `web, local`，或检查脚本路径及 SDK 安装状态。

随后在步骤 1.5 前停止。若有参与来源，向用户报告列表，例如 `Sources contributed: arxiv, semantic_scholar, web`，再继续。

**可选 PDF 下载**：仅在 `ARXIV_DOWNLOAD = true` 时执行。完成各来源检索并按相关性排序后：

```bash
# Re-resolve $ARXIV_FETCHER (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .aris/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
ARXIV_FETCHER=".aris/tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER="tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && ARXIV_FETCHER="$ARIS_REPO/tools/arxiv_fetch.py"; }
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER=""

# Download top N most relevant arXiv papers; skip silently if helper unresolved.
[ -n "$ARXIV_FETCHER" ] && python3 "$ARXIV_FETCHER" download ARXIV_ID --dir papers/
```

- 只下载相关性排名前 ARXIV_MAX_DOWNLOAD 的 arXiv 论文。
- 跳过本地已有的论文。
- 两次下载间隔 1 秒，以控制请求速率。
- 核实每个 PDF 大于 10 KB。

### 步骤 1.5：核验候选论文（强制执行，防止虚构引文）

分析前，对步骤 0a–1 收集的**全部**候选论文进行检索前核验，筛出模型虚构的 arXiv ID、DOI 或标题。标准脚本为 `verify_papers.py`，按[集成规范第 2 节](../../aris/skills/shared-references/integration-contract.md)定位；它采用 D1 策略，主脚本不可用时提供带明确标记的降级结果。若本机找不到脚本，skill 会生成替代的 `verified_papers.json`，给所有候选论文标记 `[UNVERIFIED]`，让后续分析继续进行，同时保留可审查的不确定性。

```bash
# 1. Resolve $VERIFY_PAPERS via the canonical strict-safe chain (§2).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .aris/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
VERIFY_PAPERS=".aris/tools/verify_papers.py"
[ -f "$VERIFY_PAPERS" ] || VERIFY_PAPERS="tools/verify_papers.py"
[ -f "$VERIFY_PAPERS" ] || { [ -n "${ARIS_REPO:-}" ] && VERIFY_PAPERS="$ARIS_REPO/tools/verify_papers.py"; }
[ -f "$VERIFY_PAPERS" ] || VERIFY_PAPERS=""

# 2. Emit candidates as JSON. Verification scratch lives under .aris/
#    (NOT under research-wiki/ — Step 6's wiki ingest predicate is
#    "research-wiki/ exists", and we must not trip it from Step 1.5).
mkdir -p .aris/verify-papers
cat > .aris/verify-papers/candidate_papers.json <<'JSON'
[
  {"id": "p1", "arxiv_id": "2307.03172", "doi": null, "title": "Lost in the Middle"},
  {"id": "p2", "arxiv_id": null, "doi": "10.1145/...", "title": "..."},
  {"id": "p3", "arxiv_id": null, "doi": null, "title": "Some Paper Title"}
]
JSON

# 3. Run 3-layer verification (arXiv batch → CrossRef → Semantic Scholar fuzzy).
#    Policy D1: when the helper is unresolved OR its invocation fails, emit
#    a degraded verified set tagging everything [UNVERIFIED] so the user
#    can audit search quality. If python3 itself is missing, we BLOCK
#    rather than hand-roll JSON in shell.
verify_ok=false
if [ -n "$VERIFY_PAPERS" ]; then
  if python3 "$VERIFY_PAPERS" \
        --input  .aris/verify-papers/candidate_papers.json \
        --output .aris/verify-papers/verified_papers.json; then
    verify_ok=true
  else
    echo "WARN: verify_papers.py invocation failed (resolved at $VERIFY_PAPERS); falling back to [UNVERIFIED] tagging." >&2
  fi
else
  echo "WARN: verify_papers.py not resolved at .aris/tools/, tools/, \$ARIS_REPO/tools/, or via ~/.aris/repo." >&2
  echo "      Fix: rerun bash tools/install_aris.sh or smart_update.sh (refreshes ~/.aris/repo), export ARIS_REPO, or copy the helper to tools/." >&2
fi
if [ "$verify_ok" = "false" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 unavailable; cannot emit fallback verified_papers.json." >&2
    echo "       Status: BLOCKED. Install python3 or restore the helper to proceed." >&2
    exit 1
  fi
  echo "      Emitting unverified candidate set with [UNVERIFIED] tags." >&2
  python3 - <<'PY'
import json
cands = json.load(open('.aris/verify-papers/candidate_papers.json'))
out = {
  'verdict': 'WARN',
  'reason_code': 'verify_papers_unavailable',
  'summary': 'verify_papers.py helper unresolved or invocation failed; all candidates tagged [UNVERIFIED] for audit visibility.',
  'papers': [dict(p, status='unverified', method='none') for p in cands],
}
with open('.aris/verify-papers/verified_papers.json', 'w') as f:
  json.dump(out, f, indent=2)
PY
fi

# 4. Read verdict + per-paper status from .aris/verify-papers/verified_papers.json;
#    surface warnings to the user.
```

**强制输出规则**（完整约定见[引文规范中的“检索前核验协议”](../../aris/skills/shared-references/citation-discipline.md)）：

- 在分析列表中标出每篇论文的状态：`✅ verified (via arxiv|crossref|s2)`、`⚠️ UNVERIFIED (reason)` 或 `… verify_pending`。
- **保留所有未核实的论文**，明确加上 `[UNVERIFIED]`，使用户能够检查检索质量。
- 不得凭记忆编造 DOI 或 arXiv ID。未知字段在 `candidate_papers.json` 中设为 `null`，脚本会继续尝试标题搜索。
- 若脚本返回含 `high_hallucination_rate` 的 `WARN`，原样向用户显示警告，并建议用更窄的查询重新搜索。
- 对标记为 `verify_pending` 的论文，保持待核验状态，并在下次会话重试。

可选：在 shell 中设置 `ARIS_VERIFY_EMAIL=you@institution.edu`，以使用 Crossref 较宽松的请求额度。

### 步骤 2：逐篇分析

> **按运行能力分派任务。** 每篇论文的字段提取彼此独立，可以并行。第 1 级（Workflow）：每篇或每小批论文交给一个 Claude 子 agent。第 2 级（有 Agent 工具但无 Workflow）：通过 Agent 工具分派同样的任务。第 3 级：顺序处理。各任务按[并行分派规范](../../aris/skills/shared-references/fan-out-pattern.md)返回提取结果：`{shard_id: "<论文或批次 ID>", entries: [{dedup_key: "<步骤 1.5 已分配的标准 arXiv ID / DOI / 标题哈希>", problem, method, results, relevance, source, verification_status}]}`。
>
> 此处的“裁判”是步骤 1.5 的确定性 `verify_papers.py` 核验门槛，而非另一个模型，因此符合[验收门槛规范](../../aris/skills/shared-references/acceptance-gate.md)的跨模型规则。各子任务只提取原文信息和核验状态，不决定论文是否算数，也不因论文状态并非 `verified` 而丢弃它。步骤 3 的主题归纳与缺口分析属于解释性综合，不承担论文身份的准入判定。

对 `.aris/verify-papers/verified_papers.json` 中的**每一篇**论文，包括 `verified`、`unverified`、`verify_pending` 和 `error`，提取：

- **问题**：论文针对什么研究空白？
- **方法**：核心技术贡献是什么？用 1–2 句话概括。
- **结果**：关键数据或主张是什么？
- **相关性**：与我们的研究有何关系？
- **来源**：从 Zotero、Obsidian、本地还是网页发现？以区分用户已有资料与新发现。
- **核验状态**，取以下之一：
  - `✅ verified (via arxiv|crossref|s2)`：已核实
  - `⚠️ UNVERIFIED (verification unavailable: helper unresolved or invocation failed)`：核验工具不可用或调用失败
  - `⚠️ UNVERIFIED (searched: not found in any source)`：查询后未查到
  - `… VERIFY_PENDING (transient API failure — retry next session)`：API 暂时故障，下次重试
  - `❌ ERROR (malformed input: no arxiv, no DOI, no title)`：输入缺少所有可查询字段

在分析表中展示状态；不能因为状态不是 `verified` 就悄悄删除论文。

### 步骤 3：综合

- 按方法或研究主题将论文分组。
- 识别领域内的共识与分歧。
- 找出我们可能切入的研究空白。
- 如果有 Obsidian 笔记，将用户自己的见解纳入综合分析。

### 步骤 4：输出

输出结构化文献表：

```
| Paper | Venue | Method | Key Result | Relevance to Us | Source |
|-------|-------|--------|------------|-----------------|--------|
```

再用 3–5 段文字概述该方向的研究格局。

如果已从 Zotero 导出 BibTeX，附上 `references.bib` 片段，方便写论文时直接使用。

### 步骤 5：保存（用户要求时）

- 把论文 PDF 保存到 `literature/` 或 `papers/`。
- 更新项目记忆中的相关工作笔记。
- 如果有 Obsidian，可选择在笔记库中建立文献综述笔记。

> **组合模式**：如果调用参数包含 `— composed: <canonical-report-path>`（如由 `/idea-discovery` 传入），不要另写独立的研究格局 `.md`。将文献表和文字概述返回给编排器，由它并入主报告的 “Literature Landscape” 部分。报告只链接保存的 PDF 或 `references.bib`，不重复存储研究格局。步骤 6 的 research-wiki 写入照常执行，因为 wiki 是独立的持久知识库。**默认未提供 `— composed:` 时，采用独立模式，按此文件规定输出。** 不能仅因磁盘上已有报告文件就推断为组合模式。完整规则见[输出组合规范](../../aris/skills/shared-references/output-composition.md)。

### 步骤 6：更新 Research Wiki

当 `research-wiki/` 目录存在时，**必须执行**此步骤；目录不存在时直接跳过。写入逻辑由 `tools/research_wiki.py` 实现，遵守[集成规范](../../aris/skills/shared-references/integration-contract.md)，而非在本文档中重新实现。

目录存在时，按[wiki 脚本定位规范](../../aris/skills/shared-references/wiki-helper-resolution.md)查找 `$WIKI_SCRIPT`。使用变体 B：找不到则警告并跳过。

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
ARIS_REPO="${ARIS_REPO:-$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .aris/installed-skills.txt 2>/dev/null)}"
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.aris/repo" ]; then
  ARIS_REPO=$(cat "$HOME/.aris/repo" 2>/dev/null) || true
fi
WIKI_SCRIPT=".aris/tools/research_wiki.py"
[ -f "$WIKI_SCRIPT" ] || WIKI_SCRIPT="tools/research_wiki.py"
[ -f "$WIKI_SCRIPT" ] || { [ -n "${ARIS_REPO:-}" ] && WIKI_SCRIPT="$ARIS_REPO/tools/research_wiki.py"; }
[ -f "$WIKI_SCRIPT" ] || {
  echo "WARN: research_wiki.py not found; literature synthesis will be reported but wiki ingest will be skipped. Fix: bash tools/install_aris.sh or smart_update.sh (refreshes ~/.aris/repo), export ARIS_REPO, or cp <ARIS-repo>/tools/research_wiki.py tools/." >&2
  WIKI_SCRIPT=""
}
```

```
📋 Research Wiki ingest (runs once, at end of research-lit):
   [ ] 1. Predicate: `research-wiki/` exists? If no, skip this step.
   [ ] 2. If $WIKI_SCRIPT empty (helper unreachable), skip the rest of this step
          (the warning above already explains why).
   [ ] 3. For each of the top 8–12 relevant papers (arxiv IDs collected above):
          python3 "$WIKI_SCRIPT" ingest_paper research-wiki/ \
              --arxiv-id <id> [--thesis "<one-line>"] [--tags <t1>,<t2>]
   [ ] 4. For each explicit relationship to an existing wiki entity,
          add an edge:
          python3 "$WIKI_SCRIPT" add_edge research-wiki/ \
              --from "paper:<slug>" --to "<target_node_id>" \
              --type <extends|contradicts|addresses_gap|inspired_by|...> \
              --evidence "<one-sentence quote or reasoning>"
   [ ] 5. Confirm papers/<slug>.md files were created (helper prints
          "Paper ingested: ..."); if any failed with a network error,
          retry or fall back to the --title/--authors/--year manual form.
```

`ingest_paper` 一次调用会处理 slug 生成、arXiv 元数据获取、按 arXiv ID 去重、论文页面渲染、`index.md` 与 `query_pack.md` 重建及日志追加。**不要手工编写 `papers/<slug>.md`。** 如果脚本不可用（例如离线或 `$WIKI_SCRIPT` 为空），记录缺口，后续可用 `/research-wiki sync --arxiv-ids …` 补录。

对于无 arXiv 版本的来源，例如只有 Semantic Scholar 收录的 IEEE/ACM 期刊论文或博客，改为传入人工整理的元数据：

```bash
python3 "$WIKI_SCRIPT" ingest_paper research-wiki/ \
    --title "<full title>" --authors "A, B, C" --year <yyyy> \
    --venue "<venue>" [--external-id-doi "<doi>"] [--thesis "..."]
```

## 核心规则

- 引用论文时始终包含作者、年份和发表场所。
- 区分同行评审论文与预印本。
- 如实说明每篇论文的局限。
- 指明论文是直接竞争于我们的方案，还是支持我们的方案。
- **不要因未配置 MCP 服务器而使整个流程失败**；按顺序回退到其他来源。
- Zotero、Obsidian MCP 工具的实际名称可能随配置而变化，例如 `mcp__zotero__search` 或 `mcp__zotero-mcp__search_items`；尝试常见命名并按实际配置调整。
