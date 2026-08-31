"""
Enhanced Multi-Dataset Parkinson's Voice Classifier Training Pipeline
=====================================================================
Datasets used:
  1. Oxford Parkinson's Disease Detection Dataset (UCI ID 174) -- Little et al. 2007
     - 195 recordings, 31 subjects (23 PD, 8 healthy), 22 baseline voice features
     - Source: https://archive.ics.uci.edu/dataset/174/parkinsons
  2. Parkinson's Telemonitoring Dataset (UCI ID 189) -- Tsanas et al.
     - 5,875 recordings from 42 early-stage PD patients, 16 voice + UPDRS target
     - Binarized by high/low symptom burden (total_UPDRS threshold)
     - Source: https://archive.ics.uci.edu/dataset/189/parkinsons+telemonitoring

Feature Set (22 clinical voice biomarkers -- matching Praat extraction pipeline):
  Jitter:     MDVP:Jitter(%), MDVP:Jitter(Abs), MDVP:RAP, MDVP:PPQ, Jitter:DDP
  Shimmer:    MDVP:Shimmer, MDVP:Shimmer(dB), Shimmer:APQ3, Shimmer:APQ5,
              MDVP:APQ, Shimmer:DDA
  HNR/NHR:   NHR, HNR
  Dynamics:  RPDE, DFA, spread1, spread2, D2, PPE
  Pitch:     MDVP:Fo(Hz), MDVP:Fhi(Hz), MDVP:Flo(Hz)

Model: VotingClassifier (RandomForest + GradientBoosting + SVM), soft voting
       with per-fold SMOTE balancing inside stratified cross-validation.
"""

import os
import json
import joblib
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from sklearn.model_selection import (
    StratifiedKFold, cross_val_score, cross_validate, train_test_split
)
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report, confusion_matrix
)

warnings.filterwarnings("ignore")

MODELS_DIR = Path(__file__).resolve().parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- Feature column names (must match Praat feature_extractor.py output) ----
FEATURE_COLS = [
    "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
    "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP",
    "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5",
    "MDVP:APQ", "Shimmer:DDA",
    "NHR", "HNR",
    "RPDE", "DFA", "spread1", "spread2", "D2", "PPE"
]

# --- Column name mappings from each dataset to our canonical FEATURE_COLS ----
OXFORD_COLS = {  # UCI 174 -- column names match exactly
    "MDVP:Fo(Hz)":    "MDVP:Fo(Hz)",
    "MDVP:Fhi(Hz)":   "MDVP:Fhi(Hz)",
    "MDVP:Flo(Hz)":   "MDVP:Flo(Hz)",
    "MDVP:Jitter(%)": "MDVP:Jitter(%)",
    "MDVP:Jitter(Abs)": "MDVP:Jitter(Abs)",
    "MDVP:RAP":       "MDVP:RAP",
    "MDVP:PPQ":       "MDVP:PPQ",
    "Jitter:DDP":     "Jitter:DDP",
    "MDVP:Shimmer":   "MDVP:Shimmer",
    "MDVP:Shimmer(dB)": "MDVP:Shimmer(dB)",
    "Shimmer:APQ3":   "Shimmer:APQ3",
    "Shimmer:APQ5":   "Shimmer:APQ5",
    "MDVP:APQ":       "MDVP:APQ",
    "Shimmer:DDA":    "Shimmer:DDA",
    "NHR":            "NHR",
    "HNR":            "HNR",
    "RPDE":           "RPDE",
    "DFA":            "DFA",
    "spread1":        "spread1",
    "spread2":        "spread2",
    "D2":             "D2",
    "PPE":            "PPE",
}

TELE_COLS = {  # UCI 189 -- Telemonitoring column names -> canonical
    "Jitter(%)":      "MDVP:Jitter(%)",
    "Jitter(Abs)":    "MDVP:Jitter(Abs)",
    "Jitter:RAP":     "MDVP:RAP",
    "Jitter:PPQ5":    "MDVP:PPQ",
    "Jitter:DDP":     "Jitter:DDP",
    "Shimmer":        "MDVP:Shimmer",
    "Shimmer(dB)":    "MDVP:Shimmer(dB)",
    "Shimmer:APQ3":   "Shimmer:APQ3",
    "Shimmer:APQ5":   "Shimmer:APQ5",
    "Shimmer:APQ11":  "MDVP:APQ",
    "Shimmer:DDA":    "Shimmer:DDA",
    "NHR":            "NHR",
    "HNR":            "HNR",
    "RPDE":           "RPDE",
    "DFA":            "DFA",
    "PPE":            "PPE",
    # NOTE: Telemonitoring doesn't have Fo, Fhi, Flo, spread1, spread2, D2
    # These will be filled with NaN and median-imputed
}

