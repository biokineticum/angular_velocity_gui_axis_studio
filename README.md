# angular_velocity_gui_axis_studio

**Desktop GUI for real-time angular velocity from Axis Studio / mocap BVH streams** over UDP, with joint selection and live Matplotlib plots.

For motion-capture labs streaming BVH channel data (default UDP `127.0.0.1:7005`) who need a quick joint angular-velocity view.

## Features

- Tkinter UI (`mocap_gui.py`) — configure UDP IP/port, load BVH, pick joint, window size
- Parses BVH channel layout; plots filtered angular velocity (SciPy `medfilt`)
- Bundled sample: `take003_chr01.bvh`
- Optional Windows one-file build via `build.bat` (PyInstaller + `MocapApi.dll`)

## Requirements

- Python 3 with: `numpy`, `matplotlib`, `scipy` (tkinter from stdlib)
- For EXE build: PyInstaller, and files `mocap_gui.py`, `MocapApi.dll`, `take003_chr01.bvh`

## Quick start

```bash
git clone https://github.com/biokineticum/angular_velocity_gui_axis_studio.git
cd angular_velocity_gui_axis_studio
pip install numpy matplotlib scipy
python mocap_gui.py
```

Point Axis Studio (or your streamer) at the configured UDP port, parse BVH, select a joint, start streaming.

### Build Windows EXE

```bat
build.bat
```

Output: `dist\MocapAnalysis.exe`

---

## Author

**Dariusz Mosler** (Biokineticum) — physiotherapy, biomechanics, sports science  
🌐 [biokineticum.com](https://biokineticum.com) · 📰 [Substack](https://biokineticum.substack.com) · 𝕏 [@Biokineticum](https://x.com/Biokineticum)

