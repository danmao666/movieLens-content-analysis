# 字节跳动：数据分析 / 内容策略分析方向

> 姓名、电话、邮箱、城市、学历和可到岗时间请在投递前补充。以下项目数字来自本地实际运行结果，不能继续夸大。

## 求职关键词

内容生态、用户增长、推荐策略、DAU、留存、实验设计、异常监控、SQL、Python

## 个人概述

以 Python 和 SQL 为主线完成公开内容数据的端到端分析，能够从原始行为数据建立指标模型，完成用户/内容分析、异常监控、实验设计和基础机器学习建模。重点关注指标口径、时间切分、数据泄漏和业务验证。

## 核心项目

### 泛文娱内容平台增长与推荐分析 | MovieLens 25M 模拟业务项目

GitHub：github.com/danmao666/movieLens-content-analysis

**项目规模：** 25,000,095 条评分行为、162,541 个用户、59,047 个内容，覆盖 1995-01-09 00:00:00 至 2019-11-21 00:00:00。

- 使用 DuckDB SQL 建立 `user_dim`、`content_dim`、`behavior_fact`、`date_dim`，完成多表关联、CTE、窗口函数、Top N、留存、漏斗、移动平均、标准差和异常阈值计算。
- 使用 Python/pandas/NumPy 完成数据质量检查、EDA、DAU/内容表现/用户频次分析，并用 Excel 产出 KPI、趋势、分层、留存和异常监控看板。
- 按用户快照和时间切分构造未来 30 天评分活跃代理标签，完成 Logistic Regression、PyTorch MLP 和 Random Forest 基线；Random Forest 测试 ROC-AUC 为 0.860、F1 为 0.719，PyTorch MLP ROC-AUC 为 0.835。
- 设计用户级推荐策略 A/B 实验，定义七日活跃主指标、内容多样性和评分质量护栏指标，说明显著性、置信区间和因果限制。
- 使用 PySpark 完成约 500,911 条可复现抽样行为数据的 groupBy、join、窗口排名、分区和 Shuffle/物理计划分析。

## 技术栈

Python、SQL、DuckDB、pandas、NumPy、scikit-learn、PyTorch、PySpark、Excel、Matplotlib、Seaborn、Git。

## 项目限制

MovieLens 是公开数据，不含注册、曝光、点击、观看时长、用户画像和真实实验分流。项目中的活跃、留存、流失和推荐目标均为评分行为代理指标，不代表真实公司业务成果。

## 面试准备

能够在 5～10 分钟内说明业务问题、指标口径、关键发现、原因判断、优化建议、A/B 验证和数据限制，并现场解释 SQL、时间切分和模型评估。

Generated on: 2026-10-15
