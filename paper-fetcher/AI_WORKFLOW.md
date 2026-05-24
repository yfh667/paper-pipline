# AI Workflow — 给后续低成本 AI(Sonnet / Haiku)的操作手册

目标:**让 AI 做尽量少的事**,绝大部分清洗交给确定性脚本,AI 只在脚本拿不准的地方做判断。每次任务的 token 消耗应该非常稳定。

---

## 一、完整流程图(token 视角)

```
messy.txt
   │  [大量 token,但 AI 不读它]
   │
   ▼
$ python clean_list.py messy.txt
   │
   ├─→ output/paperlist_clean.txt        [机器直接搞定的,AI 不读]
   ├─→ output/paperlist_review.json      [小,AI 读这个]
   └─→ output/clean.log                  [AI 不读]

   │
   │  [AI 介入处]
   │   读 review.json,产出 decisions.json
   ▼
$ python apply_decisions.py output/decisions.json
   │
   └─→ 更新后的 clean.txt + 缩减后的 review.json

   │
   │  [机器又接管]
   ▼
$ python run.py output/paperlist_clean.txt --skip-existing
   │
   └─→ output/{ieee,acm,sd}/*.pdf + output/manual/needs_manual.txt
```

**AI 唯一需要读的:** `paperlist_review.json`(通常 < 50 KB,几十条以内)
**AI 唯一需要写的:** `decisions.json`(把每条 review 分类)

---

## 二、review.json 三种条目形式

```json
[
  // (A) URL 形式 —— 域名不认识
  { "kind": "url", "url": "https://...", "reason": "unknown domain" },

  // (B) 标题 + CrossRef 候选(机器拿不准选哪个)
  { "kind": "title",
    "title": "CMAP: Certificate-less MQTT-based...",
    "top_score": 0.8,
    "candidates": [
      {"doi": "10.1109/...", "title": "CMAP: Certificateless ...", "score": 60.2},
      ...
    ]
  },

  // (C) 标题 + 完全没找到候选
  { "kind": "title", "title": "...", "candidates": [] }
]
```

---

## 三、AI 决策三选一

把每条 review 分到下面三个桶之一:

### 1. `accepts` — 机器拿不准但 AI 看一眼就能确定的正确匹配

判断标准(命中任何一条就归这里):
- 候选 #1 标题跟查询标题**几乎一样**,只是 hyphen / 空格 / 大小写不同(常见:`Certificate-less` vs `Certificateless`、`linkplanning` vs `link planning`)
- 候选 #1 的 score 是 #2 的 1.5× 以上,且话题明显一致
- 候选 #1 的发布商类别(IEEE/ACM/Elsevier/Optica)跟标题主题契合

写法:
```json
{
  "match": "CMAP: Certificate-less",                  // review 里这条的标题/URL 子串(用于定位)
  "tag": "ieee",                                       // ieee/acm/elsevier/spie/springer/...
  "title": "CMAP: Certificateless MQTT-Based Authentication Protocol for Medical IoT",
  "doi": "10.1109/access.2026.3684371"
}
```

`tag` 必须是 `clean_list.py` 已知的 publisher 短标签(`DOI_TAG` 字典里有);只有 `ieee/acm/elsevier` 会被 `run.py` 自动抓,其他短标签的会落到 `output/manual/needs_manual.txt`,这是预期行为。

### 2. `noise` — 不是论文,直接丢

典型:Wikipedia / GitHub / Bilibili / Notion / Google Scholar 作者列表(`L Liu, J Zhang, ...`)/ 加密过的 email link / 重复条目。

```json
{ "match": "wikipedia.org/wiki/Guowang" }
```

### 3. `manual` — 真不知道,留给人工

典型:候选全都是不相关的论文 / 论文太新 CrossRef 还没收录 / 标题被截断只有部分。

```json
{
  "match": "Starlink Constellation: Deployment, Configuration",
  "reason": "no good CrossRef match; likely a recent paper not yet indexed"
}
```

这些会保留在 review.json 顶部,带 `_manual` 字段,用户自己处理。

---

## 四、`match` 字段的语义

`match` 是**子串匹配**,不是正则,不区分大小写。脚本会拼接条目所有文本(`title` + `url` + 候选的 `title` + 候选的 `doi`)然后 substring search。所以 `match` 字段:
- 写 review 条目里独有的一段文本即可
- 不要写太短(会误中其他条目)
- 不要写太长(可能被空格/标点差异打断)
- **重复用同一个 `match` 是安全的**(脚本只匹配 review.json 里现存的条目)

---

## 五、运行命令

```powershell
# AI 看完 review.json 后,把 decisions.json 写到 output/decisions.json
& 'C:\ProgramData\miniconda3\envs\mineru\python.exe' apply_decisions.py output\decisions.json
```

apply_decisions 是幂等的(clean.txt 内部用 set 去重),误操作可以重跑。

---

## 六、典型决策示例(参考本仓库的 `output/decisions.json`)

| 现象 | 决策类别 | 备注 |
|------|---------|------|
| 标题轻微 typo 但候选 #1 score 是 #2 的 2× 且话题对得上 | accept | 选 #1 |
| 标题完全对得上但 `linkplanning` / `inIntersatellite` 这种连写 | accept | 选 #1 |
| 候选都跟主题无关(WDM vs satellite networks) | manual | 标 reason |
| 候选 score 都 < 30 | manual | CrossRef 没收录 |
| URL 是 wikipedia / github / scholar.google / notion | noise | |
| URL 是被 base64 编码的 webofscience email 链接 | noise | |
| 作者列表(`L Liu, J Zhang, ..., 2026`)而非真标题 | noise | 它是 Google Scholar 引用页面被错当成标题 |
| 看上去是同一篇但 typo 重复(`LEO Topology...` 和 `LEO Topology...Constraints` 无空格版本) | noise(任选一个版本作为 noise) | 留一个有空格的进 manual |

---

## 七、给后续 AI 的 prompt 模板

```
你是 paper-fetcher 项目的 AI 清洗助手。请按 C:\paper-fetcher\AI_WORKFLOW.md 的规则
处理 C:\paper-fetcher\output\paperlist_review.json,产出 C:\paper-fetcher\output\decisions.json,
然后运行:
  & 'C:\ProgramData\miniconda3\envs\mineru\python.exe' apply_decisions.py output\decisions.json

不要重新读 paperlist.txt 或 paperlist_clean.txt;只读 review.json 即可。
完成后报告每个桶的数量。
```

这样:
- AI 不读原始 messy txt(可能很大)
- AI 不读 clean.txt(可能很大,而且不用判断)
- 只读 review.json(几 KB)+ 写 decisions.json(几 KB)+ 跑一条命令
- token 用量稳定且最低
