
import pandas as pd
import numpy as np
import json

from pathlib import Path
from sklearn.model_selection import train_test_split

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)

from imblearn.over_sampling import SMOTENC
from catboost import CatBoostClassifier


# 1. Load dataset
data_dir = Path(__file__).resolve().parent.parent / "data"
csv_file = data_dir / "Loan_default.csv"

df = pd.read_csv(csv_file)

X = df.drop(columns=["LoanID", "Default"])
y = df["Default"]

categorical_features = X.select_dtypes(
    include=["object", "str"]
).columns.tolist()


# 2. Train-validation-test split
X_train_full, X_test, y_train_full, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

X_train, X_val, y_train, y_val = train_test_split(
    X_train_full, y_train_full,
    test_size=0.15,
    random_state=42,
    stratify=y_train_full
)

print("Training:", X_train.shape)
print("Validation:", X_val.shape)
print("Testing:", X_test.shape)


# 3. Apply SMOTENC only to training data
smotenc = SMOTENC(
    categorical_features=categorical_features,
    sampling_strategy=0.5,
    random_state=42,
    k_neighbors=5
)

X_train_resampled, y_train_resampled = smotenc.fit_resample(
    X_train, y_train
)

print("\nResampled distribution:")
print(y_train_resampled.value_counts())


# 4. Train CatBoost
model = CatBoostClassifier(
    iterations=1500,
    learning_rate=0.03,
    depth=8,
    loss_function="Logloss",
    eval_metric="AUC",
    cat_features=categorical_features,
    random_seed=42,
    verbose=100,
    allow_writing_files=False
)

print("\nTraining CatBoost...")

model.fit(
    X_train_resampled,
    y_train_resampled,
    eval_set=(X_val, y_val),
    early_stopping_rounds=150
)

print("\nBest iteration:", model.best_iteration_)


# 5. Optimize threshold using validation data
y_val_prob = model.predict_proba(X_val)[:, 1]

thresholds = np.arange(0.05, 0.96, 0.01)
results = []

for threshold in thresholds:

    y_val_pred = (y_val_prob >= threshold).astype(int)

    results.append({
        "Threshold": round(threshold, 2),
        "Precision": precision_score(
            y_val, y_val_pred, zero_division=0
        ),
        "Recall": recall_score(
            y_val, y_val_pred, zero_division=0
        ),
        "F1": f1_score(
            y_val, y_val_pred, zero_division=0
        ),
        "F2": fbeta_score(
            y_val, y_val_pred, beta=2, zero_division=0
        )
    })

results_df = pd.DataFrame(results)

best_result = results_df.loc[results_df["F2"].idxmax()]
best_threshold = float(best_result["Threshold"])

print("\nBest Validation Threshold:")
print(best_result)

print("\nTop 10 Thresholds:")
print(
    results_df.sort_values(
        by="F2", ascending=False
    ).head(10).to_string(index=False)
)


# 6. Final evaluation on untouched test data
y_test_prob = model.predict_proba(X_test)[:, 1]

y_test_pred = (
    y_test_prob >= best_threshold
).astype(int)

print("\n--- Final Test Evaluation ---")
print("Selected Threshold:", best_threshold)

print("Accuracy:", round(
    accuracy_score(y_test, y_test_pred), 4
))

print("Precision:", round(
    precision_score(y_test, y_test_pred, zero_division=0), 4
))

print("Recall:", round(
    recall_score(y_test, y_test_pred, zero_division=0), 4
))

print("F1 Score:", round(
    f1_score(y_test, y_test_pred, zero_division=0), 4
))

print("F2 Score:", round(
    fbeta_score(y_test, y_test_pred, beta=2, zero_division=0), 4
))

print("ROC-AUC:", round(
    roc_auc_score(y_test, y_test_prob), 4
))

print("PR-AUC:", round(
    average_precision_score(y_test, y_test_prob), 4
))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_test_pred))

print("\nClassification Report:")
print(classification_report(
    y_test, y_test_pred, zero_division=0
))

# Save trained model and selected threshold

model_dir = Path(__file__).resolve().parent.parent / "models"
model_dir.mkdir(parents=True, exist_ok=True)

# Save CatBoost model
model.save_model(str(model_dir / "catboost_model.cbm"))

# Save threshold
threshold_data = {
    "threshold": best_threshold,
    "optimization_metric": "F2",
    "validation_f2": float(best_result["F2"])
}

with open(model_dir / "threshold.json", "w") as file:
    json.dump(threshold_data, file, indent=4)

print("\nModel and threshold saved successfully!")

print("\nThreshold optimization completed!")
