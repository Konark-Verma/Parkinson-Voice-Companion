# Dataset & Data Pipeline Architecture Frame

> **Document:** Dataset & Feature Extraction Architecture Frame  
> **Project:** Parkinson's Voice Companion  
> **Course:** Machine Learning (DA-2 Submission)  

---

## 1. Overview & Dataset Framing

The dataset pipeline is engineered to ingest acoustic voice recordings, validate audio signal quality, extract 22 standardized clinical vocal biomarkers via Praat/Parselmouth, normalize features using Z-score scaling, and execute ensemble classification.

The system handles both benchmark datasets (UCI Oxford & UCI Telemonitoring) and synthetic/mock demonstration datasets (`mock_parkinsons_dataset_500.csv`) under a unified schema frame.

---

## 2. Dataset Pipeline Architecture Frame (Diagram)

```
+-----------------------------------------------------------------------------------+
|                            1. DATASET SOURCES / INPUTS                            |
|  * UCI Oxford Parkinson's Dataset (195 audio samples, 31 subjects)                |
|  * UCI Telemonitoring Dataset (2,946 voice samples, 42 subjects)                  |
|  * Patient Microphone Uploads (WAV Audio, >= 16kHz, >= 2.0s)                      |
|  * Demo Mock Dataset (mock_parkinsons_dataset_500.csv, 500 samples)               |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                   2. DATA QUALITY & SIGNAL VALIDATION LAYER                       |
|  * Duration Check: Audio duration >= 2.0 seconds                                  |
|  * Signal Energy Check: RMS amplitude >= 0.005 (rejects ambient silence)           |
|  * Sample Rate Standardizer: >= 16,000 Hz                                         |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|               3. ACOUSTIC FEATURE EXTRACTION LAYER (PARSELMOUTH)                  |
|  Extracts 22 Clinical Biomarkers:                                                 |
|  * Fundamental Frequency: MDVP:Fo(Hz), MDVP:Fhi(Hz), MDVP:Flo(Hz)                 |
|  * Jitter (Pitch Perturbation): Jitter(%), Jitter(Abs), RAP, PPQ, Jitter:DDP      |
|  * Shimmer (Amplitude Perturbation): Shimmer, Shimmer(dB), APQ3, APQ5, APQ, DDA  |
|  * Noise Measures: NHR (Noise-to-Harmonics), HNR (Harmonics-to-Noise)             |
|  * Non-linear Complexity: RPDE, DFA, spread1, spread2, D2, PPE                    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|               4. FEATURE NORMALIZATION & TRANSFORMATION FRAME                     |
|  * StandardScaler: Z-score transformation (mu=0, sigma=1)                        |
|  * Outlier & Infinite Value Masking                                               |
|  * 5-Fold Stratified Cross-Validation Splitter (80% Train / 20% Test)             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|               5. ENSEMBLE MODEL TRAINING & INFERENCE FRAME                        |
|  * VotingClassifier (Soft Probability Integration)                                |
|    |-- Random Forest (200 Trees, max_depth=12)                                    |
|    |-- Gradient Boosting (150 Estimators, lr=0.05)                               |
|    |-- Support Vector Classifier (SVC RBF Kernel, C=2.0)                          |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|               6. PERSISTENCE & DOWNSTREAM CLINICAL ALERTS ENGINE                  |
|  * SQLite WAL Persistence: voice_samples, extracted_features                      |
|  * Rolling Sigma Change-Point Detection (CUSUM Algorithm for Sudden Shifts)       |
|  * Medication Wearing-Off Correlation (+/-2h dosing window match)                 |
+-----------------------------------------------------------------------------------+
```

---

## 3. Dataset Feature Architecture Schema

All datasets processed by the system conform to the standard 22-feature clinical acoustic matrix:

| Feature Name | Category | Clinical Description |
|---|---|---|
| `MDVP:Fo(Hz)` | Fundamental Frequency | Average vocal pitch frequency in Hertz |
| `MDVP:Fhi(Hz)` | Fundamental Frequency | Maximum vocal pitch frequency in Hertz |
| `MDVP:Flo(Hz)` | Fundamental Frequency | Minimum vocal pitch frequency in Hertz |
| `MDVP:Jitter(%)` | Pitch Perturbation | Relative cycle-to-cycle frequency variation percentage |
| `MDVP:Jitter(Abs)` | Pitch Perturbation | Absolute cycle-to-cycle frequency variation in microseconds |
| `MDVP:RAP` | Pitch Perturbation | Relative Amplitude Perturbation |
| `MDVP:PPQ` | Pitch Perturbation | 5-point Period Perturbation Quotient |
| `Jitter:DDP` | Pitch Perturbation | Average absolute difference of consecutive jitter differences |
| `MDVP:Shimmer` | Amplitude Perturbation | Local amplitude variation percentage |
| `MDVP:Shimmer(dB)` | Amplitude Perturbation | Local amplitude variation in decibels |
| `Shimmer:APQ3` | Amplitude Perturbation | 3-point Amplitude Perturbation Quotient |
| `Shimmer:APQ5` | Amplitude Perturbation | 5-point Amplitude Perturbation Quotient |
| `MDVP:APQ` | Amplitude Perturbation | 11-point Amplitude Perturbation Quotient |
| `Shimmer:DDA` | Amplitude Perturbation | Average absolute difference of consecutive shimmer differences |
| `NHR` | Signal Noise | Noise-to-Harmonics Ratio |
| `HNR` | Signal Noise | Harmonics-to-Noise Ratio (dB) |
| `RPDE` | Non-linear Dynamics | Recurrence Period Density Entropy |
| `DFA` | Non-linear Dynamics | Detrended Fluctuation Analysis signal exponent |
| `spread1` | Frequency Variation | Non-linear fundamental frequency variation measure 1 |
| `spread2` | Frequency Variation | Non-linear fundamental frequency variation measure 2 |
| `D2` | Non-linear Dynamics | Correlation Dimension |
| `PPE` | Pitch Dynamics | Pitch Period Entropy |
| `status` | Target Label | `0` = Healthy Control, `1` = Parkinson's Disease |

---

## 4. Alignment of Real & Mock Datasets

The mock dataset (`mock_parkinsons_dataset_500.csv`) is generated with identical feature architecture, maintaining statistical distributions derived from the UCI Oxford benchmark:
- **Healthy Controls ($S_0$):** High HNR ($\mu = 25.5\text{ dB}$), low Jitter ($\mu = 0.0032$), low Shimmer ($\mu = 0.018$), low DFA ($\mu = 0.63$).
- **Parkinson's Samples ($S_1$):** Reduced HNR ($\mu = 18.0\text{ dB}$), elevated Jitter ($\mu = 0.0088$), elevated Shimmer ($\mu = 0.045$), elevated DFA ($\mu = 0.76$).
