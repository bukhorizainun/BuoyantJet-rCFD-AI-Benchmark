# `data/` — Dataset placement

The actual CFD/rCFD outputs are **not** stored in git. This folder defines
where they must be placed locally so every script and notebook in the repo
can find them.

## Expected layout

```
data/
├── raw/
│   ├── CFD_temperature.out          (CFD reference mean-T monitor)
│   ├── CFD_start_energy.out         (CFD spin-up energy trace)
│   ├── rCFD_temperature.out         (rCFD replay mean-T monitor)
│   ├── rCFD_balance.out             (rCFD energy balance)
│   └── *.trn                        (Fluent transcripts, optional)
├── cfd_snapshots/
│   └── CFD_T_path_0000.jpg ... CFD_T_path_0629.jpg
├── rcfd_snapshots/
│   └── rCFD_BJet_0000.jpg  ... rCFD_BJet_0599.jpg
├── processed/                       (filled by scripts, git-ignored)
└── metadata/                        (small YAML/JSON, git-tracked)
```

## Quick start

If you already produced the upstream tutorial outputs (in
`..\bouyant_jet_replay\post`), run:

```powershell
python scripts\organize_snapshots.py --src ..\bouyant_jet_replay\post --dst data\
python scripts\check_dataset.py      --data-root data\
```

`check_dataset.py` should report `630` CFD frames and `600` rCFD frames.

## Notes

- Files under `raw/`, `cfd_snapshots/`, `rcfd_snapshots/`, `processed/` are
  matched by `.gitignore`. Do **not** force-add them — they are bulky.
- Manifests under `metadata/` **are** tracked. Use them to document each run.
- For a tiny demo set (a few frames + truncated `.out`), see `sample_data/`.
