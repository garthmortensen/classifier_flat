#!/usr/bin/env python3
"""Simple project-wide export helper with step-based filenames.

Filename convention: n_YYYYMMDD_HHMMSSNN.ext
- n: zero-padded global step counter for the run
- YYYYMMDD_HHMMSS: static timestamp captured on first save
- NN: two-digit subsecond sequence derived from step counter

Usage:
- Call `export(data, name="optional_name", subdir="optional/subdir")`.
- Enable/disable saving via `set_export_mode(True|False)`.
- Change output root via `set_output_dir(path)`.
"""

import os
import json
import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd
try:
    import matplotlib.figure as mpl_figure
except Exception:
    mpl_figure = None
try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

_EXPORT_ENABLED = True
_STEP_COUNTER = 0
_STATIC_TS = None

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_OUTPUT_ROOT = os.path.join(_PROJECT_ROOT, "outputs")

def set_export_mode(enabled: bool) -> None:
    global _EXPORT_ENABLED
    _EXPORT_ENABLED = bool(enabled)

def set_output_dir(path: str) -> None:
    global _OUTPUT_ROOT
    _OUTPUT_ROOT = os.path.abspath(path)

def _ensure_run_state() -> None:
    global _STATIC_TS
    if _STATIC_TS is None:
        _STATIC_TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def _infer_ext(data: Any) -> str:
    if isinstance(data, pd.DataFrame):
        return "csv"
    if isinstance(data, np.ndarray):
        return "npy"
    if isinstance(data, (dict, list)):
        return "json"
    # Visuals
    if mpl_figure and isinstance(data, mpl_figure.Figure):
        return "png"
    if PILImage and isinstance(data, PILImage):
        return "png"
    return "txt"

def _save(full_path: str, data: Any, ext: str) -> None:
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    if ext == "csv":
        data.to_csv(full_path, index=False)
    elif ext == "npy":
        np.save(full_path, data)
    elif ext == "json":
        with open(full_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    elif ext == "png":
        # Support matplotlib Figure, PIL Image, or numpy array (HxWxC or HxW)
        if mpl_figure and isinstance(data, mpl_figure.Figure):
            data.savefig(full_path, bbox_inches="tight")
        elif PILImage and isinstance(data, PILImage):
            data.save(full_path)
        elif isinstance(data, np.ndarray):
            try:
                # Attempt to save via PIL if available
                if PILImage:
                    img = PILImage.fromarray(data)
                    img.save(full_path)
                else:
                    # Fallback: write raw bytes if already bytes
                    raise ValueError("PIL not available to save numpy array as PNG")
            except Exception as e:
                raise e
        else:
            raise ValueError("Unsupported data type for PNG export")
    else:
        with open(full_path, "w") as f:
            f.write(str(data))

def export(data: Any, name: Optional[str] = None, subdir: Optional[str] = None, ext: Optional[str] = None) -> Any:
    """
    Save data using step-based filename convention and return the data.
    """
    global _STEP_COUNTER
    if not _EXPORT_ENABLED:
        return data

    _ensure_run_state()
    _STEP_COUNTER += 1

    # Two-digit sequence derived from step counter (wraps at 100)
    seq = _STEP_COUNTER % 100
    ext = ext or _infer_ext(data)

    base = f"{_STEP_COUNTER:03d}_{_STATIC_TS}{seq:02d}"
    if name:
        base = f"{base}__{name}"
    filename = f"{base}.{ext}"

    target_dir = _OUTPUT_ROOT if not subdir else os.path.join(_OUTPUT_ROOT, subdir)
    full_path = os.path.join(target_dir, filename)

    try:
        # Convert non-serializable objects for json when needed
        if ext == "json" and not isinstance(data, (dict, list)):
            if hasattr(data, "to_dict"):
                data = data.to_dict()
            elif hasattr(data, "tolist"):
                data = data.tolist()
            else:
                data = str(data)

        _save(full_path, data, ext)
        print(f"Saved: {full_path}")
    except Exception as e:
        print(f"Error saving data: {e}")

    return data

# Convenience method on DataFrame
pd.DataFrame.export = lambda self, name=None, subdir=None: export(self, name=name, subdir=subdir)