import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# 1. Load data
df = pd.read_csv('gesture_dataset.csv')
X  = df.drop('label', axis=1).values
y  = df['label'].values

# 2. Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print('Classes:', le.classes_)

# 3. Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, stratify=y_encoded, random_state=42)
print(f'Train: {len(X_train)}  |  Test: {len(X_test)}')

# 4. Train
print('\nTraining MLP...')
model = MLPClassifier(
    hidden_layer_sizes=(128, 64),
    activation='relu',
    solver='adam',
    max_iter=500,
    random_state=42,
    verbose=True
)
model.fit(X_train, y_train)
print('Training complete.')

# 5. Evaluate
y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f'\nTest Accuracy: {acc * 100:.2f}%')
print('\nClassification Report:')
print(classification_report(y_test, y_pred, target_names=le.classes_))

# 6. Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title('Confusion Matrix — MLP Gesture Classifier')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()
plt.savefig('confusion_matrix.png')
print('Saved confusion_matrix.png')

# 7. Training loss curve
plt.figure(figsize=(8, 5))
plt.plot(model.loss_curve_)
plt.title('MLP Training Loss Curve')
plt.xlabel('Iteration')
plt.ylabel('Loss')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('training_loss_curve.png')
print('Saved training_loss_curve.png')

# 8. Save model
joblib.dump(model, 'gesture_model.pkl')
joblib.dump(le,    'label_encoder.pkl')
print('Saved gesture_model.pkl')
print('Saved label_encoder.pkl')
