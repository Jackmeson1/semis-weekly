# semis-weekly

[![tests](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml/badge.svg)](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml)

每周一份的半导体投资周报，看的是财报以外的东西：利率、信用、资金面、市场仓位和政策。

[English](README.md)

## 现在缺什么

半导体股票的涨跌，很多时候不是因为财报，而是因为利率突然往上冲、公司借钱变贵，或者市场上大家的仓位太挤。可是能找到的东西，大多帮不上这个忙：

- **免费的信息几乎都在讲财报和产业。** 利率、信用、资金面、仓位的数据，要么在付费终端里，要么散落在各种评论里。
- **评论通常只给结论，不讲取舍。** 利率走高和 AI 需求强劲同时出现时，该听谁的？看两周和看半年，答案为什么不一样？很少有人说清楚。
- **看板只把数据摆出来。** 几十条曲线放在一起，不告诉你这周到底是哪一项在起作用。
- **AI 写的市场总结又密又难读。** 里面的数字从哪来，也不一定查得到。

## 这个项目补什么

- **只用免费数据，付费的找替代。** 比如做市商 gamma（期权做市商的对冲方向）通常要付费买，这里用 Cboe 公开的延迟期权数据自己算；单家公司的信用保险价格拿不到，就用全市场的信用利差代替。
- **把取舍写成明确的规则。** 每个期限谁说了算，什么情况可以推翻方向，什么情况不行，都写在规则手册 `playbook/` 里，可以逐条检查、逐条修改。
- **每周给出一个判断。** 哪些因素在收紧，对未来两周、一个财报季、半年以上分别意味着什么，该加仓、维持、减仓还是对冲。
- **写给人读，也经得起查。** 分析分层写，每个数字都必须能在原始数据里找到，正文里不出现内部编号。
- **边看边学。** 每个主题都用本周的真实数字讲一个概念。

## 核心思路

把宏观因素当成刹车，把产业和财报当成油门。刹车没踩下去时，看财报和产业就够了；刹车一踩，它说了算。

哪个刹车最要紧，取决于你看多远：

- **两周以内**：市场仓位最要紧。比如期权做市商在追涨杀跌、放大波动时，好公司也会跟着跌。
- **一个财报季**：看资金面、产业景气和 AI 需求。
- **半年以上**：看产业和 AI 需求本身。只有融资真的断了，才会改变方向。

## 一期周报里有什么

- 开头一句话的结论和动作，比如“维持，加一点对冲”。
- 远、中、近三个期限各自的判断，以及它们之间有没有冲突。
- 15 个指标过去半年每周的状态：没收紧、接近、收紧。
- 7 个主题各一张卡片：信用、利率、流动性、市场仓位、产业、公司财报、政策。每张都有一段讲解，用本周的真实数字讲一个概念，适合边看边学宏观。
- 未来的 FOMC 会议和国债拍卖，以及每项数据最近一次更新的时间。

## 它是怎么做出来的

1. **抓数据。** 全部是免费来源，大部分是官方的：美联储的 FRED 数据库、SEC 的财报申报、美国财政部、CFTC、Cboe 期权数据、台湾上市公司月营收。
2. **算指标。** 由代码计算，结果可以复查。历史数据只用当时已经公布的部分，不会“偷看未来”。
3. **分主题写分析。** 每个主题交给一个 AI 单独写，它只看这个主题的数据。然后汇总成远、中、近三个期限，最后得出总结论。分层写的好处是哪一步出错都能查到，也可以只重写那一步。
4. **核对数字。** 分析里的每个数字都必须能在原始数据里找到，找不到就不收。分析里也不允许出现内部编号，要写成人能看懂的名字。
5. **生成网页。** 页面按 IBM 的 Carbon 设计规范排版，支持手机和暗色模式，每种状态都用颜色加形状区分。

写作规范在 `playbook/zh/style.md`：结论先行，一句话只说一件事，术语第一次出现时当场解释。

## 快速开始

需要 Python 3.12（用 uv 测试过）和网络。

