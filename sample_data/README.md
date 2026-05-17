# `sample_data/` — Tiny demo set

This folder is intended for a very small set of CFD and rCFD frames (e.g. 5
each) plus truncated `.out` monitor files. It is **tracked in git** so that
the notebooks and scripts can be smoke-tested without the full dataset.

Place demo frames under:

```
sample_data/
└── demo_snapshots/
    ├── CFD_T_path_0060.jpg
    ├── CFD_T_path_0120.jpg
    ├── CFD_T_path_0300.jpg
    ├── rCFD_BJet_0060.jpg
    └── rCFD_BJet_0300.jpg
```

Keep this folder **under ~5 MB** total so cloning stays fast.
