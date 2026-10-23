import json
import random
from datetime import date

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from common import OUTPUT_DIR
from week3_common import MODEL_FEATURES, ensure_model_dir, save_excel


def main() -> None:
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError as error:
        raise RuntimeError(
            "PyTorch is not installed in the active Miniconda environment. "
            "Install it before running Day 17: "
            "python -m pip install torch"
        ) from error

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    dataset_path = OUTPUT_DIR / "ml_day16_model_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(
            "Run code/day16_logistic_baseline.py before Day 17."
        )
    dataset = pd.read_csv(dataset_path)
    dataset["snapshot_cutoff"] = pd.to_datetime(dataset["snapshot_cutoff"])
    cutoffs = sorted(dataset["snapshot_cutoff"].unique())
    train_frame = dataset[dataset["snapshot_cutoff"] == cutoffs[0]].copy()
    test_frame = dataset[dataset["snapshot_cutoff"] == cutoffs[-1]].copy()

    train_part, validation_part = train_test_split(
        train_frame,
        test_size=0.2,
        random_state=42,
        stratify=train_frame["target_future_active"],
    )
    center = train_part[MODEL_FEATURES].mean()
    scale = train_part[MODEL_FEATURES].std().replace(0, 1).fillna(1)

    def tensor_frame(frame):
        values = ((frame[MODEL_FEATURES] - center) / scale).to_numpy(
            dtype=np.float32
        )
        labels = frame["target_future_active"].to_numpy(dtype=np.float32)
        return torch.tensor(values), torch.tensor(labels).reshape(-1, 1)

    x_train, y_train = tensor_frame(train_part)
    x_validation, y_validation = tensor_frame(validation_part)
    x_test, y_test = tensor_frame(test_frame)
    train_loader = DataLoader(
        TensorDataset(x_train, y_train),
        batch_size=1024,
        shuffle=True,
    )

    class ActivityMLP(nn.Module):
        def __init__(self, input_size):
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(input_size, 32),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(32, 16),
                nn.ReLU(),
                nn.Linear(16, 1),
            )

        def forward(self, features):
            return self.network(features)

    model = ActivityMLP(len(MODEL_FEATURES))
    positive = float(y_train.sum())
    negative = float(len(y_train) - positive)
    pos_weight = torch.tensor([negative / max(positive, 1.0)])
    loss_function = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    history = []
    for epoch in range(1, 21):
        model.train()
        train_losses = []
        for features, labels in train_loader:
            optimizer.zero_grad()
            loss = loss_function(model(features), labels)
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))

        model.eval()
        with torch.no_grad():
            validation_loss = float(
                loss_function(model(x_validation), y_validation).item()
            )
        history.append(
            {
                "epoch": epoch,
                "train_loss": float(np.mean(train_losses)),
                "validation_loss": validation_loss,
            }
        )

    model.eval()
    with torch.no_grad():
        probabilities = torch.sigmoid(model(x_test)).numpy().ravel()

    from week3_common import classification_metrics

    metrics, predictions = classification_metrics(
        test_frame["target_future_active"],
        probabilities,
    )
    metrics.update(
        {
            "model": "pytorch_mlp",
            "train_rows": len(train_part),
            "validation_rows": len(validation_part),
            "test_rows": len(test_frame),
            "epochs": 20,
            "device": "cpu",
        }
    )
    metrics_frame = pd.DataFrame([metrics])
    history_frame = pd.DataFrame(history)

    model_dir = ensure_model_dir()
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "features": MODEL_FEATURES,
            "center": center.to_dict(),
            "scale": scale.to_dict(),
        },
        model_dir / "day17_pytorch_mlp.pt",
    )
    with (model_dir / "day17_pytorch_metadata.json").open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "features": MODEL_FEATURES,
                "device": "cpu",
                "epochs": 20,
            },
            file,
            indent=2,
        )

    predictions_frame = test_frame[
        ["user_id", "snapshot_cutoff", "target_future_active"]
    ].copy()
    predictions_frame["predicted"] = predictions
    predictions_frame["predicted_probability"] = probabilities
    output = save_excel(
        {
            "metrics": metrics_frame,
            "training_history": history_frame,
            "test_predictions": predictions_frame.head(10000),
        },
        "ml_day17_pytorch_mlp.xlsx",
    )
    metrics_frame.to_csv(
        OUTPUT_DIR / "ml_day17_pytorch_metrics.csv",
        index=False,
        encoding="utf-8-sig",
    )
    history_frame.to_csv(
        OUTPUT_DIR / "ml_day17_pytorch_training_history.csv",
        index=False,
        encoding="utf-8-sig",
    )
    report = f"""# Day 17: PyTorch MLP

## Model

The model uses a custom PyTorch `Dataset` through `TensorDataset`, an MLP with two hidden layers, `BCEWithLogitsLoss`, Adam, mini-batch training, and a separate validation split from the earlier training snapshot. The later snapshot is kept for temporal test evaluation.

## Metrics

{metrics_frame.to_string(index=False)}

## Training artifacts

- Model weights: `models/day17_pytorch_mlp.pt`.
- Training history: `days/ml_day17_pytorch_training_history.csv`.
- Feature names and scaling statistics are saved with the weights.

## Limitations

This is a CPU baseline for a future-activity proxy. It is not a production recommendation or churn model. The next day compares it with a scikit-learn model and examines errors and leakage.

Generated on: {date.today().isoformat()}
"""
    (OUTPUT_DIR / "ml_day17_pytorch_mlp.md").write_text(report, encoding="utf-8")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
