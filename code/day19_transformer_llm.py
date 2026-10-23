import argparse
import re
from datetime import date

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from common import OUTPUT_DIR, csv_sql_path
from week3_common import connect_week3, require_week3_tables, ensure_model_dir, save_excel


def build_tag_dataset(connection, sample_size=30000):
    tags_path = csv_sql_path("tags.csv")
    query = f"""
        SELECT
            lower(trim(t.tag)) AS tag_text,
            CASE
                WHEN c.genres IS NULL OR c.genres = '' THEN 'unknown'
                ELSE split_part(c.genres, '|', 1)
            END AS primary_genre
        FROM read_csv_auto('{tags_path}') t
        JOIN content_dim c
            ON CAST(t.movieId AS INTEGER) = c.content_id
        WHERE trim(t.tag) <> ''
        USING SAMPLE {int(sample_size)} (reservoir, 42)
    """
    return connection.sql(query).df()


def create_tag_summary(tags: pd.DataFrame) -> pd.DataFrame:
    return (
        tags.groupby(["primary_genre", "tag_text"], as_index=False)
        .size()
        .rename(columns={"size": "tag_count"})
        .sort_values(
            ["primary_genre", "tag_count"],
            ascending=[True, False],
        )
        .groupby("primary_genre", as_index=False)
        .head(10)
    )


def run_transformer_inference(tags: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    try:
        from transformers import pipeline
    except ImportError:
        return (
            pd.DataFrame(
                columns=["tag_text", "label", "score", "model"]
            ),
            "not_run: transformers is not installed",
        )

    sample = tags["tag_text"].drop_duplicates().head(100).tolist()
    try:
        classifier = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1,
        )
        predictions = classifier(sample, truncation=True)
    except Exception as error:
        return (
            pd.DataFrame(
                columns=["tag_text", "label", "score", "model"]
            ),
            f"not_completed: {type(error).__name__}: {error}",
        )
    output = pd.DataFrame(
        [
            {
                "tag_text": text,
                "label": prediction["label"],
                "score": prediction["score"],
                "model": "distilbert-base-uncased-finetuned-sst-2-english",
            }
            for text, prediction in zip(sample, predictions)
        ]
    )
    return output, "completed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-transformer",
        action="store_true",
        help="Run optional Hugging Face sentiment inference and download the model if needed.",
    )
    args = parser.parse_args()

    connection = connect_week3()
    try:
        require_week3_tables(connection, "content_dim")
        tags = build_tag_dataset(connection)
        tags = tags.dropna(subset=["tag_text", "primary_genre"])
        tags = tags[tags["tag_text"].str.len().between(2, 200)]
        tags = tags[tags["primary_genre"] != "unknown"]
        label_counts = tags["primary_genre"].value_counts()
        valid_labels = label_counts[label_counts >= 20].index
        tags = tags[tags["primary_genre"].isin(valid_labels)].copy()

        train, test = train_test_split(
            tags,
            test_size=0.2,
            random_state=42,
            stratify=tags["primary_genre"],
        )
        text_model = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        min_df=2,
                        max_features=20000,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=500,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        text_model.fit(train["tag_text"], train["primary_genre"])
        predicted = text_model.predict(test["tag_text"])
        accuracy = accuracy_score(test["primary_genre"], predicted)
        report = classification_report(
            test["primary_genre"],
            predicted,
            output_dict=True,
            zero_division=0,
        )
        text_metrics = pd.DataFrame(
            [
                {
                    "task": "tag text to primary genre baseline",
                    "train_rows": len(train),
                    "test_rows": len(test),
                    "label_count": tags["primary_genre"].nunique(),
                    "accuracy": accuracy,
                    "macro_f1": report["macro avg"]["f1-score"],
                }
            ]
        )
        tag_summary = create_tag_summary(tags)
        transformer_output = pd.DataFrame()
        transformer_status = "not_requested"
        if args.run_transformer:
            transformer_output, transformer_status = run_transformer_inference(tags)

        model_dir = ensure_model_dir()
        import pickle

        with (model_dir / "day19_tfidf_tag_classifier.pkl").open("wb") as file:
            pickle.dump(text_model, file)
        output_sheets = {
            "text_metrics": text_metrics,
            "tag_summary": tag_summary,
            "classification_report": pd.DataFrame(report).T.reset_index(
                names="label"
            ),
        }
        if args.run_transformer:
            output_sheets["transformer_inference"] = transformer_output
        output = save_excel(output_sheets, "ml_day19_transformer_llm.xlsx")
        text_metrics.to_csv(
            OUTPUT_DIR / "ml_day19_text_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        tag_summary.to_csv(
            OUTPUT_DIR / "ml_day19_tag_summary.csv",
            index=False,
            encoding="utf-8-sig",
        )
        if args.run_transformer:
            transformer_output.to_csv(
                OUTPUT_DIR / "ml_day19_transformer_inference.csv",
                index=False,
                encoding="utf-8-sig",
            )

        documentation = f"""# Day 19: Transformer and LLM Small Experiment

## Concepts

- A tokenizer maps raw text to token IDs.
- Embeddings map token IDs into continuous vectors.
- Self-attention lets each token condition on other tokens in the sequence.
- Transformer blocks combine attention, feed-forward layers, residual connections, and normalization.
- A pre-trained language model can be called for inference without training a model from scratch.

## Local text experiment

The dataset uses MovieLens user tags joined to the first listed movie genre. A TF-IDF plus logistic-regression classifier is the transparent baseline for predicting the primary genre from a tag. It is a weak-label/content-tag exercise, not a recommendation-quality benchmark.

{text_metrics.to_string(index=False)}

## Optional pre-trained inference

Transformer inference status: **{transformer_status}**.

Run the optional inference with:

```bat
python code\\day19_transformer_llm.py --run-transformer
```

This uses `distilbert-base-uncased-finetuned-sst-2-english` for a small sentiment inference demo on tags. The model is not trained for MovieLens tags, so the output is a demonstration of calling a pre-trained model and must not be treated as a validated content classifier.

## Limitations

Tags are user-entered text, the genre label is a proxy, and the sample is not a production taxonomy. A real project would use reviewed labels, a domain model, held-out time periods, and error analysis by content category.

Generated on: {date.today().isoformat()}
"""
        (OUTPUT_DIR / "ml_day19_transformer_llm.md").write_text(
            documentation,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
