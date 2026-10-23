from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week4_common import save_excel


QUESTIONS = [
    ("AI01", "什么是过拟合？如何处理？", "训练集表现很好但泛化差。可用时间切分验证、正则化、降低模型复杂度、早停、增加数据、特征筛选和误差分析。"),
    ("AI02", "AUC 和准确率有什么区别？", "AUC 衡量排序能力，准确率依赖阈值和类别比例。类别不平衡时不能只看准确率，应结合 PR-AUC、召回率和业务成本。"),
    ("AI03", "为什么使用时间切分？", "用户行为预测要模拟上线时只看到过去的场景。随机切分可能把未来模式泄漏到训练集，造成过高评估。"),
    ("AI04", "特征工程的原则是什么？", "围绕业务机制构造可用、稳定、可解释的特征，并确保特征在预测时点可获得。记录窗口、口径、缺失处理和版本。"),
    ("AI05", "如何处理类别不平衡？", "看业务代价选择 class_weight、重采样、阈值调整或 focal loss；评价使用 PR-AUC、召回率和成本，不盲目追求 accuracy。"),
    ("AI06", "什么是数据泄漏？", "训练过程使用了预测时不可获得的信息，例如用未来行为构造过去特征，或在全量数据上先标准化再切分。"),
    ("AI07", "Embedding 是什么？", "把离散对象或文本映射为低维稠密向量，使相似对象在向量空间中更接近，可用于召回、分类或相似度计算。"),
    ("AI08", "Transformer 的核心是什么？", "自注意力让序列中每个 token 根据其他 token 计算加权表示，再结合前馈层、残差连接和归一化构成 Transformer block。"),
    ("AI09", "Self-attention 如何计算？", "输入经过线性层得到 Q、K、V，使用 softmax(QK^T/sqrt(d_k))V 聚合上下文信息。"),
    ("AI10", "Tokenization 的作用？", "把文本切分为模型词表中的 token 并转换为 ID，控制输入长度、词表覆盖和未知词处理。"),
    ("AI11", "预训练和微调有什么区别？", "预训练在大规模通用数据学习表示，微调在下游标注任务或领域数据上更新模型以适配目标。"),
    ("AI12", "LoRA 解决什么问题？", "冻结大模型主参数，只训练低秩适配矩阵，减少显存、训练参数和存储成本，适合资源有限的领域适配。"),
    ("AI13", "PyTorch 训练循环有哪些步骤？", "Dataset/DataLoader 取批次，forward，计算 loss，zero_grad，backward，optimizer.step；训练和验证阶段分别控制 train/eval。"),
    ("AI14", "为什么使用 BCEWithLogitsLoss？", "它把 sigmoid 和二元交叉熵稳定地合并，避免单独计算 sigmoid 造成数值问题；类别不平衡可设置 pos_weight。"),
    ("AI15", "如何分析模型误判？", "按 false positive/false negative 抽样，比较行为频次、样本稀疏度、分群和概率边界，检查标签噪声、泄漏和业务代价。"),
    ("AI16", "如何部署模型？", "固定特征口径和模型版本，提供批量或在线推理接口，加入输入校验、超时、日志、监控、回滚和模型注册。"),
    ("AI17", "模型上线后监控什么？", "输入分布漂移、缺失率、预测分布、延迟、错误率、标签延迟后的 AUC/召回率，以及分群公平性或业务护栏。"),
    ("AI18", "Spark 的 Shuffle 是什么？", "当 groupBy、join、窗口或 repartition 需要按 key 重新分发数据时发生 Shuffle，带来网络、磁盘和内存成本。"),
    ("AI19", "PySpark 如何优化 Join？", "先过滤和选择必要列，检查数据倾斜，适当广播小表，控制分区数，避免重复 action，并查看 physical plan。"),
    ("AI20", "没有 GPU 时如何做 LLM 项目？", "优先做预训练模型推理、提示词实验、轻量分类或 CPU 可运行的基线；不要把未实际训练的 LoRA 或微调写成完成。"),
]


def main() -> None:
    frame = pd.DataFrame(
        [
            {"id": item[0], "question": item[1], "answer": item[2]}
            for item in QUESTIONS
        ]
    )
    output = save_excel({"questions": frame}, "ml_day26_ai_interview.xlsx")
    frame.to_csv(
        OUTPUT_DIR / "ml_day26_ai_interview.csv",
        index=False,
        encoding="utf-8-sig",
    )
    markdown = "# Day 26: AI Interview Questions\n\n"
    markdown += "回答时必须区分已经在本项目中实际完成的内容和仅学习过的概念。\n\n"
    for row in QUESTIONS:
        markdown += (
            f"## {row[0]} {row[1]}\n\n"
            f"**参考回答：** {row[2]}\n\n"
        )
    markdown += f"\nGenerated on: {date.today().isoformat()}\n"
    (OUTPUT_DIR / "ml_day26_ai_interview.md").write_text(
        markdown,
        encoding="utf-8",
    )
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
