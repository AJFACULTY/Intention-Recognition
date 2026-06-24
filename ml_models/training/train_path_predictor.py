import pandas as pd, numpy as np
import torch, torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
import joblib, matplotlib.pyplot as plt

# ── 1. Load trajectories ───────────────────────────────────────
df = pd.read_csv('trajectory_dataset.csv')
print(f'Dataset: {df.shape[0]} sequences, {df.shape[1]} columns')
print(f'Any nulls: {df.isnull().sum().sum()}')

data   = df.values.astype(np.float32)
N, SEQ = data.shape[0], 15
data_3d = data.reshape(N, SEQ, 2)

# Input: first 10 frames → predict next 5 frames
X = data_3d[:, :10, :]
y = data_3d[:, 10:, :]
print(f'X shape: {X.shape}  →  y shape: {y.shape}')

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)
print(f'Train: {len(X_train)}  |  Test: {len(X_test)}')

X_tr = torch.tensor(X_train); y_tr = torch.tensor(y_train)
X_te = torch.tensor(X_test);  y_te = torch.tensor(y_test)
loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=16, shuffle=True)

# ── 2. LSTM model ──────────────────────────────────────────────
class TrajectoryLSTM(nn.Module):
    def __init__(self, input_size=2, hidden=64, layers=2, pred_len=5):
        super().__init__()
        self.lstm    = nn.LSTM(input_size, hidden, layers,
                               batch_first=True, dropout=0.2)
        self.fc      = nn.Linear(hidden, pred_len * 2)
        self.pred_len = pred_len

    def forward(self, x):
        out, _ = self.lstm(x)
        pred   = self.fc(out[:, -1, :])
        return pred.view(-1, self.pred_len, 2)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f'\nTraining on: {device}')
net     = TrajectoryLSTM().to(device)
opt     = torch.optim.Adam(net.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

# ── 3. Train ───────────────────────────────────────────────────
EPOCHS = 150
losses = []
print('Training LSTM...')
for epoch in range(EPOCHS):
    net.train()
    epoch_loss = 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        opt.zero_grad()
        loss = loss_fn(net(xb), yb)
        loss.backward()
        opt.step()
        epoch_loss += loss.item()
    avg = epoch_loss / len(loader)
    losses.append(avg)
    if (epoch + 1) % 30 == 0:
        print(f'  Epoch {epoch+1:3d}/{EPOCHS} | Loss: {avg:.6f}')

# ── 4. Evaluate — Average Displacement Error ──────────────────
net.eval()
with torch.no_grad():
    y_pred_te = net(X_te.to(device)).cpu().numpy()

ade = np.mean(np.sqrt(np.sum((y_pred_te - y_test)**2, axis=-1)))
fde = np.mean(np.sqrt(np.sum((y_pred_te[:,-1,:] - y_test[:,-1,:])**2, axis=-1)))
print(f'\nAverage Displacement Error (ADE): {ade:.4f}')
print(f'Final   Displacement Error (FDE): {fde:.4f}')
print(f'In pixels (640px wide): ADE = {ade*640:.1f}px')

# ── 5. Save ────────────────────────────────────────────────────
torch.save(net.state_dict(), 'path_predictor.pt')
joblib.dump({'hidden': 64, 'layers': 2, 'pred_len': 5}, 'path_predictor_config.pkl')
print('\nSaved: path_predictor.pt')
print('Saved: path_predictor_config.pkl')

# ── 6. Loss curve ──────────────────────────────────────────────
plt.figure(figsize=(8,5))
plt.plot(losses, color='steelblue', linewidth=2)
plt.title('LSTM Path Predictor — Training Loss')
plt.xlabel('Epoch'); plt.ylabel('MSE Loss')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('path_predictor_loss.png', dpi=300)
print('Saved: path_predictor_loss.png')
