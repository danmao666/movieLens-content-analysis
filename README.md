# MovieLens 内容平台分析

这是一个基于 **MovieLens 25M** 公开数据的内容平台增长与推荐分析项目。项目将评分行为作为用户活跃行为代理，模拟内容平台常见的数据分析工作：指标建模、用户与内容分析、留存分析、异常监控、A/B 实验设计和基础机器学习建模。

> MovieLens 不是企业生产数据。项目中的活跃、留存、流失和推荐目标均为代理定义，不能作为真实业务结果对外表述。

## 项目内容

- 使用 DuckDB SQL 建立用户、内容、行为和日期模型，完成多表关联、CTE、窗口函数、留存、漏斗、Top N 和异常检测。
- 使用 Python/pandas 完成数据质量检查、EDA、趋势分析、用户分层、内容表现分析和未来活跃预测。
- 使用 scikit-learn、PyTorch 和 PySpark 完成分类基线、MLP 基线、指标聚合和窗口排名分析。
- 设计推荐策略 A/B 实验，定义主指标、护栏指标、显著性检验和数据限制。

## 仓库结构

```text
├── code/       # Python/R 分析脚本及分阶段说明
├── sql/        # DuckDB SQL 建模与分析脚本
├── portfolio/  # 项目介绍、数据字典、限制说明和简历草稿
└── README.md
```

## 使用说明

1. 从 [GroupLens MovieLens](https://grouplens.org/datasets/movielens/) 下载 MovieLens 25M 数据，并解压到本地 `dataset/ml-25m/`。
2. 按 `code/README_week1.md` 至 `code/README_week4.md` 的顺序运行分析脚本。
3. SQL 脚本位于 `sql/`，可使用 DuckDB 执行。

为控制仓库体积，原始数据、虚拟环境、模型权重和本地生成结果未上传；`.gitignore` 已排除常见本地文件。

## 简历项目链接

GitHub：github.com/danmao666/movieLens-content-analysis
