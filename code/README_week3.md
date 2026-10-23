# Week 3 Code

Week 3 extends the first two weeks into statistics, machine learning, PyTorch, NLP/Transformer concepts, Spark, and final project packaging.

The same public MovieLens 25M data is used. The dataset contains ratings and tags, not a real company's click, exposure, watch-time, registration, or experiment logs. The model target is future rating activity and must be described as a proxy.

## Dependencies

The existing Miniconda base environment already contains the Week 1/2 dependencies. Confirm or install the Week 3 packages in that same environment:

```bat
python -c "import importlib.util; names=['torch','pyspark','transformers']; [print(n, 'OK' if importlib.util.find_spec(n) else 'MISSING') for n in names]"
python -m pip install torch pyspark transformers
```

`transformers` is optional until the `--run-transformer` flag is used. PyTorch and PySpark are required to claim those two practical tasks are executed.

## Run order

Run one script at a time from the project directory:

```bat
# Run the following commands from the repository root.
python code\day15_statistics_ab_template.py
python code\day16_logistic_baseline.py
python code\day17_pytorch_mlp.py
python code\day18_model_comparison.py
python code\day19_transformer_llm.py
python code\day20_pyspark_metrics.py
python code\day21_finalize.py
```

Optional pre-trained Transformer inference:

```bat
python code\day19_transformer_llm.py --run-transformer
```

The optional command downloads a Hugging Face model on first use and may take substantially longer. It is a demonstration, not a domain-validated content classifier.

## Day mapping

### Day 15: statistics and A/B analysis

Calculates means, variance, reproducible sampling, bootstrap confidence intervals, Welch t-test, Mann-Whitney test, Pearson correlation, and a causal-inference warning. Saves an A/B experiment template with hypothesis, unit, primary metric, guardrails, alpha, confidence level, and power.

### Day 16: baseline model

Builds a time-aware user snapshot dataset. Features use only the 90 days before a snapshot; the label is whether the user rates something in the next 30 days. Trains and evaluates a class-weighted logistic-regression baseline.

### Day 17: PyTorch

Uses tensors, `TensorDataset`, `DataLoader`, an MLP, `BCEWithLogitsLoss`, Adam, training/validation history, CPU inference, and saved model weights.

### Day 18: feature engineering and comparison

Adds activity intensity, content diversity, recent activity share, and a rating variability proxy. Compares logistic regression and random forest, saves feature importance, misclassified samples, and a leakage audit.

### Day 19: Transformer and LLM basics

Uses MovieLens tags joined to primary genres for a transparent TF-IDF baseline. The optional Hugging Face pipeline demonstrates pre-trained Transformer inference; its output is explicitly treated as a toy experiment.

### Day 20: Spark

Runs a PySpark DataFrame workflow for ratings, daily metrics, content joins, window ranking, partition counts, and physical-plan inspection. The notebook wrapper is `notebooks/day20_pyspark_metrics.ipynb`.

### Day 21: finalization

Checks expected files, model outputs, and Week 2/3 DuckDB tables. Writes a final acceptance workbook, summary, and root `README.md`.

## Week 3 acceptance

- Statistics and A/B template completed.
- Logistic baseline has train/test split, metrics, and leakage-safe temporal features.
- PyTorch has train/validation metrics and saved weights.
- Model comparison includes errors and data leakage analysis.
- NLP/Transformer experiment records its model and limitations.
- PySpark shows groupBy, join, window, partitions, and shuffle/physical-plan evidence.
- Final README, model metrics, limitations, and reproducibility instructions are present.
