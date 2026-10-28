# semis-weekly

[![tests](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml/badge.svg)](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml)

每周一期的半导体“远端”周报。财报和产业数据很容易找；这套系统补的是更远的几层：信用、利率、流动性管道、仓位和政策，并且每周判断其中哪一层真的在收紧。

[English](README.md)

判断规则提炼自一位在 X 上公开写作的宏观交易者三年的帖子（不公开其身份）。从中取的核心思路是：远端是**约束**，近端是**目标**。约束没收紧时，财报和产业决定方向；约束一收紧就会否决，而且谁说了算取决于期限。

## 流程

```
sources/registry.yaml       22 个序列和事件源，接口都实测过
   ↓ 抓取（原文件存档，期权链 gzip）
schema/schema.sql           DuckDB：raw_fetch → observations（point-in-time）→ events
   ↓ 代码按 signals/signals.yaml 算 15 个信号
signals、signal_history     每周每个信号的值和状态（slack / watch / binding / na）
   ↓ 第 1 级：每个信道一个模型，只读本信道（playbook/<语言>/channels/）
logs/<周>/C1…C7             7 份信道日志：依据、期限含义、讲解
   ↓ 第 2 级：远、中、近（playbook/<语言>/aggregation.md），含传导链检查
logs/<周>/near、mid、far
   ↓ 第 3 级：综合（aggregation.md + invariants.md）
logs/<周>/synthesis.md
   ↓ 渲染
reports/<周>.html           当期网页
   ↓ 4–8 周后
calibration                 回头对照，调阈值
```

- **代码算，模型判。** 抓取、清洗、算信号是确定的、可复查的；模型只读结果、做判断、写日志。
- **每一级只读下一级。** 某一级出错能定位，只重跑那一级和它上面的级；单个信道也能单独重跑。
- **每个数字都有出处。** `semis check` 检查日志里的每个数字都能在输入包（或下一级日志）里找到，允许四舍五入和单位换算；`ingest` 不通过就不登记。
- **写给人读，不是写给校验器。** 日志按 `playbook/<语言>/style.md` 写：结论先行、一句一事、术语在第一次出现时解释。
  信号和规则编号只留在 json 里供追溯，正文用 `playbook/glossary.yaml` 里的名字；网页上会显示的地方出现编号，`check` 不通过。
- **按当时能看到的数据。** 观测值记录首次看到和发布时间；回补的历史信号不会用到当时还没发布的季报和月营收。

## 信道

| 信道 | 数据 | 信号 |
|---|---|---|
| C1 信用 | FRED ICE BofA 利差；SEC 云厂 capex 和经营现金流 | S-L3-01/02/03 |
| C2 利率 | FRED 收益率和曲线；TreasuryDirect 拍卖 | S-L1-01/02/03、S-L2-01 |
| C3 流动性管道（低权重） | FRED 联储资产、TGA、逆回购 | S-L2-02 |
| C4 仓位 | Cboe VIX；Cboe 期权链自算 GEX（SPY、QQQ、SMH）；CFTC TFF | S-L4-01/02/03/04 |
| C5 产业 | FinMind 台积电和台湾 AI 服务器链月营收；SEC 云厂 capex | S-L5-01/02/03 |
| C6 公司与财报 | SEC 8-K Item 2.02 和 EX-99.1 新闻稿（11 家美国公司）；6-K 季报新闻稿（台积电、ASML） | 模型读新闻稿 |
| C7 政策与事件 | FOMC 日程和会后声明（自动抓）；即将进行的拍卖；可选的用户笔记 | 模型读声明和日历 |

TLT 30 日隐含波动每天存档，暂不判定；攒够历史后作为 C2 的 swaption 波动代理。

## 快速开始

需要 Python 3.12（用 uv 测试过）和网络。

```
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # macOS/Linux 用 .venv/bin/python
cp .env.example .env        # 填 CONTACT_NAME、CONTACT_EMAIL（SEC 要求）；SEMIS_LANG=zh 或 en
P=.venv/Scripts/python.exe
$P -m semis prepare         # 全部信道：抓取 → 信号 → 第 1 级输入包
$P -m semis backfill        # 可选：回补 26 周信号历史
$P -m unittest discover -s tests
```

## 每周运行

模型那几步是为 Claude Code 设计的：说“出本周报告”（或 “run this week's report”），`.claude/skills/weekly-report/SKILL.md` 会跑完整流程。手动跑：

```
$P -m semis prepare
$P -m semis prompt --run 2026-W44 --channel C1    # 每个信道（C1..C7）各交给一个模型
$P -m semis check  --run 2026-W44
$P -m semis ingest --run 2026-W44
#   第 2、3 级：按 playbook/<语言>/aggregation.md 写 near/mid/far.md 和 synthesis.md
$P -m semis check  --run 2026-W44
$P -m semis ingest --run 2026-W44
$P -m semis render --run 2026-W44                 # reports/2026-W44.html
$P -m semis review                                 # 4–8 周前待回填的判断
$P -m semis calibrate --run 2026-W44 --item 2:near:state --outcome 对 --note "……"
```

`--lang zh|en`（或 `.env` 里的 `SEMIS_LANG`）决定规则手册、提示词和网页的语言。一期只用一种语言。

## 数据源和条款

所有来源都免费，大部分是官方的（FRED、SEC EDGAR、TreasuryDirect、联储、CFTC）。Cboe 延迟期权链和 FinMind 是公开的，但条款在清单里标为 `check`，每天只抓一次，供个人研究。SEC 联系邮箱只发给 sec.gov；其他来源如实标明 `python-requests`（FRED 会拦截不带这个标识的请求）。

## 已知限制

- GEX 依赖做市商方向假设（客户卖 call、买 put），贴近 flip 时符号可能翻转；数据日当天到期的合约已排除。
- 没有 when-issued 收益率，拍卖走弱用认购倍数和 10 年期变动近似。
- swaption 隐含波动不免费，暂用 10 年期已实现波动代替。
- FRED 上的 ICE BofA 利差只有近 3 年，本地历史攒起来之前分位样本偏短。
- 6-K 没有事项编号，台积电和 ASML 的季报靠附件正文识别；开头没提到季度和业绩项的新闻稿会漏掉。
- 大部分阈值是标为“补充”的初值，靠校准修正。
- 回补的历史用当前数据版本，修订无法还原；GEX 在第一次快照之前没有历史。

网页按 IBM Carbon 设计体系（字阶、间距、颜色 token、tile、tag、数据表），迷你走势图参照英国政府分析职能（Analysis
Function）的图表指南。每个状态都是颜色加形状，不单靠颜色区分。

## 目录

```
semis/        抓取、信号、渲染、命令行（python -m semis）
sources/      registry.yaml
signals/      signals.yaml（阈值和修改记录）
schema/       schema.sql
playbook/     zh/ 和 en/：目录页、不变量、聚合规则、写作规范、channels/C1–C7；glossary.yaml
prompts/      第 1 级提示词模板（zh、en）
tests/        回归测试
```

不在仓库里：`.env`、`data/`（数据库和原始存档）、`logs/`、`reports/`。

## 许可证

MIT，见 [LICENSE](LICENSE)。不构成投资建议。
