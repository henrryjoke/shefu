# Changelog

## [0.2.0] — 2026-05-28

### Added
- 梅花易数起卦引擎（`scripts/qigua_meihua.py`）：时间起卦 + 数字起卦
- 六爻纳甲起卦引擎（`scripts/qigua_liuyao.py`）：铜钱摇卦 → 纳甲装爻 → 六亲 → 世应 → 六神
- 历法模块（`scripts/lifa.py`）：年月日干支、月建日建计算
- 64卦数据库（`data/guaci_db.json`）
- 纳甲数据表（`data/najia_table.json`）
- 起卦测试界面（`qigua_test.html`）
- SKILL.md：新增起卦入口、意识聚焦提示、默认六爻手摇优先级

### Fixed
- 体用关系判断反转
- 铜钱老阳/老阴规则（三背=老阳, 三字=老阴）
- 爻位显示顺序（上爻在上、初爻在下）

## [0.1.0] — 2026-05-25

### Added
- 正易心法六层解卦工作流
- 6 篇参考文档（references/）
- 射覆模式（猜物占卜）
