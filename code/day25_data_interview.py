from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week4_common import save_excel


QUESTIONS = [
    {
        "id": "DA01",
        "question": "DAU 是什么？如何定义？",
        "answer": "DAU 是日活跃用户数。先定义活跃事件，再按日期 COUNT(DISTINCT user_id)。本项目用至少产生一条评分作为活跃代理，并明确这不是观看活跃。",
        "follow_up": "如果行为表有重复事件，先确认事件粒度并去重。",
    },
    {
        "id": "DA02",
        "question": "DAU 突然下降，你如何排查？",
        "answer": "先确认数据完整性和日期时区，再拆分新老用户、行为次数、活跃内容、渠道和设备；比较环比、移动平均和分群趋势，最后结合发布、活动和数据管道日志。",
        "follow_up": "先区分数据问题、用户问题和内容供给问题。",
    },
    {
        "id": "DA03",
        "question": "如何计算次日和七日留存？",
        "answer": "先按用户取首个活跃日形成 cohort，再判断用户是否在首日加 1 天或 7 天再次活跃，最后用留存用户数除以 cohort 用户数。要排除尚未到达观察窗口的 cohort。",
        "follow_up": "说明 exact-day retention 与 rolling retention 的差别。",
    },
    {
        "id": "DA04",
        "question": "为什么不能只按平均评分给内容排名？",
        "answer": "低样本内容的平均值方差大，容易把偶然高分误判为高质量。应同时设置最小行为量，并结合活跃用户、行为次数、评分分布和内容覆盖。",
        "follow_up": "可以补充贝叶斯平滑或置信区间。",
    },
    {
        "id": "DA05",
        "question": "SQL 中 COUNT(*) 和 COUNT(DISTINCT user_id) 的区别？",
        "answer": "COUNT(*) 统计行为记录数，COUNT(DISTINCT user_id) 统计去重用户数。DAU 必须使用后者，否则一个用户多次行为会被重复计算。",
        "follow_up": "说明 NULL 对 COUNT(column) 的影响。",
    },
    {
        "id": "DA06",
        "question": "什么时候使用窗口函数？",
        "answer": "需要保留明细行，同时计算排名、前后日期、累计值或分组内比较时使用窗口函数，例如 ROW_NUMBER 做每类 Top N，LAG 做环比。",
        "follow_up": "解释 PARTITION BY 和 ORDER BY 的作用。",
    },
    {
        "id": "DA07",
        "question": "如何写每个类型的 Top 3 内容？",
        "answer": "先聚合到内容类型和内容粒度，再使用 ROW_NUMBER() OVER(PARTITION BY type ORDER BY metric DESC) 排名，最后过滤 rank <= 3。",
        "follow_up": "确认并列时使用 RANK 还是 ROW_NUMBER。",
    },
    {
        "id": "DA08",
        "question": "如何设计用户行为漏斗？",
        "answer": "先定义每一层的事件和用户粒度，再按用户聚合阶段是否完成，统计每层人数、层间转化率和总转化率。不能把评分数据包装为曝光或点击漏斗。",
        "follow_up": "说明漏斗窗口和事件顺序。",
    },
    {
        "id": "DA09",
        "question": "如何处理重复值？",
        "answer": "先判断重复是合法重复行为还是数据重复，明确业务唯一键；保留最新或可信记录，或用 DISTINCT 形成分析层，同时记录删除数量和规则。",
        "follow_up": "不要未经确认直接 drop_duplicates。",
    },
    {
        "id": "DA10",
        "question": "如何处理缺失值？",
        "answer": "先统计缺失比例和分布，判断缺失是否有业务含义；关键键缺失通常隔离或拒绝，数值字段可按业务规则填补，并把处理前后数量写入质量报告。",
        "follow_up": "区分随机缺失与非随机缺失。",
    },
    {
        "id": "DA11",
        "question": "移动平均和标准差异常检测怎么做？",
        "answer": "对当前日期之前的历史窗口计算均值和标准差，当前值与均值差除以标准差得到 z-score，再设置最小基线和阈值。窗口不能包含当前值，否则会削弱异常信号。",
        "follow_up": "讨论季节性和分位数阈值。",
    },
    {
        "id": "DA12",
        "question": "内容集中度有什么业务含义？",
        "answer": "例如 Top 10 内容行为量占总行为量的比例，反映活动是否依赖少数内容。集中度高可能利于爆款，也可能增加内容供给风险。",
        "follow_up": "同时观察长尾覆盖和用户内容多样性。",
    },
    {
        "id": "DA13",
        "question": "相关性可以说明因果关系吗？",
        "answer": "不能。相关性只能说明变量共同变化，可能受混杂因素、反向因果或选择偏差影响。因果判断需要随机实验、准实验或明确识别假设。",
        "follow_up": "说明 A/B 实验如何提供因果证据。",
    },
    {
        "id": "DA14",
        "question": "A/B 实验为什么要以用户为分流单位？",
        "answer": "推荐策略通常影响用户后续行为，用户级持久分流可以避免同一用户同时接触两个策略造成污染。分流单位应和干预以及指标的独立性匹配。",
        "follow_up": "如果是商家或房间级干预，分流单位可能要更高层级。",
    },
    {
        "id": "DA15",
        "question": "主指标和护栏指标如何选择？",
        "answer": "主指标对应实验假设且只能预先指定一个主要决策指标；护栏指标监控用户体验、质量、成本和生态风险，避免主指标提升但整体体验恶化。",
        "follow_up": "本项目主指标可用七日 rating-active rate，护栏含内容多样性。",
    },
    {
        "id": "DA16",
        "question": "如何解释一个模型的 AUC？",
        "answer": "AUC 是随机抽取正负样本时，模型给正样本更高分的概率。它衡量排序能力，不等于准确率，也不代表概率校准或业务收益。",
        "follow_up": "结合正负样本比例和 PR-AUC。",
    },
    {
        "id": "DA17",
        "question": "项目中如何避免数据泄漏？",
        "answer": "按时间切分训练和测试，特征只使用快照日期之前的数据，标签使用未来窗口；拟合标准化和特征选择只在训练集完成，并检查字段是否含 future、post 或 label 信息。",
        "follow_up": "随机切分时间序列用户快照可能造成未来信息泄漏。",
    },
    {
        "id": "DA18",
        "question": "业务方只看一个平均数，你会怎么沟通？",
        "answer": "先确认决策问题，再补充分布、分群、时间趋势和置信区间。把统计结果翻译为行动和验证方案，同时明确数据限制。",
        "follow_up": "提供一个具体图表而不是堆更多指标。",
    },
    {
        "id": "DA19",
        "question": "如何评价一次分析报告是否合格？",
        "answer": "问题明确、指标口径可复现、事实与假设分开、结论有证据、建议可执行、验证方案具体、局限清楚，并且原始数据到图表的路径可追溯。",
        "follow_up": "让别人能用代码重新得到主要数字。",
    },
    {
        "id": "DA20",
        "question": "如何讲清楚这个项目？",
        "answer": "用业务问题开场，说明数据和限制，再讲指标体系、关键发现、原因判断、建议和实验验证。最后说明自己做了什么、结果是多少、哪些结论不能下。",
        "follow_up": "控制在 5 到 10 分钟，避免逐个展示所有 SQL。",
    },
]


def main() -> None:
    questions = pd.DataFrame(QUESTIONS)
    output = save_excel(
        {"questions": questions},
        "ml_day25_data_interview_questions.xlsx",
    )
    questions.to_csv(
        OUTPUT_DIR / "ml_day25_data_interview_questions.csv",
        index=False,
        encoding="utf-8-sig",
    )
    markdown = "# Day 25: Data Analysis Interview Questions\n\n"
    markdown += "先独立回答，再查看答案。回答必须结合本项目真实数据和限制。\n\n"
    for row in QUESTIONS:
        markdown += (
            f"## {row['id']} {row['question']}\n\n"
            f"**参考回答：** {row['answer']}\n\n"
            f"**追问：** {row['follow_up']}\n\n"
        )
    (OUTPUT_DIR / "ml_day25_data_interview_questions.md").write_text(
        markdown,
        encoding="utf-8",
    )
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
