# Scholar Workflows

这个仓库集中维护可单独安装的科研 skills。参考了本工作区的 ARIS `skills/<name>/SKILL.md` 布局，以及 Agent Skills 的目录规范。每个 skill 的运行依赖都放在自己的目录内，安装单个 skill 后也能使用。

```text
scholar-workflows/
├── skills/
│   └── literature-landscape/
│       ├── SKILL.md                 技能入口：YAML name、description 和使用说明
│       └── scripts/
│           └── search_sources.py   该技能专用的只读检索脚本
├── docs/                      维护者的调研材料，不随单个 skill 安装
└── README.md                  技能目录与安装方法
```

## 已有技能

| Skill | 用途 | 额外配置 |
| --- | --- | --- |
| [literature-landscape](skills/literature-landscape/SKILL.md) | 多来源检索、核验论文并绘制文献地图 | 可选的 Zotero、Semantic Scholar、DeepXiv、Exa |

`literature-landscape` 的检索脚本使用 Python 标准库；DeepXiv 来源需要额外安装 `deepxiv-sdk`。按需在**运行脚本的项目目录**设置环境变量，或将 [`.env.example`](.env.example) 复制为该项目的 `.env`。不要提交含密钥的 `.env`。

```bash
python3 skills/literature-landscape/scripts/search_sources.py --doctor
python3 skills/literature-landscape/scripts/search_sources.py "research topic in English" --limit 8
```

## 安装

仓库已经发布。在要使用技能的项目目录中运行：

```bash
npx skills add Nullion2021/scholar-workflows --list
npx skills add Nullion2021/scholar-workflows --skill literature-landscape -a codex
```

Claude Code 用户把 `-a codex` 改为 `-a claude-code`；要安装到个人全局目录，在安装命令末尾加 `-g`。

如果已经克隆了本仓库，并且当前终端位于仓库根目录，也可以从本地发现技能：

```bash
npx skills add . --list
```

私有仓库也可通过相同命令安装，但运行命令的机器需要有对应的 Git 凭据。

## 后续添加技能

1. 新建 `skills/<skill-name>/SKILL.md`，在 YAML 头部填写与目录一致的 `name` 和明确的 `description`。
2. 把这个 skill 专用的脚本放在其 `scripts/`，按需加入 `references/` 或 `assets/`。让 `SKILL.md` 只引用技能目录内的可安装文件或公开文档。
3. 在上表登记用途；运行 `npx skills add . --list` 确认新 skill 可被发现，再从一个临时项目安装验证。

目录命名使用小写字母、数字和连字符。维护材料放在仓库级 `docs/`；运行时必需的资源必须留在对应 skill 目录内。

## 参考材料

- [Agent Skills 目录规范](https://agentskills.io/specification)
- [Skills CLI 安装与发现规则](https://github.com/vercel-labs/skills#skill-discovery)
- [Claude Code 本地试用](claude-skill-test/README.md)
- [ARIS research-lit 中文译文](docs/research-lit.zh-CN.md)

`docs/` 中的 ARIS 译文和架构材料依据 [ARIS 原项目](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)整理；其 [MIT 许可及原作者声明](docs/ARIS-LICENSE)随文档保留。