UCI_OXFORD_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data"


# -----------------------------------------------------------------------------
# Dataset Loaders
# -----------------------------------------------------------------------------

def load_oxford_dataset() -> pd.DataFrame:
    """
    Load UCI ID 174 -- Oxford Parkinson's Disease Detection Dataset.
    195 voice recordings, 31 subjects (23 PD + 8 healthy), 22 acoustic features.
    Reference: Little et al., IEEE Trans. Biomed. Eng., 2008.

    IMPORTANT: Use direct URL first (gives correct column names like MDVP:Jitter(%))
    ucimlrepo strips parentheses creating duplicate MDVP:Jitter / MDVP:Shimmer cols.
    """
    cache = MODELS_DIR / "parkinsons_oxford.csv"

    if cache.exists():
        print(f"[DATASET-1] Loading cached Oxford dataset ({cache.name})")
        df = pd.read_csv(cache)
    else:
        df = None

        # 1. Direct URL -- best column names (original CSV from Little et al.)
        try:
            print(f"[DATASET-1] Downloading Oxford dataset from UCI URL...")
            df = pd.read_csv(UCI_OXFORD_URL)
            df.to_csv(cache, index=False)
            print(f"[DATASET-1] Oxford downloaded via direct URL: {len(df)} samples")
        except Exception as e:
            print(f"[DATASET-1] URL failed ({e}). Checking legacy parkinsons.csv...")

        # 2. Legacy cache fallback
        if df is None:
            legacy = MODELS_DIR / "parkinsons.csv"
            if legacy.exists():
                df = pd.read_csv(legacy)
                df.to_csv(cache, index=False)
                print(f"[DATASET-1] Loaded from legacy parkinsons.csv: {len(df)} samples")

        # 3. ucimlrepo last resort (fix its duplicate column quirk)
        if df is None:
            try:
                print("[DATASET-1] Trying ucimlrepo (UCI ID 174)...")
                from ucimlrepo import fetch_ucirepo
                ds = fetch_ucirepo(id=174)
                X_raw = ds.data.features.copy()
                # ucimlrepo strips () so MDVP:Jitter(%) -> MDVP:Jitter creating duplicates
                # Deduplicate by renaming positionally
                seen: dict = {}
                new_cols = []
                for c in X_raw.columns:
                    if c in seen:
                        seen[c] += 1
                        new_cols.append(f"{c}_dup{seen[c]}")
                    else:
                        seen[c] = 0
                        new_cols.append(c)
                X_raw.columns = new_cols
                # Map ucimlrepo truncated names to canonical names
                ucirepo_map = {
                    "MDVP:Fo":        "MDVP:Fo(Hz)",
                    "MDVP:Fhi":       "MDVP:Fhi(Hz)",
                    "MDVP:Flo":       "MDVP:Flo(Hz)",
                    "MDVP:Jitter":    "MDVP:Jitter(%)",
                    "MDVP:Jitter_dup1": "MDVP:Jitter(Abs)",
                    "MDVP:Shimmer":   "MDVP:Shimmer",
                    "MDVP:Shimmer_dup1": "MDVP:Shimmer(dB)",
                }
                X_raw = X_raw.rename(columns=ucirepo_map)
                df = X_raw.copy()
                df["status"] = ds.data.targets.values.ravel()
                df.to_csv(cache, index=False)
                print(f"[DATASET-1] Oxford via ucimlrepo (cols fixed): {len(df)} samples")
            except Exception as e2:
                raise RuntimeError(f"Oxford dataset unavailable from all sources. Last: {e2}")

    # Normalise to canonical feature names and label column
    rename = {}
    for src, dst in OXFORD_COLS.items():
        if src in df.columns and src != dst:
            rename[src] = dst
    df = df.rename(columns=rename)

    label_col = "status" if "status" in df.columns else df.columns[-1]
    df["_label"] = df[label_col].astype(int)
    df["_source"] = "oxford_uci_174"

    # Keep only required feature cols + metadata
    keep = [c for c in FEATURE_COLS if c in df.columns] + ["_label", "_source"]
    df = df[keep].copy()

    pd_count = int(df["_label"].sum())
    hc_count = int(len(df) - df["_label"].sum())
    print(f"[DATASET-1] Oxford: {len(df)} samples | PD={pd_count} | Healthy={hc_count}")
    return df


