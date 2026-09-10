#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import sys
# Add the path to the cognition_perception package so we can import hand_features
sys.path.append('/home/j/cognition_ws/src/cognition_perception/cognition_perception')
from hand_features import extract_features_from_row

# 1. Load data
df = pd.read_csv('gesture_dataset.csv')
print(f"Dataset shape: {df.shape}")

# 2. Extract features from each row
X_list = []
y_list = []
for idx, row in df.iterrows():
    vals = row.drop('label').values.astype(float)
    feats = extract_features_from_row(vals)
    X_list.append(feats)
    y_list.append(row['label'])

X = np.array(X_list)
y = np.array(y_list)
print(f"Feature vector length: {X.shape[1]}")

# 3. Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print('Classes:', le.classes_)

# 4. Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, stratify=y_encoded, random_state=42)
print(f'Train: {len(X_train)}  |  Test: {len(X_test)}')

# 5. Noise augmentation
augment = True
if augment:
    noise_std = 0.03
    X_aug = X_train.copy()
    y_aug = y_train.copy()
    for _ in range(3):  # 3x augmentation
        noise = np.random.normal(0, noise_std, X_train.shape)
        X_aug = np.vstack([X_aug, X_train + noise])
        y_aug = np.hstack([y_aug, y_train])
    X_train = X_aug
    y_train = y_aug
    print(f'Augmented training size: {len(X_train)}')
    # Additional augmentation: rotation noise and scaling
    angle_noise_std = 10  # degrees
    dist_scale_std = 0.05
    # Add noise to angle features (indices 13,14,15)
    X_train[:, 13] += np.random.normal(0, angle_noise_std, X_train.shape[0])
    X_train[:, 14] += np.random.normal(0, angle_noise_std, X_train.shape[0])
    X_train[:, 15] += np.random.normal(0, angle_noise_std, X_train.shape[0])
    # Scale distance features (indices 8-12)
    dist_scale = np.random.normal(1, dist_scale_std, (X_train.shape[0], 5))
    X_train[:, 8:13] *= dist_scale
    print(f"Added rotation and scaling augmentation")

# 6. Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 7. Train MLP
print('\nTraining MLP...')
model = MLPClassifier(
    hidden_layer_sizes=(128, 64),
    activation='relu',
    solver='adam',
    max_iter=500,
    random_state=42,
    verbose=True
)
model.fit(X_train_scaled, y_train)
print('Training complete.')

# 8. Evaluate
y_pred = model.predict(X_test_scaled)
acc = accuracy_score(y_test, y_pred)
print(f'\nTest Accuracy: {acc * 100:.2f}%')
print('\nClassification Report:')
print(classification_report(y_test, y_pred, target_names=le.classes_))

# 9. Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title('Confusion Matrix — Feature‑based MLP')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()
plt.savefig('confusion_matrix_features.png')
print('Saved confusion_matrix_features.png')

# 10. Save model, scaler, and label encoder
joblib.dump(model, 'gesture_model_features.pkl')
joblib.dump(scaler, 'scaler_features.pkl')
joblib.dump(le, 'label_encoder_features.pkl')
print('Saved gesture_model_features.pkl, scaler_features.pkl, label_encoder_features.pkl')
