"""
Архитектура CRNN (CNN + LSTM) для классификации речевых сигналов.
Обоснование: CNN извлекает локальные спектральные паттерны mel-спектрограммы,
LSTM моделирует временну́ю динамику речи.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class SpeechCRNN(nn.Module):
    def __init__(self, n_mels: int = 64, n_classes: int = 10, hidden: int = 128):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),  # только по частоте
            nn.Dropout2d(0.05),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
            nn.Dropout2d(0.1),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 2)),
            nn.Dropout2d(0.15),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
        )
        # частота: 64 / 2 / 2 / 2 / 2 = 4
        self.rnn_input = 128 * 4
        self.rnn = nn.GRU(
            input_size=self.rnn_input,
            hidden_size=hidden,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.2,
        )
        self.attn = nn.Linear(hidden * 2, 1)
        self.head = nn.Sequential(
            nn.Linear(hidden * 2, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 1, n_mels, T)
        h = self.cnn(x)
        b, c, f, t = h.shape
        h = h.permute(0, 3, 1, 2).contiguous().view(b, t, c * f)
        out, _ = self.rnn(h)
        weights = torch.softmax(self.attn(out).squeeze(-1), dim=1)
        context = torch.sum(out * weights.unsqueeze(-1), dim=1)
        return self.head(context)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
