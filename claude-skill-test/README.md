# Claude Code 测试项目

这个目录用于试运行 `literature-landscape`。`.claude/skills/literature-landscape` 链接到原始 skill，脚本也随 skill 一起加载；修改原始文件后，这里会直接使用新版本。个人 API 配置可放在此测试项目的 `.env`，或使用环境变量。

在此目录运行：

```bash
python3 .claude/skills/literature-landscape/scripts/search_sources.py --doctor
claude
```

进入 Claude Code 后，先输入 `/skills` 确认能看到 `literature-landscape`，再输入：

```text
/literature-landscape 我想了解边缘设备上的大语言模型推理，请先给我一份附论文原始链接的文献地图。
```

`/skills` 中若未显示，退出 Claude Code 后确认当前目录是本测试项目，再重新启动。
