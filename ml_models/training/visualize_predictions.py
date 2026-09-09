import pandas as pd, numpy as np
import torch, torch.nn as nn
import matplotlib.pyplot as plt
import joblib
from sklearn.model_selection import train_test_split

class TrajectoryLSTM(nn.Module):
    def __init__(self, input_size=2, hidden=64, layers=2, pred_len=5):
        super().__init__()
        self.lstm     = nn.LSTM(input_size, hidden, layers,
                                batch_first=True, dropout=0.2)
        self.fc       = nn.Linear(hidden, pred_len * 2)
        self.pred_len = pred_len
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :]).view(-1, self.pred_len, 2)

# Load model
net = TrajectoryLSTM()
net.load_state_dict(torch.load('path_predictor.pt', map_location='cpu'))
net.eval()

# Load data
df      = pd.read_csv('trajectory_dataset.csv')
data_3d = df.values.astype(np.float32).reshape(len(df), 15, 2)
X       = data_3d[:, :10, :]
y       = data_3d[:, 10:, :]
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

with torch.no_grad():
    y_pred = net(torch.tensor(X_test)).numpy()

# Plot 6 examples
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()

for i, ax in enumerate(axes):
    if i >= len(X_test):
        break
    hist = X_test[i]       # 10 history points
    true = y_test[i]       # 5 true future points
    pred = y_pred[i]       # 5 predicted future points

    # Scale to pixels
    H, W = 480, 640
    ax.plot(hist[:,0]*W, hist[:,1]*H,
            'o-', color='steelblue', linewidth=2, label='History (known)')
    ax.plot(true[:,0]*W, true[:,1]*H,
            's--', color='green', linewidth=2, label='True future')
    ax.plot(pred[:,0]*W, pred[:,1]*H,
            '^--', color='red',   linewidth=2, label='LSTM predicted')

    # Connect last history point to first future point
    ax.plot([hist[-1,0]*W, true[0,0]*W],
            [hist[-1,1]*H, true[0,1]*H], 'k:', linewidth=1)

    ax.set_xlim(0, W); ax.set_ylim(H, 0)
    ax.set_title(f'Sample {i+1}')
    ax.set_xlabel('X (px)'); ax.set_ylabel('Y (px)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

plt.suptitle('LSTM Path Prediction — History vs True vs Predicted',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('path_prediction_examples.png', dpi=300)
print('Saved: path_prediction_examples.png')
