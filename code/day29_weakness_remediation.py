from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week4_common import model_facts, read_output_csv, save_excel, write_portfolio_file


def main() -> None:
    models = model_facts()
    comparison = pd.DataFrame(models.get("comparison", []))
    spark = models.get("spark", {})
    remediation = []

    if not comparison.empty:
        best = comparison.sort_values("roc_auc", ascending=False).iloc[0]
        pytorch = comparison.loc[
            comparison["model"].str.contains("pytorch", case=False, na=False)
        ]
        pytorch_auc = (
            float(read_output_csv("ml_day17_pytorch_metrics.csv").iloc[0]["roc_auc"])
            if not read_output_csv("ml_day17_pytorch_metrics.csv").empty
            else None
        )
        remediation.append(
            {
                "priority": "high",
                "weakness": "PyTorch baseline is not the strongest tabular model.",
                "evidence": f"Best comparison ROC-AUC={best['roc_auc']:.3f}; PyTorch ROC-AUC={pytorch_auc:.3f}.",
                "practice": "Run 3 controlled experiments: hidden width, learning rate, and class threshold; keep the temporal test fixed and compare ROC-AUC/PR-AUC/F1.",
                "acceptance": "Write why a tree model may fit tabular aggregates better and include an error slice by activity quartile.",
            }
        )

    transformer_status = ""
    transformer_report = OUTPUT_DIR / "ml_day19_transformer_llm.md"
    if transformer_report.exists():
        text = transformer_report.read_text(encoding="utf-8")
        if "not_completed" in text:
            transformer_status = "pre-trained model weights were unavailable through the current network"
            remediation.append(
                {
                    "priority": "medium",
                    "weakness": "Transformer inference was not completed.",
                    "evidence": transformer_status,
                    "practice": "Keep the TF-IDF baseline, learn tokenizer/attention/embedding concepts, and rerun --run-transformer only when model weights can be downloaded or supplied locally.",
                    "acceptance": "Never write that Transformer inference or LoRA fine-tuning was completed until an output file and model version exist.",
                }
            )

    if str(spark.get("sample_mode", "")).startswith("reproducible sample"):
        remediation.append(
            {
                "priority": "medium",
                "weakness": "PySpark was validated on a local reproducible sample rather than full MovieLens.",
                "evidence": f"{spark.get('ratings_rows', 'unknown')} rows; {spark.get('sample_mode', 'unknown')}.",
                "practice": "Explain why local memory caused the sample choice, inspect the physical plan, and describe how a cluster/full run would change partitions and resources.",
                "acceptance": "Be explicit in interviews that the sample run proves the Spark workflow, not a full-scale benchmark.",
            }
        )

    remediation.extend(
        [
            {
                "priority": "high",
                "weakness": "Timed SQL score has not been recorded by the learner.",
                "evidence": "Day 22 script verifies answer-key queries but does not represent a human 90-minute attempt.",
                "practice": "Set a 90-minute timer, solve the four Day 22 prompts without opening the answer key, then record time, score, and failed cases.",
                "acceptance": "At least 80% rubric score and an explanation for every missed edge case.",
            },
            {
                "priority": "high",
                "weakness": "Public data lacks exposure and product-event evidence.",
                "evidence": "MovieLens contains ratings/tags only.",
                "practice": "Practice stating the exact proxy definition, what cannot be concluded, and the event schema needed for a real analysis.",
                "acceptance": "Every interview answer separates fact, hypothesis, and validation method.",
            },
        ]
    )

    frame = pd.DataFrame(remediation)
    output = save_excel(
        {"remediation": frame},
        "ml_day29_weakness_remediation.xlsx",
    )
    frame.to_csv(
        OUTPUT_DIR / "ml_day29_weakness_remediation.csv",
        index=False,
        encoding="utf-8-sig",
    )
    report = "# Day 29: Weakness Remediation\n\n"
    report += "先完成 high 优先级，再补 medium。不要通过改写简历掩盖未完成项。\n\n"
    for row in remediation:
        report += (
            f"## {row['priority'].upper()}: {row['weakness']}\n\n"
            f"**证据：** {row['evidence']}\n\n"
            f"**练习：** {row['practice']}\n\n"
            f"**验收：** {row['acceptance']}\n\n"
        )
    report += f"Generated on: {date.today().isoformat()}\n"
    (OUTPUT_DIR / "ml_day29_weakness_remediation.md").write_text(
        report,
        encoding="utf-8",
    )
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