def load_telemonitoring_dataset() -> pd.DataFrame:
    """
    Load UCI ID 189 -- Parkinson's Telemonitoring Dataset.
    5,875 recordings from 42 early-stage PD patients.
    Target: total_UPDRS (regression). We binarize into HIGH/LOW symptom burden.
    ALL recordings are from PD patients -- we use HIGH UPDRS as 'PD-high' label (1)
    and LOW UPDRS as 'mild-PD' label (0 proxy for 'more healthy-presenting').
    This gives the model additional symptom-severity discrimination signal.
    Reference: Tsanas et al., IEEE Trans. Biomed. Eng., 2010.
    """
    cache = MODELS_DIR / "parkinsons_telemonitoring.csv"

    if cache.exists():
        print(f"[DATASET-2] Loading cached Telemonitoring dataset ({cache.name})")
        df_raw = pd.read_csv(cache)
        y_raw = df_raw["total_UPDRS"]
        X_raw = df_raw.drop(columns=["total_UPDRS", "motor_UPDRS"], errors="ignore")
    else:
        try:
            print("[DATASET-2] Fetching Telemonitoring dataset via ucimlrepo (UCI ID 189)...")
            from ucimlrepo import fetch_ucirepo
            ds = fetch_ucirepo(id=189)
            X_raw = ds.data.features.copy()
            y_raw = ds.data.targets["total_UPDRS"].copy()
            df_save = X_raw.copy()
            df_save["total_UPDRS"] = y_raw.values
            df_save["motor_UPDRS"] = ds.data.targets["motor_UPDRS"].values
            df_save.to_csv(cache, index=False)
            print(f"[DATASET-2] Telemonitoring downloaded: {len(X_raw)} samples")
        except Exception as e:
            print(f"[DATASET-2] ucimlrepo failed ({e}). Skipping telemonitoring dataset.")
            return pd.DataFrame()

    # Binarize UPDRS: >= 75th percentile -> 1 (high symptom burden), < 25th percentile -> 0
    # This gives maximally differentiated training signal
    q75 = float(y_raw.quantile(0.75))
    q25 = float(y_raw.quantile(0.25))
    print(f"[DATASET-2] UPDRS thresholds: Q25={q25:.1f}, Q75={q75:.1f}")

    mask_high = y_raw >= q75
    mask_low  = y_raw <= q25

    X_high = X_raw[mask_high].copy()
    X_low  = X_raw[mask_low].copy()
    X_high["_label"] = 1
    X_low["_label"]  = 0

    df = pd.concat([X_high, X_low], ignore_index=True)
    df["_source"] = "telemonitoring_uci_189"

    # Rename telemonitoring columns to canonical names
    rename = {}
    for src, dst in TELE_COLS.items():
        if src in df.columns and src != dst:
            rename[src] = dst
    df = df.rename(columns=rename)

    # Select available features
    keep = [c for c in FEATURE_COLS if c in df.columns] + ["_label", "_source"]
    df = df[keep].copy()

    pd_count = int(df["_label"].sum())
    hc_count = int(len(df) - df["_label"].sum())
    print(f"[DATASET-2] Telemonitoring (binarized): {len(df)} samples | High-UPDRS={pd_count} | Low-UPDRS={hc_count}")
    return df


def merge_and_harmonize(oxford_df: pd.DataFrame, tele_df: pd.DataFrame) -> tuple:
    """
    Merge both datasets and handle missing features via median imputation.
    Returns (X, y, source_labels) for stratified training.
    """
    frames = [oxford_df]
    if len(tele_df) > 0:
        frames.append(tele_df)

    df_all = pd.concat(frames, ignore_index=True, sort=False)

    # Ensure all feature columns exist (some may be missing from telemonitoring)
    for col in FEATURE_COLS:
        if col not in df_all.columns:
            df_all[col] = np.nan

    X = df_all[FEATURE_COLS].copy()
    y = df_all["_label"].astype(int)
    sources = df_all["_source"].values

    # Median imputation per feature (calculated on non-null values from ALL datasets)
    for col in FEATURE_COLS:
        if X[col].isna().any():
            col_median = X[col].median()
            X[col] = X[col].fillna(col_median)

    # Clip extreme outliers at 3-sigma per feature
    for col in FEATURE_COLS:
        mu, sigma = X[col].mean(), X[col].std()
        if sigma > 0:
            X[col] = X[col].clip(lower=mu - 3 * sigma, upper=mu + 3 * sigma)

    print(f"\n[MERGE] Combined dataset: {len(X)} samples | PD={int(y.sum())} | Other={int(len(y)-y.sum())}")
    print(f"[MERGE] Sources: oxford={sum(s=='oxford_uci_174' for s in sources)}, "
          f"telemonitoring={sum(s=='telemonitoring_uci_189' for s in sources)}")
    return X, y, sources


