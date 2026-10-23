from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week4_common import model_facts, project_facts, write_portfolio_file, connect_week4, require_week4_tables


TARGETS = {
    "base": {
        "title": "数据分析 / 经营分析 / 内容平台分析",
        "keywords": "SQL、Python、DuckDB、pandas、指标体系、留存、用户分层、异常监控、A/B 实验、Excel、PyTorch、PySpark",
        "emphasis": "指标体系、业务分析、用户和内容分群、可复现报告",
    },
    "bytedance": {
        "title": "字节跳动：数据分析 / 内容策略分析方向",
        "keywords": "内容生态、用户增长、推荐策略、DAU、留存、实验设计、异常监控、SQL、Python",
        "emphasis": "内容平台指标、推荐策略验证、用户增长和快速定位问题",
    },
    "pdd": {
        "title": "拼多多：数据分析 / 经营分析方向",
        "keywords": "经营指标、用户分层、漏斗、转化、留存、异常排查、SQL、Python、Excel、数据驱动决策",
        "emphasis": "指标拆解、分群比较、行动建议和验证闭环",
    },
    "bilibili": {
        "title": "B站：内容分析 / 用户分析方向",
        "keywords": "内容表现、用户活跃、内容集中度、cohort、留存、推荐、用户画像、SQL、Python、A/B 实验",
        "emphasis": "内容供给和用户行为的结合、内容多样性、推荐实验",
    },
}


def metric_text(facts, models):
    comparison = models.get("comparison", [])
    forest = next(
        (
            row for row in comparison
            if row.get("model") == "random_forest_with_enhanced_features"
        ),
        {},
    )
    pytorch = models.get("pytorch", {})
    spark = models.get("spark", {})
    return {
        "rows": int(facts["scale"]["behavior_count"]),
        "users": int(facts["scale"]["user_count"]),
        "content": int(facts["scale"]["content_count"]),
        "forest_auc": float(forest.get("roc_auc", 0)),
        "forest_f1": float(forest.get("f1", 0)),
        "pytorch_auc": float(pytorch.get("roc_auc", 0)),
        "spark_rows": int(float(spark.get("ratings_rows", 0))),
    }


def build_resume(target, facts, metrics):
    return f"""# {target['title']}

> 姓名、电话、邮箱、城市、学历和可到岗时间请在投递前补充。以下项目数字来自项目运行结果，不能继续夸大。

## 求职关键词

{target['keywords']}

## 个人概述

以 Python 和 SQL 为主线完成公开内容数据的端到端分析，能够从原始行为数据建立指标模型，完成用户/内容分析、异常监控、实验设计和基础机器学习建模。重点关注指标口径、时间切分、数据泄漏和业务验证。

## 核心项目

### 泛文娱内容平台增长与推荐分析 | MovieLens 25M 模拟业务项目

**项目规模：** {metrics['rows']:,} 条评分行为、{metrics['users']:,} 个用户、{metrics['content']:,} 个内容，覆盖 {facts['scale']['first_date']} 至 {facts['scale']['last_date']}。

- 使用 DuckDB SQL 建立 `user_dim`、`content_dim`、`behavior_fact`、`date_dim`，完成多表关联、CTE、窗口函数、Top N、留存、漏斗、移动平均、标准差和异常阈值计算。
- 使用 Python/pandas/NumPy 完成数据质量检查、EDA、DAU/内容表现/用户频次分析，并用 Excel 产出 KPI、趋势、分层、留存和异常监控看板。
- 按用户快照和时间切分构造未来 30 天评分活跃代理标签，完成 Logistic Regression、PyTorch MLP 和 Random Forest 基线；Random Forest 测试 ROC-AUC 为 {metrics['forest_auc']:.3f}、F1 为 {metrics['forest_f1']:.3f}，PyTorch MLP ROC-AUC 为 {metrics['pytorch_auc']:.3f}。
- 设计用户级推荐策略 A/B 实验，定义七日活跃主指标、内容多样性和评分质量护栏指标，说明显著性、置信区间和因果限制。
- 使用 PySpark 完成约 {metrics['spark_rows']:,} 条可复现抽样行为数据的 groupBy、join、窗口排名、分区和 Shuffle/物理计划分析。

## 技术栈

Python、SQL、DuckDB、pandas、NumPy、scikit-learn、PyTorch、PySpark、Excel、Matplotlib、Seaborn、Git。

## 项目限制

MovieLens 是公开数据，不含注册、曝光、点击、观看时长、用户画像和真实实验分流。项目中的活跃、留存、流失和推荐目标均为评分行为代理指标，不代表真实公司业务成果。

## 面试准备

能够在 5～10 分钟内说明业务问题、指标口径、关键发现、原因判断、优化建议、A/B 验证和数据限制，并现场解释 SQL、时间切分和模型评估。

Generated on: {date.today().isoformat()}
"""


def main() -> None:
    connection = connect_week4()
    try:
        require_week4_tables(connection, "behavior_fact", "content_dim")
        facts = project_facts(connection)
        models = model_facts()
        metrics = metric_text(facts, models)
        files = []
        for name, target in TARGETS.items():
            content = build_resume(target, facts, metrics)
            path = write_portfolio_file(f"resume_{name}.md", content)
            files.append(
                {
                    "version": name,
                    "target": target["title"],
                    "file": str(path.relative_to(path.parents[1])),
                    "keyword_focus": target["keywords"],
                    "status": "draft - add personal information and verify job description",
                }
            )
        matrix = pd.DataFrame(
            [
                {
                    "target": name,
                    "title": target["title"],
                    "keyword_focus": target["keywords"],
                    "emphasis": target["emphasis"],
                }
                for name, target in TARGETS.items()
            ]
        )
        files_frame = pd.DataFrame(files)
        with pd.ExcelWriter(
            OUTPUT_DIR / "ml_day27_resume_versions.xlsx",
            engine="openpyxl",
        ) as writer:
            files_frame.to_excel(writer, sheet_name="files", index=False)
            matrix.to_excel(writer, sheet_name="keyword_matrix", index=False)
        matrix.to_csv(
            OUTPUT_DIR / "ml_day27_resume_keyword_matrix.csv",
            index=False,
            encoding="utf-8-sig",
        )
        print("Saved three targeted resume drafts in portfolio/ plus base version.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
