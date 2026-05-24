# paper-fetcher

按 publisher 分流抓 PDF 的小框架。三个 handler 并行(不同 publisher),每个 handler 内部串行(同一 publisher 间隔 60s)。

## 目录结构

```
paper-fetcher/
├── run.py              # CLI 入口
├── core.py             # 异步调度
├── handlers/
│   ├── base.py         # Job + 抽象基类
│   ├── ieee.py         # 纯 requests + stamp.jsp
│   ├── acm.py          # undetected-chromedriver(过 Cloudflare)
│   └── elsevier.py     # subprocess 调下面的 Node 脚本
├── sd-fetch-node/      # SD 用的 Node 脚本
│   ├── fetch-one.mjs   # 主脚本(puppeteer-extra + stealth + 打印 PDF)
│   ├── package.json
│   └── node_modules/   # 已 npm install
└── output/             # 运行时产物
    ├── ieee/           # IEEE PDF 落点
    ├── acm/            # ACM PDF 落点
    ├── sd/             # ScienceDirect PDF 落点
    ├── manual/needs_manual.txt   # 不在三大社的条目,留给用户手动处理
    ├── _acm_dl_tmp/    # ACM 下载暂存(自动清理)
    └── logs/run-YYYYMMDD-HHMMSS.log
```

## 输入格式

每行一条:

```
[ieee] Paper Title Here  (doi=10.1109/xxx.yyyy.zzzz)
[acm] Another Title  (doi=10.1145/xxxxxxx.yyyyyyy)
[elsevier] SD Title  (doi=10.1016/j.xxx.2025.123456)
[spie] 不在三大社  (doi=10.1117/...)        # 自动转发到 needs_manual.txt
[no-doi] 缺 DOI 的标题  (doi=)             # 自动转发到 needs_manual.txt
```

`[ieee]` / `[acm]` / `[elsevier]` 之外的所有 tag,以及 doi= 为空的行,都会 dump 到 `output/manual/needs_manual.txt` 留给手动处理。

## 完整流程

```
原始 messy 笔记 (.txt)
        │
        │  python clean_list.py messy.txt
        ▼
output/paperlist_clean.txt   <-- 可直接喂给 run.py
output/paperlist_review.json <-- 机器拿不准的(AI / 人工解决)
        │
        │  python run.py output/paperlist_clean.txt --skip-existing
        ▼
output/{ieee,acm,sd}/*.pdf
output/manual/needs_manual.txt  <-- 不属于三大社的条目
```

## 清洗步骤(`clean_list.py`)

输入是杂乱笔记(中英混排、URL、注释都行):

```powershell
& 'C:\ProgramData\miniconda3\envs\mineru\python.exe' clean_list.py C:\papers\paperlist.txt
```

脚本干这些(全自动,不用 AI):
1. 按段落切,逐段抽 URL / DOI 字面值 / 候选英文标题
2. 去除 markdown 装饰、中文注释尾巴、噪音命令行
3. 找到的 DOI → CrossRef 反查标题、发布商
4. 找到的标题 → CrossRef 搜索 → 高置信度匹配的直接落到 clean.txt
5. CrossRef 多个相近候选 / 完全没匹配 / 未知域名 URL → 落到 `paperlist_review.json`

CrossRef 调用每次 sleep 1s(polite pool 规范)。100 个标题大概 2 分钟。

## AI 介入

`paperlist_review.json` 是给 AI / 用户的工作区,典型条目:

```json
{
  "kind": "title",
  "title": "CMAP: Certificate-less MQTT-based Authentication Protocol for Medical IoT",
  "candidates": [
    {"doi": "10.1109/access.2026.3684371", "title": "CMAP: Certificateless...", "score": 60.2},
    {"doi": "10.1007/s13369-023-08047-6", "title": "CMAP-IoT: Chaotic Map...", "score": 37.3}
  ]
}
```

AI 看了上下文就能选第一个,append 一行 `[ieee] ... (doi=10.1109/access.2026.3684371)` 到 `paperlist_clean.txt`。

## 用法

```powershell
cd C:\paper-fetcher
& 'C:\ProgramData\miniconda3\envs\mineru\python.exe' run.py path\to\list.txt

# 已经下过的不重抓
& 'C:\ProgramData\miniconda3\envs\mineru\python.exe' run.py path\to\list.txt --skip-existing
```

完整运行时间(参考):60s 间隔下,每篇 ~70-100s,9 篇约 12 分钟。

## 依赖

- **Python**(用 mineru conda env):`requests`、`undetected-chromedriver`
- **Node.js**:`puppeteer-core`、`puppeteer-extra`、`puppeteer-extra-plugin-stealth`(已在 sd-fetch-node/node_modules/)
- **System Chrome**:`C:\Program Files\Google\Chrome\Application\chrome.exe`(Node 脚本调它)

## 已知行为

- **IEEE** 偶尔会被 Akamai 返回 APM HTML 挑战页,handler 会自动 sleep 90s + 换 session 重试一次
- **ACM** 偶尔 Cloudflare 不放行,handler 会自动重启 Chrome driver + sleep 90s 重试一次
- **SD** 太密的请求 → SD WAF 拉黑 IP(临时,30-60min 自解)。60s 间隔基本不会触发
- **TechRxiv preprint**(DOI 10.36227/...) 不在 ieeexplore.ieee.org 上,IEEE handler 会报 "no arnumber"
- 三个 handler 进程 / browser 互相独立,日志合在一个文件里
