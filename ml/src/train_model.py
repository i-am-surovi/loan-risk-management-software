
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    classification_report,
    confusion_matrix
)

from imblearn.over_sampling import SMOTENC
from catboost import CatBoostClassifier

# Load dataset
data_dir = Path(__file__).resolve().parent.parent / "data"
csv_file = next(data_dir.glob("*.csv"))
df = pd.read_csv(csv_file)

# Separate features and target
X = df.drop(columns=["LoanID", "Default"])
y = df["Default"]

# Identify categorical features
categorical_features = X.select_dtypes(
    include=["str", "object"]
).columns.tolist()

# Split into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Split training data again for validation
X_train_sub, X_val, y_train_sub, y_val = train_test_split(
    X_train,
    y_train,
    test_size=0.15,
    random_state=42,
    stratify=y_train
)

print("Original training distribution:")
print(y_train_sub.value_counts())

# Apply SMOTENC only to training subset
smotenc = SMOTENC(
    categorical_features=categorical_features,
    sampling_strategy=0.5,
    random_state=42,
    k_neighbors=5
)

X_train_resampled, y_train_resampled = smotenc.fit_resample(
    X_train_sub,
    y_train_sub
)

print("\nAfter SMOTENC:")
print(y_train_resampled.value_counts())

# Create CatBoost model
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

# Train model
print("\nTraining CatBoost with SMOTENC...")

model.fit(
    X_train_resampled,
    y_train_resampled,
    eval_set=(X_val, y_val),
    early_stopping_rounds=150,
    verbose=100
)

# Predict on untouched test data
y_pred = model.predict(X_test).ravel()
y_prob = model.predict_proba(X_test)[:, 1]

# Evaluation
print("\n--- CatBoost + SMOTENC Evaluation ---")

print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
print("Precision:", round(precision_score(y_test, y_pred), 4))
print("Recall:", round(recall_score(y_test, y_pred), 4))
print("F1 Score:", round(f1_score(y_test, y_pred), 4))
print("ROC-AUC:", round(roc_auc_score(y_test, y_prob), 4))
print("PR-AUC:", round(average_precision_score(y_test, y_prob), 4))

print("\n--- Classification Report ---")
print(classification_report(y_test, y_pred))

print("\n--- Confusion Matrix ---")
print(confusion_matrix(y_test, y_pred))

print("\nSMOTENC + CatBoost training completed!")
