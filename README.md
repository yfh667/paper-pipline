# paper-pipline

> 学术文献从"杂乱清单"到"结构化 markdown"的全自动流水线。一个人 / 一个 AI 维护得了的小工具集合,不是企业级框架。

## 1. 这个 repo 是干嘛的

你研究的时候日常会面对这种局面:

- 一个 txt(或者剪贴板里的笔记)里堆了几十条乱七八糟的"想读的论文"——有的是英文标题、有的带中文备注、有的是 URL、有的甚至是同事发来的乱码
- 你想把这些都搞到 Zotero 里、统一管理
- 然后还想把每篇 PDF 喂给 MinerU 转成 markdown,这样可以让 AI(或者你自己)按章节快速消化

这个 repo 把上面三件事串起来:

```
┌─────────────────────┐
│  杂乱 paperlist.txt │
└──────────┬──────────┘
           │  paper-fetcher: 清洗 / 抓 PDF / 推 Zotero
           ▼
┌─────────────────────┐
│   Zotero 桌面 app   │  ← 元数据自动识别(Zotero 内建能力,我们不写)
│   + PDF 附件         │
└──────────┬──────────┘
           │  zotero-mineru: 扫 Zotero storage 跑 MinerU
           ▼
┌─────────────────────┐
│   每篇 PDF → MD     │
│ + 图 + 双链回 Zotero │
└─────────────────────┘
```

两个子项目都是 Python 为主(+ paper-fetcher 里 ScienceDirect 专门用 Node 因为 Python stealth 库被 SD 反爬识破)。

## 2. 目录结构

```
paper-pipline/
├── README.md                    ← 这份文档
├── .gitignore
├── paper-fetcher/               ← 子项目 A:从杂乱清单到 Zotero
│   ├── README.md                  各家 publisher handler 的设计细节
│   ├── AI_WORKFLOW.md             给清洗步骤里 AI 角色的"操作手册"
│   ├── run.py                     CLI 主入口(并行抓 PDF)
│   ├── core.py                    async 调度器
│   ├── clean_list.py              杂乱 txt → 结构化 + CrossRef 查 DOI
│   ├── apply_decisions.py         AI 给的 decisions.json → 合并到 clean.txt
│   ├── import_to_zotero.py        把 PDF 灌进本地 Zotero(端口 23119)
│   ├── handlers/                  每个 publisher 一个抓取实现
│   │   ├── base.py                  Job / PublisherHandler 抽象
│   │   ├── ieee.py                  IEEE Xplore:requests + stamp.jsp
│   │   ├── acm.py                   ACM DL:undetected-chromedriver(过 CF)
│   │   └── elsevier.py              ScienceDirect:subprocess 调 Node 脚本
│   ├── sd-fetch-node/             SD 用的 Node 套件(puppeteer-extra + stealth)
│   │   ├── fetch-one.mjs            主脚本:打开 → 等正文 → 剥浮层 → 打印 PDF
│   │   ├── package.json
│   │   └── (node_modules/ 被 .gitignore 排除,clone 后 npm install)
│   ├── input/                     ★ 用户把杂乱 txt 丢这里 ★
│   └── output/                    所有产物(被 .gitignore 排除大部分)
│       ├── paperlist_clean.txt
│       ├── paperlist_review.json
│       ├── decisions.json
│       ├── {ieee,acm,sd}/         按 publisher 分文件夹的 PDF
│       ├── manual/needs_manual.txt
│       └── logs/run-*.log
│
└── zotero-mineru/               ← 子项目 B:Zotero PDF → MinerU markdown
    ├── batch.py                   一次性扫 + 转
    ├── watcher.py                 后台守护,Zotero 新 PDF 自动转
    ├── common.py                  转换/状态/日志的共享逻辑
    ├── config.json                Zotero storage 路径 / mineru exe 等
    ├── audit-orphans.py           找"有 MD 但 Zotero 没条目"的孤儿
    ├── audit-trash.py             找进了 trash 但 MD 还在的
    ├── build_index.py             生成全库 markdown 索引
    ├── status.py / status.ps1     看进度
    ├── export_md.py               把 MD 导出到任意位置
    ├── start-watcher.ps1          启动 watcher
    ├── zotero-action-attach-md.js  Zotero 内 Actions 插件脚本:把 MD attach 到条目
    └── zotero-action-md-to-note.js Zotero 内插件脚本:MD → Zotero note
```

注意:`paper-fetcher/input/` 和 `paper-fetcher/output/`(以及它们的子目录里的 PDF)是机器本地数据,**不会 push 到 GitHub**(.gitignore 排除了)。只有结构占位 `.gitkeep` 在 repo 里。

## 3. 完整流程图(关键步骤的输入输出)

