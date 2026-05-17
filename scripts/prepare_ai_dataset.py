"""Prepare AI-ready tensors from the CFD/rCFD snapshot folders.

What this script does (Step 1, conservative):
- Reads every snapshot image, converts to grayscale, resizes to a fixed
  resolution defined in ``configs/dataset_config.yaml`` (default 128x128).
- Stacks frames into ``(N, H, W)`` float32 tensors normalized to ``[0, 1]``.
- Writes ``data/processed/cfd_T_field.npy`` and ``data/processed/rcfd_T_field.npy``.
- Writes a YAML manifest with shapes, source paths, and SHA-256 hashes.

What this script does **not** do:
- Decode true temperature values from the colormap. The Fluent snapshots are
  rendered images, not raw field data. To recover physical Kelvins, run the
  CFD/rCFD case with a node-value export and feed those into a future
  ``export_numpy_arrays.py`` direct extractor. The current tensor is suitable
  for **visual / latent** baselines and as input to autoencoder studies.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from tqdm import tqdm

from cfdio import ensure_dir, list_snapshots


def _load_frame(path: Path, size: tuple[int, int]) -> np.ndarray:
    with Image.open(path) as img:
        img = img.convert("L").resize(size, Image.BILINEAR)
        arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr


def _stack(folder: Path, pattern: str, size: tuple[int, int]) -> np.ndarray:
    frames = list_snapshots(folder, pattern)
    if not frames:
        raise FileNotFoundError(f"No frames in {folder} matching {pattern}")
    out = np.empty((len(frames), size[1], size[0]), dtype=np.float32)
    for i, f in enumerate(tqdm(frames, desc=folder.name)):
        out[i] = _load_frame(f, size)
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    ap.add_argument("--config", default="configs/dataset_config.yaml", type=Path)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    size = tuple(cfg.get("image_size", [128, 128]))
    print(f"Resizing frames to {size}")

    out_dir = ensure_dir(args.out)

    cfd = _stack(args.data_root / "cfd_snapshots", "CFD_T_path_*.jpg", size)
    rcfd = _stack(args.data_root / "rcfd_snapshots", "rCFD_BJet_*.jpg", size)

    cfd_path = out_dir / "cfd_T_field.npy"
    rcfd_path = out_dir / "rcfd_T_field.npy"
    np.save(cfd_path, cfd)
    np.save(rcfd_path, rcfd)

    manifest = {
        "image_size": list(size),
        "cfd": {
            "path": str(cfd_path),
            "shape": list(cfd.shape),
            "dtype": str(cfd.dtype),
            "sha256": _sha256(cfd_path),
        },
        "rcfd": {
            "path": str(rcfd_path),
            "shape": list(rcfd.shape),
            "dtype": str(rcfd.dtype),
            "sha256": _sha256(rcfd_path),
        },
        "note": (
            "Values are grayscale intensities in [0, 1], NOT Kelvin. "
            "Use only for visual / latent-space learning until a true "
            "temperature exporter is wired in."
        ),
    }
    manifest_path = out_dir / "dataset_manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False),
                             encoding="utf-8")

    print(f"CFD tensor : {cfd.shape} -> {cfd_path}")
    print(f"rCFD tensor: {rcfd.shape} -> {rcfd_path}")
    print(f"Manifest   : {manifest_path}")


if __name__ == "__main__":
    main()
