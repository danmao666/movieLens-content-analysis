from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week4_common import project_facts, connect_week4, require_week4_tables, save_excel, write_portfolio_file


TALK_SECTIONS = [
    ("00:00-00:45", "项目背景", "我用 MovieLens 25M 模拟内容平台，关注用户活跃、内容表现、留存和指标波动。先说明数据是公开数据，评分是活动代理。"),
    ("00:45-01:45", "业务问题", "用户为什么可能不再活跃？哪些内容吸引更多活跃用户？DAU 波动时如何判断是用户、内容还是数据问题？"),
    ("01:45-03:00", "数据和指标", "介绍 behavior_fact、content_dim、user_dim、date_dim，以及 DAU、行为次数、内容活跃用户、留存和异常定义。"),
    ("03:00-04:30", "分析方法", "用 DuckDB SQL 做多表关联、窗口函数、留存、漏斗和异常；用 Python 做 EDA、分层和模型；用 Excel 做看板。"),
    ("04:30-06:00", "关键发现", "展示实际 DAU、内容排名、用户分层、cohort 留存和集中度结果。只陈述数据支持的事实，不把相关性说成原因。"),
    ("06:00-07:15", "模型结果", "说明时间快照特征和未来 30 天活动代理标签，比较 Logistic、PyTorch MLP 和 Random Forest，并展示 ROC-AUC 与误判分析。"),
    ("07:15-08:20", "建议与实验", "提出用户级推荐策略 A/B 实验，主指标是七日 rating-active rate，护栏包含内容多样性、评分质量和数据完整性。"),
    ("08:20-09:20", "局限与风险", "没有曝光、点击、观看时长、注册和真实分流，因此留存、流失和推荐标签都是代理；PySpark 本地使用可复现抽样。"),
    ("09:20-10:00", "总结", "总结自己完成的工程链路、一个最重要发现、一个建议和一个下一步验证。邀请面试官追问 SQL、时间切分或指标口径。"),
]


MOCK_QUESTIONS = [
    {
        "id": "M01",
        "question": "你为什么选择 MovieLens？",
        "target": "说明选择原因、数据规模和局限，不把它包装成真实业务。",
    },
    {
        "id": "M02",
        "question": "你的 DAU 口径是什么？",
        "target": "明确评分行为代理、去重用户和日期粒度。",
    },
    {
        "id": "M03",
        "question": "DAU 下降你先查什么？",
        "target": "按数据完整性、行为量、内容量、新老用户和业务日志拆解。",
    },
    {
        "id": "M04",
        "question": "为什么模型要按时间切分？",
        "target": "回答预测时点和防止未来信息泄漏。",
    },
    {
        "id": "M05",
        "question": "Random Forest 为什么比 PyTorch MLP 好？",
        "target": "只引用实际测试结果，并讨论表格数据、特征量、调参和样本限制。",
    },
    {
        "id": "M06",
        "question": "这个模型能直接上线吗？",
        "target": "不能；还要校准、阈值、业务成本、漂移、标签延迟和线上验证。",
    },
    {
        "id": "M07",
        "question": "你如何证明推荐策略有效？",
        "target": "用户级随机分流、主指标、护栏、显著性和置信区间。",
    },
    {
        "id": "M08",
        "question": "PySpark 的 Shuffle 在哪里发生？",
        "target": "解释 groupBy、join、窗口和 repartition 的数据重分发。",
    },
    {
        "id": "M09",
        "question": "项目中最需要改进的地方是什么？",
        "target": "主动说明真实缺口：缺少真实曝光/点击、Transformer 权重未下载、Spark 默认抽样等。",
    },
    {
        "id": "M10",
        "question": "如果再做一周，你会做什么？",
        "target": "提出接入真实事件、校准模型、离线推荐评估或真实 A/B 日志。",
    },
]


def main() -> None:
    connection = connect_week4()
    try:
        require_week4_tables(connection, "behavior_fact", "content_dim")
        facts = project_facts(connection)
    finally:
        connection.close()

    talk = pd.DataFrame(
        [
            {
                "time": time,
                "section": section,
                "talking_points": points,
            }
            for time, section, points in TALK_SECTIONS
        ]
    )
    mock = pd.DataFrame(MOCK_QUESTIONS)
    output = save_excel(
        {
            "ten_minute_talk": talk,
            "mock_questions": mock,
            "recording_checklist": pd.DataFrame(
                [
                    {"check": "under 10 minutes", "done": False},
                    {"check": "states data limitation", "done": False},
                    {"check": "quotes real project metrics", "done": False},
                    {"check": "separates facts from hypotheses", "done": False},
                    {"check": "explains validation plan", "done": False},
                    {"check": "answers one SQL follow-up", "done": False},
                ]
            ),
        },
        "ml_day28_project_presentation.xlsx",
    )
    talk.to_csv(
        OUTPUT_DIR / "ml_day28_project_talk.csv",
        index=False,
        encoding="utf-8-sig",
    )
    mock.to_csv(
        OUTPUT_DIR / "ml_day28_mock_interview.csv",
        index=False,
        encoding="utf-8-sig",
    )

    markdown = f"""# Day 28: Project Presentation and Mock Interview

## Ten-minute talk

Use the workbook timing table. The project scale is {int(facts['scale']['behavior_count']):,} events, {int(facts['scale']['user_count']):,} users and {int(facts['scale']['content_count']):,} content items. Speak from the business problem to evidence, action and validation.

## Recording process

1. Record one uninterrupted ten-minute explanation.
2. Mark every place where a metric has no definition or a claim exceeds the data.
3. Remove implementation narration that does not support a business decision.
4. Re-record after answering the ten mock questions without reading the answers.
5. Save the recording path and revision notes in the workbook checklist.

## Core delivery rule

Do not say “the user churned because of X” when the data only shows a rating gap. Say “the observed rating activity decreased; X is a hypothesis that requires validation.”

Generated on: {date.today().isoformat()}
"""
    write_portfolio_file("day28_project_talk.md", markdown)
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
