# Windows 11 Adaptation

The upstream `bouyant_jet_replay` tutorial assumes a Linux host. This document
records the changes needed to run the full CFD → rCFD → post-processing
pipeline on Windows 11.

## 1. Toolchain prerequisites

- **ANSYS Fluent** 2023 R2 or later (3D, double precision).
- **Visual Studio Build Tools** matching the Fluent UDF compiler
  (MSVC C/C++ toolset).
- **MATLAB** for the original post-processing scripts; the Python scripts in
  `scripts/` reproduce the same plots if MATLAB is unavailable.
- **Python 3.10+** with the packages in `requirements.txt`.

Fluent must be launched from a shell that has inherited the MSVC environment
variables, otherwise UDF compilation fails. A working approach:

```powershell
# Run once per shell
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
# Then start Fluent from the same shell
& "C:\Program Files\ANSYS Inc\v232\fluent\ntbin\win64\fluent.exe" 3ddp -t4
```

## 2. Path conventions

The upstream scheme files use forward-slash paths. Fluent on Windows accepts
both, but any auxiliary `.bat` driver in this project (`run_postproc.bat`)
uses Windows-style paths. The Python utilities in `scripts/` use
`pathlib.Path` and are OS-agnostic.

## 3. Post-processing driver

`run_postproc.bat` (in the upstream tutorial) chains the MATLAB
post-processing scripts. The Python equivalents here are explicit:

```powershell
python scripts\plot_temperature_series.py --data-root data\ --out assets\figures\
python scripts\compare_cfd_rcfd.py        --data-root data\ --out assets\figures\
python scripts\make_animation.py          --src data\cfd_snapshots\  --out assets\animations\cfd.gif
python scripts\make_animation.py          --src data\rcfd_snapshots\ --out assets\animations\rcfd.gif
```

## 4. Known caveats

- File-permission issues on `D:\` drives can prevent Fluent from writing
  outputs. Granting the user `Modify` access to the working directory
  (`icacls ... /grant <user>:(OI)(CI)M /T`) is usually enough.
- Long path names (>260 characters) can still trip Fluent on Windows. Keep
  the project path short, or enable Win32 long paths in Group Policy.
- Use line-buffered terminal output (`-noconsole` flag avoided) when watching
  long replays — Windows console buffering can otherwise hide errors.

## 5. Verified configuration

The Step 1 results in this repository were produced on:

- Windows 11 Home Single Language 10.0.26200
- ANSYS Fluent 2026 R1 (3ddp, 4 partitions)
- MSVC 2022 Build Tools
- Python 3.10