```
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # macOS/Linux 用 .venv/bin/python
cp .env.example .env        # 填 CONTACT_NAME、CONTACT_EMAIL（SEC 要求）；SEMIS_LANG=zh 或 en
P=.venv/Scripts/python.exe
$P -m semis prepare         # 抓数据、算指标、给每个主题准备输入
$P -m semis backfill        # 可选：补算过去 26 周的指标
$P -m unittest discover -s tests
```

## 每天自动抓取

有些数据只能在当天存下来，比如期权链和隐含波动，过了这一天就拿不到了。所以除了每周出报告，最好每个工作日自动抓一次：

```
$P -m semis daily        # 抓一遍所有数据，结果追加到 data/fetch-logs/<日期>.log
```

Windows 上用任务计划程序，每个工作日美股收盘后跑一次（用 pythonw.exe，不弹窗口）：

```powershell
$root = "<项目目录>"
$action = New-ScheduledTaskAction -Execute "$root\.venv\Scripts\pythonw.exe" -Argument '-m semis daily' -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '14:30'   # 本地时间
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'semis-weekly daily fetch' -Action $action -Trigger $trigger -Settings $settings
```

macOS/Linux 用 cron：`30 21 * * 1-5 cd <项目目录> && .venv/bin/python -m semis daily`（UTC 时间）。

## 每周运行

写分析的几步是为 Claude Code 设计的：在 Claude Code 里说“出本周报告”（或 “run this week's report”），它会按 `.claude/skills/weekly-report/SKILL.md` 跑完整个流程。手动跑的话：

```
$P -m semis prepare
$P -m semis prompt --run 2026-W44 --channel C1    # 生成给 AI 的任务说明，C1 到 C7 每个主题一份
$P -m semis check  --run 2026-W44                 # 核对数字来源、检查有没有内部编号
$P -m semis ingest --run 2026-W44                 # 登记结论
#   然后按 playbook/zh/aggregation.md 写远、中、近和总结论，再 check、ingest 一次
$P -m semis render --run 2026-W44                 # 生成网页 reports/2026-W44.html
$P -m semis review                                 # 列出 4 到 8 周前、该回头核对的判断
$P -m semis calibrate --run 2026-W44 --item 2:near:state --outcome 对 --note "……"
```

`--lang zh|en`（或 `.env` 里的 `SEMIS_LANG`）决定规则手册、提示词和网页用哪种语言。一期只用一种语言。

## 数据来源和使用条款

所有来源都免费。Cboe 的延迟期权数据和 FinMind 是公开的，但条款没有明确允许自动抓取，所以在数据清单里标为 `check`，每天只抓一次，只用于个人研究。

SEC 要求请求里带联系邮箱，这个邮箱只发给 sec.gov。其他来源收到的都是如实的 `python-requests` 标识；FRED 会拦截不带这个标识的请求。

## 已知限制

- **做市商仓位是估算的。** 期权数据不告诉你做市商站在哪一边，我们按行业通行的假设算。价格离临界点很近时，结论可能反过来。
- **有几项数据拿不到，用近似代替。** 没有国债发行前的交易数据，拍卖好坏用认购倍数近似；利率期权的隐含波动要付费，暂时用已实现波动代替。
- **信用利差的历史只有 3 年。** 历史分位的样本偏短，要等本地数据攒起来。
- **台积电和 ASML 的财报靠正文识别。** 它们交的 6-K 表格没有事项编号，开头没提到季度和业绩的新闻稿会漏掉。
- **大部分警戒线是我们自己定的初值。** 每 4 到 8 周对照实际结果复核一次，再调整。
- **补算的历史用的是现在的数据版本。** 后来修订过的数字无法还原；期权仓位数据在第一次抓取之前没有历史。

## 目录

```
semis/        抓取、指标、网页、命令行（python -m semis）
sources/      数据清单 registry.yaml
signals/      指标定义和警戒线 signals.yaml，含修改记录
schema/       数据库结构 schema.sql
playbook/     规则手册，zh/ 和 en/ 各一套；glossary.yaml 是编号对应的名字
prompts/      给 AI 的任务模板（zh、en）
tests/        回归测试
```

不在仓库里：`.env`、`data/`（数据库和原始存档）、`logs/`、`reports/`。

## 致谢

判断框架参考了一位宏观交易者的公开观点。

## 许可证

MIT，见 [LICENSE](LICENSE)。不构成投资建议。