```
              [USER]
                │ 把 messy.txt 丢到 paper-fetcher/input/
                ▼
   ┌──────────────────────────────────┐
   │  python clean_list.py messy.txt  │
   └─────────────────┬────────────────┘
                     │
            ┌────────┴────────┐
            ▼                 ▼
   paperlist_clean.txt  paperlist_review.json
      (机器搞定的)       (机器拿不准的 ~20-30 条)
                              │
                              ▼
              [AI / 人 看 review.json,写 decisions.json]
              规则见 paper-fetcher/AI_WORKFLOW.md
                              │
                              ▼
   ┌──────────────────────────────────────────┐
   │ python apply_decisions.py decisions.json │
   └─────────────────┬────────────────────────┘
                     │
                     ▼
        paperlist_clean.txt(更全) + paperlist_review.json(缩到只剩 manual)
                              │
                              ▼
   ┌──────────────────────────────────────────────────────┐
   │ python run.py paperlist_clean.txt --skip-existing    │
   │   (内部并行三个 publisher,各 60s 间隔避免反爬)        │
   └─────────────────┬────────────────────────────────────┘
                     │
            ┌────────┼────────┐
            ▼        ▼        ▼
       output/ieee  output/acm  output/sd     ← PDF 落到这里
                              │
                              ▼
   ┌──────────────────────────────────────────┐
   │ python import_to_zotero.py               │
   │   (要求 Zotero desktop 在跑;            │
   │    建议先在 UI 里建并选中目标 collection) │
   └─────────────────┬────────────────────────┘
                     │
                     ▼
         Zotero 桌面 app(本地 API 端口 23119)
         自动:PDF → 识别元数据 → conferencePaper/journalArticle
         PDF 物理路径:C:\Users\<you>\Zotero\storage\<key>\*.pdf
                              │
                              ▼
   ┌─────────────────────────────────────────────────┐
   │ cd zotero-mineru                                 │
   │ python batch.py        # 一次性                   │
   │ # 或 .\start-watcher.ps1   # 后台守护             │
   └─────────────────┬───────────────────────────────┘
                     │
                     ▼
       <mirror_dir>/<key>/{paper.md, images/...}
       (后续可被任何 AI / 人按 markdown 消费)
```

## 4. 从零搭建(新机器)

### 4.1 依赖

| 类别 | 工具 | 版本 | 用途 |
|------|------|------|------|
| Python | conda env `mineru` | 3.11+ | 两个子项目的运行时 |
| Python pkg | `requests` | latest | IEEE handler / Zotero import |
| Python pkg | `undetected-chromedriver` | latest | ACM handler(过 Cloudflare) |
| Python pkg | `pyzotero` | latest | (可选,目前 import 直接走 HTTP) |
| Python pkg | `playwright` | latest | (老的 Python elsevier handler 残留依赖,可不装) |
| Python pkg | `pypdf` | latest | zotero-mineru 算页数 |
| Python pkg | `mineru` | latest | MinerU 本体 |
| Node | Node.js | ≥ 18 | SD handler 的 puppeteer-extra |
| Node pkg | (在 sd-fetch-node/) | locked | `npm install` 装齐 |
| 浏览器 | Google Chrome | latest | Node puppeteer 调它(不下载 Chromium) |
| App | Zotero desktop | ≥ 7 | 7+ 后才有完整 local API |
| App 设置 | "允许其他应用与 Zotero 通信" | 开 | Edit → Preferences → Advanced |

### 4.2 一键安装(PowerShell)

```powershell
# 1) 克隆代码
git clone https://github.com/yfh667/paper-pipline.git C:\paper-pipline
cd C:\paper-pipline

# 2) Python 环境
conda create -n mineru python=3.11 -y
conda activate mineru
pip install requests undetected-chromedriver pyzotero pypdf mineru httpx

# 3) Node 依赖
cd paper-fetcher\sd-fetch-node
npm install
cd ..\..

# 4) Zotero
# (a) 装 https://www.zotero.org/download
# (b) 启动 Zotero,Edit → Preferences → Advanced → "Allow other applications..."
# (c) 编辑 zotero-mineru\config.json,改 zotero_library_id 和 zotero_storage 路径

# 5)(可选)Claude Code skill —— 让 AI 自动跑全流程
#   把 ~/.claude/skills/paper-fetch/SKILL.md 复制过来,路径都是 C:\paper-pipline\paper-fetcher\
```

### 4.3 zotero-mineru/config.json 要改什么

打开 `zotero-mineru\config.json`,核对/修改:

```json
{
  "mineru_exe":         "C:\\ProgramData\\miniconda3\\envs\\mineru\\Scripts\\mineru.exe",
  "zotero_storage":     "C:\\Users\\<YOU>\\Zotero\\storage",
  "mirror_dir":         "C:\\Users\\<YOU>\\Zotero\\mineru-mirror",
  "state_file":         "C:\\paper-pipline\\zotero-mineru\\state.json",
  "zotero_api_base":    "http://localhost:23119",
  "zotero_library_id":  12146168
}
```

