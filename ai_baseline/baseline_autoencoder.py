"""Convolutional autoencoder baseline — SKELETON.

Status: **not validated**. The structure below sketches a small 2D
convolutional encoder/decoder for the buoyant-jet temperature snapshot. The
goal is to learn a nonlinear low-dimensional latent representation as an
alternative to POD.

A latent time-stepper (linear / LSTM / Transformer) will be plugged in
afterwards. This module only defines the compression interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AutoencoderConfig:
    image_size: tuple[int, int] = (128, 128)
    latent_dim: int = 32
    base_channels: int = 16
    depth: int = 3
    lr: float = 1e-3
    epochs: int = 50
    batch_size: int = 16
    seed: int = 0


def build_encoder(cfg: AutoencoderConfig) -> Any:
    # TODO: Conv2D stack → flatten → linear projection to latent_dim.
    raise NotImplementedError("baseline_autoencoder.build_encoder is a TODO")


def build_decoder(cfg: AutoencoderConfig) -> Any:
    # TODO: linear projection → reshape → ConvTranspose2D stack.
    raise NotImplementedError("baseline_autoencoder.build_decoder is a TODO")


def train(cfg: AutoencoderConfig, train_tensor, val_tensor) -> Any:
    # TODO: MSE-loss training loop with MAE / max-AE logging via metrics.summary.
    raise NotImplementedError("baseline_autoencoder.train is a TODO")


def main(*_args: Any, **_kwargs: Any) -> None:
    raise SystemExit(
        "baseline_autoencoder is a skeleton — implement encoder/decoder, "
        "train on data/processed/cfd_T_field.npy, evaluate on the held-out "
        "tail, and only then publish numbers."
    )


if __name__ == "__main__":
    main()
