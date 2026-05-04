# A股盘后选股系统(配套主升浪突破策略)

每日盘后(建议 17:30 之后)运行,基于 Tushare Pro 数据自动产出次日候选池与交易计划。
配套设计文档:`strategies/ashare-postmarket-screener.md`。

## 一、安装

```bash
cd strategies/ashare_screener
pip install -r requirements.txt
```

## 二、Token 配置(只在本地终端执行一次,不要发送到任何聊天)

推荐方式:用 Tushare 官方 `set_token` 写入 `~/.tushare/token`,代码自动读取。

```bash
python -c "import tushare as ts; ts.set_token('您的真实token')"
```

备选:设置环境变量(临时覆盖)

```bash
export TUSHARE_TOKEN=您的真实token
```

## 三、运行

```bash
cd strategies/ashare_screener
python run_daily.py --date 20260430
```

输出:

- `reports/20260430.md` — 人类可读报告(主攻 / 守正 / 观察分档)
- `data/candidates/candidates_20260430.json` — 结构化结果(用于回测/复盘)
- `data/cache/<endpoint>/20260430.parquet` — 各接口本地缓存(再次运行复用)

## 四、需要用到的 Tushare 接口

| 接口 | 用途 |
|------|------|
| `daily` | 全市场 OHLCV |
| `daily_basic` | 流通市值、换手率、量比 |
| `limit_list_d` | 涨跌停明细(首封时间、封单、连板数) |
| `top_list` / `top_inst` | 龙虎榜与营业部明细 |
| `moneyflow` | 主力净流入 |
| `hsgt_top10` | 北向 Top10 |
| `kpl_concept` / `kpl_concept_cons` | 开盘啦概念板块 |
| `stock_basic` | 名称、上市日期(用于 ST 与次新过滤) |
| `trade_cal` | 交易日历 |

会员积分需覆盖以上接口。若 `kpl_*` 不可用,系统会跳过板块映射(板块相关分数为 0,但流程继续)。

## 五、配置

`config/thresholds.yaml` 里集中调整所有阈值(权重、闸门、黑名单、候选层、分档、计划)。

`config/hot_money_seats.yaml` — 知名游资席位字典,根据近期龙虎榜定期维护。

`config/theme_keywords.yaml` — 题材催化关键词(预留,未启用)。

## 六、测试

```bash
cd strategies/ashare_screener
pytest tests/
```

## 七、安全

- token 只存在 `~/.tushare/token` 或环境变量,不入仓库
- `data/`、`reports/` 已在本目录 `.gitignore`
- 代码不打印 token

## 八、限制

- 系统只输出**候选与计划**,不替代盘中执行
- 数据接口失败会输出 warning 并继续(对应特征置 0),建议运行后核对 stdout
- `price_pos_60` 当前为占位 0.5;如需精确实现可在 `features.py` 接入 60 日 daily 历史
