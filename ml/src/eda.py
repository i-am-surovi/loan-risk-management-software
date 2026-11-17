
import pandas as pd
from pathlib import Path

# Load dataset
data_dir = Path(__file__).resolve().parent.parent / "data"
csv_files = list(data_dir.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError("No CSV dataset found in ml/data")

df = pd.read_csv(csv_files[0])

print("Dataset:", csv_files[0].name)
print("Shape:", df.shape)

# Duplicate analysis
print("\n--- Duplicate Analysis ---")
print("Duplicate rows:", df.duplicated().sum())
print("Duplicate LoanIDs:", df["LoanID"].duplicated().sum())

# Target distribution
print("\n--- Target Distribution ---")
print(df["Default"].value_counts())
print("\nPercentage:")
print((df["Default"].value_counts(normalize=True) * 100).round(2))

# Numerical feature analysis
print("\n--- Numerical Features ---")
print(df.select_dtypes(include="number").describe().round(2))

# Categorical feature analysis
print("\n--- Categorical Features ---")
categorical_columns = df.select_dtypes(include="str").columns

for column in categorical_columns:
    if column != "LoanID":
        print(f"\n{column}:")
        print(df[column].value_counts())


# Feature and target separation
print("\n--- Feature and Target Separation ---")

X = df.drop(columns=["LoanID", "Default"])
y = df["Default"]

print("Feature shape:", X.shape)
print("Target shape:", y.shape)

print("\nFeatures:")
print(X.columns.tolist())

print("\nTarget classes:")
print(y.value_counts())