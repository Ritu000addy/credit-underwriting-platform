from pathlib import Path

import joblib
import pandas as pd 
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score

BASE_DIR = Path(__file__).resolve().parents[3]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "credit_risk_training.csv"
)

MODEL_DIR = BASE_DIR / "data" / "synthetic" / "models"

MODEL_PATH = MODEL_DIR / "credit_risk_model.joblib"

TARGET_COLUMN = "default_flag"

def main() -> None:

    print("Loading training data...")

    df = pd.read_csv(DATA_PATH)

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    print(f"Dataset shape: {df.shape}")
    print(f"Feature count: {X.shape[1]}")

    print(f"Target distribution:\n{y.value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        stratify=y,
        random_state=42,
    )

    model = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )

    print("\nTraining model...")

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(X_test)[:,1]

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    if len(y_test.unique()) == 2:
        auc = roc_auc_score(
            y_test,
            probabilities,
        )

        print(f"ROC-AUC: {auc:.4f}")

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok = True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print(f"\nModel saved to:")
    print(MODEL_PATH)

if __name__ == "__main__":
    main()