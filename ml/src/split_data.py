import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# Load dataset
data_dir = Path(__file__).resolve().parent.parent / "data"
csv_file = next(data_dir.glob("*.csv"))

df = pd.read_csv(csv_file)

# Separate features and target
X = df.drop(columns=["LoanID", "Default"])
y = df["Default"]

# Split dataset: 80% training, 20% testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Display results
print("Training Features:", X_train.shape)
print("Testing Features:", X_test.shape)

print("\nTraining Target Distribution:")
print(y_train.value_counts(normalize=True).round(4) * 100)

print("\nTesting Target Distribution:")
print(y_test.value_counts(normalize=True).round(4) * 100)