`zotero_library_id` 怎么查:打开 https://www.zotero.org/settings/keys ,Your userID 就是。

## 5. 日常用法

### 5.1 全流程一次过(推荐:用 Claude Code skill)

如果你装了 `paper-fetch` skill,直接说一句"清洗 input 里的清单,抓 PDF,推 Zotero" 就行;AI 按 SKILL.md 走 7 步,中途只跟你确认一次"review.json 里拿不准的那几条 OK 吗"。

### 5.2 手动跑(没装 skill 时)

```powershell
cd C:\paper-pipline\paper-fetcher

# step 1: 杂乱 txt 丢到 input/(随便起名)
# step 2: 清洗
python clean_list.py input\my_list.txt

# step 3: 看 output\paperlist_review.json,人或 AI 写 decisions.json
#   规则详见 AI_WORKFLOW.md
notepad output\paperlist_review.json
notepad output\decisions.json   # 自己写

# step 4: apply
python apply_decisions.py output\decisions.json

# step 5: 抓 PDF(后台,看 output/logs/run-*.log)
python run.py output\paperlist_clean.txt --skip-existing

# step 6: 推 Zotero(Zotero 桌面 app 必须开,且先在 UI 里选中目标 collection)
python import_to_zotero.py

# step 7: 转 markdown
cd ..\zotero-mineru
python batch.py
# 或后台守护:
.\start-watcher.ps1
```

### 5.3 只跑某一段

```powershell
# 只想转 markdown(Zotero 里已经有 PDF,跳过前面)
cd zotero-mineru
python batch.py

# 只想抓某一篇(skip 整个清洗流程)
cd paper-fetcher
python run.py output\paperlist_clean.txt --skip-existing
#   (在 clean.txt 临时加一行 `[ieee] Foo (doi=10.1109/...)` 即可)
```

## 6. 注意事项 / 踩过的坑

### 6.1 publisher 反爬

- **IEEE Xplore**:Akamai 偶尔返回"APM HTML 挑战页"而不是 PDF。handler 自动 sleep 90s + 换 session 重试一次。如果连续多篇失败 → 暂停 10 分钟。
- **ACM DL**:Cloudflare 拦截普通 HTTP 请求,**必须**用 undetected-chromedriver(本质上是一个真 Chrome)。第一次启动 chromedriver 慢点(下载 driver),后面快。
- **ScienceDirect**:SD 的 WAF 极其敏感。
  - Python 的 `playwright-stealth` 库被 SD 识破(踩过坑,所以我们用 Node 的 `puppeteer-extra-plugin-stealth`)。
  - 60 秒/篇的间隔是底线。**别同时跑多个 SD 实例,别紧密重试**。
  - 一旦撞 "anti-bot blocked: are you a robot",对应 IP 会进 SD 的观察池,严重时 1 小时内任何 stealth 都过不了。**唯一办法:等**。
  - 别在 SD 跑批的时候改 sd-fetch-node 里的 .mjs 文件(Node 进程行为可能异常)。
- **TechRxiv** preprints(DOI 10.36227/...):它们的 publisher 字段会被 CrossRef 标成 "IEEE",但实际不在 ieeexplore.ieee.org 上,IEEE handler 会报 "no arnumber in landing url"。归到 manual 让用户手动下。

### 6.2 Zotero local API 的限制

- 端口 23119 上 Zotero 提供两套接口:
  - `/api/users/<id>/...`:Web API 模拟,**只支持 GET**(读)
  - `/connector/...`:Browser Connector API,**支持写**(其实就是浏览器插件保存到 Zotero 用的)
- 我们用 `/connector/saveStandaloneAttachment` 写 PDF。它接受 PDF 字节 + `X-Metadata` header。
- 上传后 Zotero **自动**调用元数据识别(从 PDF 文本里挖标题 → 查 CrossRef / DOI.org)。几秒钟后,PDF 就变成一个完整的 conferencePaper / journalArticle 条目。
- **新 item 进哪个 collection?** 进你 Zotero UI 当前选中的那个。所以跑 `import_to_zotero.py` 前请在 Zotero 左边栏点一下你想放的 collection(比如 paper-fetcher)。
- **PowerShell 的 Invoke-WebRequest 用不了**:Zotero 返回 HTTP/1.0,PowerShell 不会处理。`requests` / `pyzotero` / `curl` 都没问题。

### 6.3 paper-fetcher 内部约定

