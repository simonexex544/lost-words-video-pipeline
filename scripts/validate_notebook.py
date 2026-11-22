#!/usr/bin/env python3
"""Lightweight static checks for the Colab notebook and renderer contract."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "lost_words_pipeline.ipynb"
REQUIREMENTS = ROOT / "requirements-colab.txt"
CONTRACT = ROOT / "docs" / "visual_renderer_contract.md"
README = ROOT / "README.md"


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = notebook.get("cells")
    if not isinstance(cells, list) or len(cells) != 8:
        fail("Expected one markdown cell and seven code cells.")

    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
    if len(code_cells) != 7:
        fail(f"Expected 7 code cells, got {len(code_cells)}.")

    # Allow top-level await used by Edge TTS in Google Colab/Jupyter.
    for index, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        try:
            compile(
                source,
                filename=f"notebook_cell_{index + 1}.py",
                mode="exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
                dont_inherit=True,
            )
        except SyntaxError as exc:
            fail(
                f"Python syntax error in cell {index + 1}, "
                f"line {exc.lineno}: {exc.msg}"
            )

    sources = ["".join(cell.get("source", [])) for cell in cells]
    all_code = "\n".join(sources)
    required_tokens = {
        "Google Drive mount": "drive.mount('/content/drive'",
        "Edge TTS retry": "max_attempts = 3",
        "Safe Edge TTS normalization": "normalize_edge_tts_adjustment",
        "Final audio stream validation": "audio_stream.get('sample_rate', 0)",
        "Silent renderer clips": "renderer ma zwracać cichy MP4",
        "Per-shot manifest": "SHOT_PLAN_PATH",
        "T4 VRAM inspection": "torch.cuda.mem_get_info",
        "CPU fallback": "CPU fallback after CUDA OOM",
        "Renderer API": "renderer_module.render_shot",
        "Per-shot checkpoint": "write_json_atomic(checkpoint_path, record)",
        "Final ffprobe frame rate": "r_frame_rate",
        "Polish subtitles": "DejaVu Sans",
    }
    for label, token in required_tokens.items():
        if token not in all_code:
            fail(f"Missing required feature: {label} ({token}).")

    if any(token in all_code for token in ("FAL_KEY", "fal_client", "fal.ai")):
        fail("The notebook still contains hosted fal.ai rendering code.")

    requirements = REQUIREMENTS.read_text(encoding="utf-8").casefold()
    if "fal-client" in requirements:
        fail("requirements-colab.txt still depends on fal-client.")

    config = sources[2]
    if not all(token in config for token in (
        "NUM_SCENES = 12",
        "MIN_VIDEO_SECONDS = 60",
        "GOAL_VIDEO_SECONDS = 60",
        "MIN_SCRIPT_WORDS = 180",
        "MAX_VIDEO_SECONDS = 120",
        "SHOT_DURATION_MIN = 1.0",
        "SHOT_DURATION_MAX = 3.0",
    )):
        fail("Episode duration or shot duration settings do not match the contract.")

    fallback = sources[3].split("def fallback_story():", 1)[1].split("def generate_story_openai():", 1)[0]
    if fallback.count("        ('") != 12:
        fail("Fallback story must contain exactly 12 scenes.")

    contract = CONTRACT.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    if "render_shot(shot: dict, runtime: dict) -> dict" not in contract:
        fail("Renderer contract signature is missing.")
    if "visuals/shot_renderer.py" not in readme:
        fail("README does not document the visual renderer module.")

    print("[OK] Notebook JSON structure: 8 cells / 7 code cells.")
    print("[OK] All Python cells compile (top-level await enabled).")
    print("[OK] Google Drive, TTS, shot manifest, T4/CPU, resume and FFmpeg checks present.")
    print("[OK] No hosted fal.ai dependency remains in the notebook.")
    print("[OK] Renderer contract and README are consistent.")


if __name__ == "__main__":
    main()