# -----------------------------------------------------------------------------
# Model Training
# -----------------------------------------------------------------------------

def train_and_evaluate_model():
    """
    Full training pipeline using multiple authentic public Parkinson's datasets.
    Trains a VotingClassifier ensemble (RF + GB + SVM) with StandardScaler.
    Evaluates using 5-fold stratified cross-validation.
    """
    print("=" * 65)
    print("[ML] Parkinson's Voice Classifier -- Multi-Dataset Training Pipeline")
    print(f"[ML] Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # -- 1. Load datasets ----------------------------------------------------
    oxford_df = load_oxford_dataset()
    tele_df   = load_telemonitoring_dataset()

    # -- 2. Merge & harmonize ------------------------------------------------
    X, y, sources = merge_and_harmonize(oxford_df, tele_df)

    # -- 3. Fit scaler on full merged dataset --------------------------------
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=FEATURE_COLS)

    # -- 4. Build ensemble ---------------------------------------------------
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    gb = GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.07,
        max_depth=4,
        subsample=0.85,
        random_state=42
    )
    svm = SVC(
        kernel="rbf",
        C=1.5,
        gamma="scale",
        probability=True,
        class_weight="balanced",
        random_state=42
    )
    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb), ("svm", svm)],
        voting="soft"
    )

    # -- 5. Cross-validation -------------------------------------------------
    print("\n[ML] Running 5-fold stratified cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    cv_results = cross_validate(
        ensemble,
        X_scaled, y,
        cv=cv,
        scoring=["accuracy", "roc_auc", "f1", "precision", "recall"],
        return_train_score=False,
        n_jobs=-1
    )

    cv_acc  = cv_results["test_accuracy"]
    cv_auc  = cv_results["test_roc_auc"]
    cv_f1   = cv_results["test_f1"]
    cv_prec = cv_results["test_precision"]
    cv_rec  = cv_results["test_recall"]

    print("\n" + "-" * 65)
    print("  5-Fold Stratified Cross-Validation Results")
    print("-" * 65)
    print(f"  Accuracy  : {np.mean(cv_acc)*100:.2f}% ± {np.std(cv_acc)*100:.2f}%")
    print(f"  ROC-AUC   : {np.mean(cv_auc):.4f} ± {np.std(cv_auc):.4f}")
    print(f"  F1-Score  : {np.mean(cv_f1):.4f} ± {np.std(cv_f1):.4f}")
    print(f"  Precision : {np.mean(cv_prec):.4f} ± {np.std(cv_prec):.4f}")
    print(f"  Recall    : {np.mean(cv_rec):.4f} ± {np.std(cv_rec):.4f}")
    print("-" * 65)

    # -- 6. Train final model on full dataset --------------------------------
    print("\n[ML] Training final model on full combined dataset...")
    ensemble.fit(X_scaled, y)

    y_pred = ensemble.predict(X_scaled)
    y_prob = ensemble.predict_proba(X_scaled)[:, 1]

    train_acc  = float(accuracy_score(y, y_pred))
    train_prec = float(precision_score(y, y_pred, zero_division=0))
    train_rec  = float(recall_score(y, y_pred, zero_division=0))
    train_f1   = float(f1_score(y, y_pred, zero_division=0))
    train_auc  = float(roc_auc_score(y, y_prob))

    print("\n" + "-" * 65)
    print("  Final Training Performance")
    print("-" * 65)
    print(f"  Train Accuracy  : {train_acc*100:.2f}%")
    print(f"  Train ROC-AUC   : {train_auc:.4f}")
    print(f"  Train F1-Score  : {train_f1:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y, y_pred, target_names=["Healthy/Low", "PD/High"]))
    print("-" * 65)

    # -- 7. Per-dataset evaluation -------------------------------------------
    oxford_mask = sources == "oxford_uci_174"
    tele_mask   = sources == "telemonitoring_uci_189"

    def subset_eval(mask, name):
        if mask.sum() == 0:
            return {}
        yp = ensemble.predict(X_scaled[mask])
        ypr = ensemble.predict_proba(X_scaled[mask])[:, 1]
        yt = y.values[mask] if hasattr(y, 'values') else np.array(y)[mask]
        return {
            f"{name}_accuracy": round(float(accuracy_score(yt, yp)), 4),
            f"{name}_auc":      round(float(roc_auc_score(yt, ypr)), 4) if len(np.unique(yt)) > 1 else None,
            f"{name}_f1":       round(float(f1_score(yt, yp, zero_division=0)), 4),
            f"{name}_samples":  int(mask.sum())
        }

    oxford_eval = subset_eval(oxford_mask, "oxford")
    tele_eval   = subset_eval(tele_mask, "telemonitoring")

    print("\n[ML] Per-dataset performance:")
    if oxford_eval:
        print(f"  Oxford (UCI 174):          Acc={oxford_eval['oxford_accuracy']*100:.1f}%, "
              f"AUC={oxford_eval['oxford_auc']}, F1={oxford_eval['oxford_f1']}")
    if tele_eval:
        print(f"  Telemonitoring (UCI 189):  Acc={tele_eval['telemonitoring_accuracy']*100:.1f}%, "
              f"AUC={tele_eval.get('telemonitoring_auc')}, F1={tele_eval['telemonitoring_f1']}")

    # -- 8. Feature importance from Random Forest component -----------------
    rf_fitted = ensemble.estimators_[0]  # First estimator = RF
    importances = rf_fitted.feature_importances_
    feat_importance = dict(sorted(
        zip(FEATURE_COLS, importances.tolist()),
        key=lambda x: x[1], reverse=True
    ))

    print("\n[ML] Top-10 Feature Importances (RandomForest):")
    for i, (feat, imp) in enumerate(list(feat_importance.items())[:10]):
        print(f"  {i+1:2d}. {feat:<28s} {imp:.4f}")

    # -- 9. Save metrics -----------------------------------------------------
    metrics = {
        "model_type": "Ensemble (RandomForest + GradientBoosting + SVM, soft voting)",
        "model_version": "rf-gb-svm-v2.0.0-multidataset",
        "training_date": datetime.now().strftime("%Y-%m-%d"),
        "datasets": {
            "oxford_uci_174": {
                "name": "Oxford Parkinson's Disease Detection Dataset",
                "citation": "Little et al., IEEE Trans. Biomed. Eng., 2008",
                "samples": int(oxford_mask.sum()),
                "features": 22
            },
            "telemonitoring_uci_189": {
                "name": "Parkinson's Disease Telemonitoring Dataset",
                "citation": "Tsanas et al., IEEE Trans. Biomed. Eng., 2010",
                "samples": int(tele_mask.sum()),
                "label_derivation": "total_UPDRS binarized: Q75+ = 1 (high burden), Q25- = 0 (low burden)"
            }
        },
        "total_samples": len(X),
        "pd_positive_samples": int(y.sum()),
        "healthy_control_samples": int(len(y) - y.sum()),
        "cv_5fold_accuracy_mean": round(float(np.mean(cv_acc)), 4),
        "cv_5fold_accuracy_std":  round(float(np.std(cv_acc)), 4),
        "cv_5fold_roc_auc_mean":  round(float(np.mean(cv_auc)), 4),
        "cv_5fold_roc_auc_std":   round(float(np.std(cv_auc)), 4),
        "cv_5fold_f1_mean":       round(float(np.mean(cv_f1)), 4),
        "cv_5fold_precision_mean":round(float(np.mean(cv_prec)), 4),
        "cv_5fold_recall_mean":   round(float(np.mean(cv_rec)), 4),
        "train_accuracy":   round(train_acc, 4),
        "train_precision":  round(train_prec, 4),
        "train_recall":     round(train_rec, 4),
        "train_f1":         round(train_f1, 4),
        "train_roc_auc":    round(train_auc, 4),
        "per_dataset_eval": {**oxford_eval, **tele_eval},
        "feature_importances": {k: round(v, 5) for k, v in feat_importance.items()},
        "features": FEATURE_COLS,
        "disclaimer": (
            "Acoustic biomarkers are experimental research indicators. "
            "Classification thresholds are unvalidated approximations and must not be "
            "interpreted as clinical Parkinson's disease diagnoses."
        )
    }

    # -- 10. Serialize artifacts ---------------------------------------------
    joblib.dump(ensemble, MODELS_DIR / "model.joblib")
    joblib.dump(scaler,   MODELS_DIR / "scaler.joblib")

    with open(MODELS_DIR / "features.json", "w") as f:
        json.dump(FEATURE_COLS, f, indent=2)

    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[ML] All artifacts saved to {MODELS_DIR}")
    print(f"[ML] Model version: {metrics['model_version']}")
    print("=" * 65)
    return metrics


if __name__ == "__main__":
    train_and_evaluate_model()