- 输入路径:**只**从 `paper-fetcher/input/*.txt` 拿(多个 txt 时取最新修改的)。
- 输出路径:固定 `paper-fetcher/output/{ieee,acm,sd}/<title>.pdf`。
- PDF 文件名 = paper title(去掉 Windows 非法字符,截到 140 字),不是 DOI。早期 Node 版用 DOI 命名,迁移时手动改过名 —— 如果你的旧 PDF 是 DOI 名,run.py 的 `--skip-existing` 会不认它,会重抓。
- `gap_seconds = 60`(IEEE / ACM / SD 通用,源码里改),已是踩坑后的最低值。

### 6.4 AI 步骤(decisions.json)的 token 预算

设计目标:让 Sonnet / Haiku 这种便宜模型也能做。详见 `paper-fetcher/AI_WORKFLOW.md`。

总结:
- AI **只读** `paperlist_review.json`(几 KB)
- AI **只写** `decisions.json`(几 KB)
- AI **不读** 原始 messy.txt(可能 50KB)、不读 `paperlist_clean.txt`(可能 30KB)
- 每篇决策模板见 AI_WORKFLOW.md 第三节

### 6.5 旧目录

`C:\paper-fetcher\` 和 `C:\Users\Administrator\zotero-mineru\` 是迁移前的原始位置,目前**保留不动**。新工作全部在 `C:\paper-pipline\` 下做。两边别同时改,避免混乱。

### 6.6 Probe 残留

调试 Zotero API 时往 Zotero 里塞过几个测试条目(标题以 `_probe_` 开头)。需要的时候在 Zotero UI 里搜 `_probe` 一并删掉。

## 7. 故障排查

| 症状 | 大概率原因 | 处理 |
|------|----------|------|
| `Zotero local API not reachable` | Zotero 没开 / 端口被防火墙挡 / 设置里关了 | 启动 Zotero,Edit → Preferences → Advanced 里勾上"Allow other apps" |
| `connection unexpectedly closed`(PowerShell) | PowerShell 不会处理 HTTP/1.0 | 改用 curl 或 Python requests 测 |
| `node not available` | Node 没装 / 不在 PATH | 装 Node ≥ 18,确认 `where node` 有结果 |
| `Node fetch script missing` | sd-fetch-node 被移走/没 `npm install` | 检查路径 + `cd paper-fetcher\sd-fetch-node && npm install` |
| SD `anti-bot blocked: are you a robot` | IP 进了 SD WAF 名单 | **停手**,等 30-60 分钟,期间别再撞 |
| IEEE `APM HTML challenge` | Akamai 限速 | handler 自动 retry 一次;不行就停 10 分钟再来 |
| ACM `cloudflare stuck` | undetected-chromedriver 没过 CF | handler 自动重启 driver + sleep;再不行换时间段 |
| Zotero 里新 PDF 没自动识别元数据 | Zotero 后台任务慢 / PDF 是扫描件没文字 | 等 10 秒;扫描件需要先 OCR(右键 → "Add Annotation from OCR") |
| `mineru` 命令找不到 | conda env 没激活 / mineru 没装 | `conda activate mineru` + `pip install mineru` |
| zotero-mineru 跑了但没新输出 | state.json 标记为已处理 | 删对应 key 的 state 条目,或 `--force` 重跑 |

## 8. 给后续 AI 的提示

如果你是 Claude(或别的 AI)在这个 repo 里干活,有几个事先知道能少踩坑:

1. **不要自己装 stealth 库的 Python 版本** —— 我们试过了不行(SD 识破)。SD 部分只用 Node。
2. **不要试图给本地 Zotero `/api/` 端点 POST/PATCH** —— 它返回 400 "Endpoint does not support method"。写操作只走 `/connector/`。
3. **不要在测试时连续撞 SD** —— 一次失败请等 30 分钟,不是 30 秒。
4. **改 SKILL.md 路径时**:`C:\paper-pipline\paper-fetcher\` 是当前生效路径,旧的 `C:\paper-fetcher\` 是历史。
5. **CrossRef API 请求要 polite**:UA 里带 mailto,间隔 1s/req,`clean_list.py` 已经这样了。
6. **遇到 paper-fetcher 输出目录文件丢失**:`run.py --skip-existing` 会重抓所有,这是预期行为。
7. **手动决策时优先放 manual,别强行 accept**:`paperlist_clean.txt` 一旦有错条目,后续抓取会失败/抓错文章,污染下游。

## 9. License / 致谢

私人工具,不打算严肃维护。代码可以随便看 / fork / 拿走改 —— 不保证不破 publisher TOS,机构访问权限你自己负责。

依赖的第三方:
- [pyzotero](https://github.com/urschrei/pyzotero)
- [puppeteer-extra-plugin-stealth](https://github.com/berstend/puppeteer-extra)
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [MinerU](https://github.com/opendatalab/MinerU)
- [Zotero](https://www.zotero.org/)
- [CrossRef API](https://api.crossref.org/)
