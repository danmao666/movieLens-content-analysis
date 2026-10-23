from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week4_common import (
    PORTFOLIO_DIR,
    connect_week4,
    model_facts,
    project_facts,
    require_week4_tables,
    save_excel,
    write_portfolio_file,
)


def main() -> None:
    connection = connect_week4()
    try:
        require_week4_tables(
            connection,
            "behavior_fact",
            "content_dim",
            "week2_daily_metrics",
        )
        facts = project_facts(connection)
        models = model_facts()
        PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

        root_readme = f"""# 泛文娱内容平台增长与推荐分析

这是一个基于 MovieLens 25M 的公开数据项目，用于模拟内容平台的用户活跃、内容表现、留存、异常监控、实验设计和基础建模分析。它不是任何真实公司的业务结果。

## 项目成果

- 使用 DuckDB SQL 完成用户、内容、行为、日期模型，多表关联、CTE、窗口函数、留存、漏斗、Top N 和异常检测。
- 使用 Python 完成清洗、EDA、可视化、用户未来活跃预测和模型误差分析。
- 使用 Excel 完成指标监控和内容分析看板。
- 使用 PyTorch 完成 MLP 基线，使用 PySpark 完成指标聚合和窗口排序。
- 设计推荐策略 A/B 实验方案，并记录统计检验、置信区间和因果限制。

## 数据规模

- 行为记录：{int(facts['scale']['behavior_count']):,}。
- 用户：{int(facts['scale']['user_count']):,}。
- 内容：{int(facts['scale']['content_count']):,}。
- 时间范围：{facts['scale']['first_date']} 至 {facts['scale']['last_date']}。

## 关键结果

- 最新指标日期：{facts['latest']['date_day']}，DAU：{int(facts['latest']['dau']):,}。
- 活跃用户最多的合格内容：{facts['top_content']['title']}，活跃用户：{int(facts['top_content']['active_users']):,}。
- 随机森林模型结果见 `days/ml_day18_model_comparison.csv`，不得脱离时间切分和代理标签解释。

## 文件

- Week 1：`code/README_week1.md`。
- Week 2：`code/README_week2.md`。
- Week 3：`code/README_week3.md`。
- Week 4：`code/README_week4.md`。
- 端到端报告：`days/ml_day23_end_to_end_report.md`。
- Dashboard：`days/ml_day14_dashboard.xlsx` 和 `days/ml_day23_end_to_end_analysis.xlsx`。

## 数据限制

MovieLens 只有评分和标签，没有注册、曝光、点击、观看时长、用户画像、活动日志或真实实验分流。因此项目中的活跃、留存、流失和推荐目标都是代理定义，不能包装成真实企业业务成果。

Generated on: {date.today().isoformat()}
"""
        write_portfolio_file("README.md", root_readme)

        data_dictionary = pd.DataFrame(
            [
                {
                    "table": "behavior_fact",
                    "grain": "one user-content rating event",
                    "key_fields": "user_id, content_id, event_ts",
                    "source": "dataset/ml-25m/ratings.csv",
                    "business_use": "user activity and daily metrics",
                },
                {
                    "table": "content_dim",
                    "grain": "one movie",
                    "key_fields": "content_id",
                    "source": "dataset/ml-25m/movies.csv",
                    "business_use": "content title and genre analysis",
                },
                {
                    "table": "user_dim",
                    "grain": "one user",
                    "key_fields": "user_id",
                    "source": "derived from behavior_fact",
                    "business_use": "user frequency and segmentation",
                },
                {
                    "table": "date_dim",
                    "grain": "one calendar date",
                    "key_fields": "date_day",
                    "source": "derived from event date range",
                    "business_use": "complete date spine and trend analysis",
                },
                {
                    "table": "week2_daily_metrics",
                    "grain": "one date",
                    "key_fields": "date_day",
                    "source": "SQL aggregate",
                    "business_use": "DAU, volume, new-user proxy, content activity",
                },
            ]
        )
        data_dictionary.to_csv(
            PORTFOLIO_DIR / "DATA_DICTIONARY.csv",
            index=False,
            encoding="utf-8-sig",
        )

        assets = pd.DataFrame(
            [
                {
                    "asset": "Daily dashboard",
                    "path": "days/ml_day14_dashboard.xlsx",
                    "use": "KPI, trend, anomaly, segmentation, retention, actions",
                },
                {
                    "asset": "End-to-end chart",
                    "path": "days/ml_day23_end_to_end_summary.png",
                    "use": "Presentation summary image",
                },
                {
                    "asset": "Model confusion matrix",
                    "path": "days/ml_day18_best_model_confusion_matrix.png",
                    "use": "Model error discussion",
                },
                {
                    "asset": "Spark physical plan",
                    "path": "days/ml_day20_spark_physical_plan.txt",
                    "use": "Shuffle and execution explanation",
                },
            ]
        )
        assets.to_csv(
            PORTFOLIO_DIR / "ASSETS.csv",
            index=False,
            encoding="utf-8-sig",
        )
        structure = """# Project Structure

```text
movieLens-content-analysis/
├── code/       # day-by-day executable scripts and run notes
├── sql/        # DuckDB SQL source and analysis queries
├── portfolio/  # project materials, data dictionary, and resume drafts
└── README.md
```

Raw data, generated reports, model weights, and the generated database are intentionally excluded; source code remains under `code/` and `sql/`.
"""
        write_portfolio_file("PROJECT_STRUCTURE.md", structure)
        write_portfolio_file(
            "DATA_LIMITATIONS.md",
            """# Data Limitations

MovieLens 25M contains ratings and tags. It does not contain registration events, impressions, clicks, watch time, demographic data, campaign logs, recommendation exposures, or randomized experiment assignment.

Consequences:

- Rating activity is a proxy for platform activity.
- New users are first observed rating users, not confirmed registrations.
- Retention is a later rating event, not confirmed product return.
- Churn and future activity targets are proxy labels.
- A/B results cannot be estimated from this historical observational dataset.
- Anomaly flags need business and pipeline logs for root-cause confirmation.
""",
        )

        manifest = []
        for path in sorted(OUTPUT_DIR.glob("ml_day*.xlsx")):
            manifest.append(
                {
                    "artifact": path.name,
                    "type": "workbook",
                    "exists": True,
                    "portfolio_use": "analysis output or dashboard",
                }
            )
        for path in sorted(OUTPUT_DIR.glob("ml_day*.png")):
            manifest.append(
                {
                    "artifact": path.name,
                    "type": "image",
                    "exists": True,
                    "portfolio_use": "presentation screenshot/chart",
                }
            )
        manifest_frame = pd.DataFrame(manifest)
        output = save_excel(
            {
                "assets": assets,
                "data_dictionary": data_dictionary,
                "artifacts": manifest_frame,
                "model_facts": pd.DataFrame(models.get("comparison", [])),
            },
            "ml_day24_portfolio_manifest.xlsx",
        )
        manifest_frame.to_csv(
            OUTPUT_DIR / "ml_day24_portfolio_manifest.csv",
            index=False,
            encoding="utf-8-sig",
        )
        print(f"Saved portfolio files in {PORTFOLIO_DIR}")
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
