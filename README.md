# paper-pipline

文献从"杂乱清单 → 抓 PDF → 进 Zotero → MinerU 转 markdown"的端到端工具集。两个独立但通过 Zotero 衔接的项目放在同一仓库:

```
paper-pipline/
├── paper-fetcher/      # (2) 杂乱清单 → 清洗 → 按 publisher 抓 PDF → 推 Zotero
└── zotero-mineru/      # (3) Zotero 里的 PDF → MinerU → markdown / Zotero note
```

第三块"MinerU 本体"是独立的 conda env(`mineru`),装好就跑,不在这个仓库里。

## 流程图

```
┌────────────────────────┐
│  messy paperlist.txt   │
└──────────┬─────────────┘
           │  paper-fetcher/clean_list.py
           ▼
┌────────────────────────┐
│ paperlist_clean.txt    │
│ paperlist_review.json  │  ← AI 处理 review,写 decisions.json
└──────────┬─────────────┘
           │  paper-fetcher/run.py  (并行 IEEE / ACM / SD)
           ▼
┌────────────────────────┐
│ output/{ieee,acm,sd}/  │
│        *.pdf           │
└──────────┬─────────────┘
           │  paper-fetcher/import_to_zotero.py
           ▼
┌────────────────────────┐
│  Zotero 桌面 app       │
│  自动识别元数据         │
│  PDF 落 Zotero/storage │
└──────────┬─────────────┘
           │  zotero-mineru/batch.py (扫 Zotero storage,过 MinerU)
           ▼
┌────────────────────────┐
│  *.md / 图片 / 索引     │
│  zotero-mineru-mirror/ │
└────────────────────────┘
```

## 两个项目各自的 README

- [paper-fetcher/README.md](paper-fetcher/README.md) — 抓取部分的细节
- [paper-fetcher/AI_WORKFLOW.md](paper-fetcher/AI_WORKFLOW.md) — AI 决策规则(给后续 Sonnet/Haiku 看)
- (zotero-mineru 的 README 待补 — 看代码 `batch.py` `watcher.py` `common.py` 入口)

## 新机器从零搭建

```powershell
git clone https://github.com/yfh667/paper-pipline.git C:\paper-pipline
cd C:\paper-pipline

# Python 端(共用一个 conda env)
conda create -n mineru python=3.11 -y
conda activate mineru
pip install requests undetected-chromedriver pyzotero playwright httpx pypdf
# MinerU 本体(zotero-mineru 调用)
pip install mineru
# 浏览器二进制(playwright 不一定要用,但装上保险)
playwright install chromium

# Node 端(paper-fetcher 的 SD handler 用)
cd paper-fetcher\sd-fetch-node
npm install
cd ..\..

# Zotero 桌面 app
# 1. 装 Zotero (zotero.org/download)
# 2. 登录,开启 Edit → Preferences → Advanced → "Allow other applications to communicate with Zotero"
# 3. 编辑 zotero-mineru\config.json,把 zotero_library_id / zotero_storage 改成你的

# Claude Code skill(可选,用 paper-fetch skill 自动跑全流程)
mkdir $env:USERPROFILE\.claude\skills\paper-fetch
copy <从仓库或现有机器的 ~/.claude/skills/paper-fetch/SKILL.md>  # 略
```

## 常见命令

```powershell
# 跑一遍 paper-fetcher(只需要 raw txt 丢到 paper-fetcher\input\)
cd paper-pipline\paper-fetcher
python clean_list.py input\my_list.txt
# 然后:AI 处理 output\paperlist_review.json 写 decisions.json
python apply_decisions.py output\decisions.json
python run.py output\paperlist_clean.txt --skip-existing
python import_to_zotero.py

# 跑 zotero-mineru(扫 Zotero storage,把新 PDF 过 MinerU)
cd ..\zotero-mineru
python batch.py
# 或后台 watcher 模式
.\start-watcher.ps1
```

## 不提交什么

- `paper-fetcher/output/{ieee,acm,sd}/` 下的 PDF(可能有版权,而且太大)
- `paper-fetcher/input/*.txt`(你的私有研究方向)
- `node_modules/`(`npm install` 重建)
- `state.json` / `logs/`(运行时,机器相关)
- `__pycache__/`

详见 [.gitignore](.gitignore)。
