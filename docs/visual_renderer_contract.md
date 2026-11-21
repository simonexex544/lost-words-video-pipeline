# Visual renderer contract — Lost-words

This file is the interface agreement between the Colab/story/TTS/montage owner and the visual-animation owner.

## Ownership

- Colab runtime, Google Drive layout, episode settings, Polish story JSON, Edge TTS, subtitle generation, final FFmpeg mux and ffprobe validation: notebook cells 1–4 and 7.
- Shot manifest builder + stable renderer handoff: notebook cell 5.
- Visual model implementation and per-shot animation worker: `visuals/shot_renderer.py`, imported by notebook cell 6. The visual owner may edit cell 6 only when the integration shape changes; do not edit cells 1–5 or 7 without coordination.
- Do not force-push, reset, or rewrite commits from the other owner's branch.

## Compute policy

- Local inference only. Do not call paid hosted inference APIs.
- Preferred device: CUDA GPU, especially Colab NVIDIA T4. CPU is the fallback.
- Colab TPU v5e-1 is not selected by this contract; the notebook probes CUDA first, then falls back to CPU if CUDA is unavailable.
- Read the current free VRAM at the start of each shot. Default T4 policy: batch size 1, FP16 where supported, attention/ VAE slicing, CPU offload when useful, release model/cache between shots if needed.
- Suggested starting render resolutions are 432x768 for a T4 (conservative) and 288x512 for CPU. Both are portrait 9:16. Renderer may lower the resolution on CUDA out-of-memory, but must not exceed the runtime-provided pixel/VRAM budget.
- Final delivery is always upscaled/cropped by FFmpeg to 1080x1920, 30 fps. Do not attempt to render every diffusion frame natively at 1080x1920 on a 16 GB T4.
- Model weights may be downloaded on first use if their license allows local use; cache them on Drive under `models/`. No API keys or paid job submissions.

## Input: one shot dictionary

Notebook cell 5 writes `assets/<episode_id>_shot_manifest.json` and passes one dictionary at a time to:

```python
render_shot(shot: dict, runtime: dict) -> dict
```

Required input fields:

| Field | Type | Meaning |
|---|---|---|
| schema_version | string | `1.0` |
| episode_id | string | episode folder key |
| shot_id | string | unique stable ID, e.g. `S03_SH02` |
| scene_id | string | originating dialogue scene, e.g. `S03` |
| order | integer | global shot order, starting at 0 |
| timeline_start_sec | number | absolute start in the final video |
| duration_sec | number | strictly between 1 and 3 seconds (inclusive) |
| shot_type | string | `talking_character` or `environment` |
| shot_kind | string | `medium_action`, `insert_detail`, `side_follow`, `reaction`, `wide`, `tracking`, `reveal` |
| visual_prompt_en | string | English visual description; no on-screen text |
| motion_prompt_en | string | English physical action / environmental movement |
| speaker | string | speaker role from story |
| voice_role | string | Polish TTS profile |
| character_id | string | stable identity key, or `none` |
| character_description_en | string | stable character description |
| audio_path | string | full Polish WAV path for this scene |
| audio_offset_sec | number | offset into audio_path for this cut |
| audio_duration_sec | number | same as duration_sec, clipped to available speech |
| frame_path | string | Drive PNG path for optional start/reference frame |
| output_path | string | Drive MP4 path, one file per shot |
| checkpoint_path | string | Drive JSON checkpoint path for this shot |
| render_width | integer | runtime-selected source width |
| render_height | integer | runtime-selected source height |
| output_width | integer | always 1080 |
| output_height | integer | always 1920 |
| output_fps | integer | always 30 |

The renderer receives two dictionaries:
- `shot`: exactly the per-shot fields above.
- `runtime`: device, free/total VRAM, render resolution, dtype, batch size, offload/slicing switches, model cache path, and a cancel/resume-safe checkpoint directory.

## Output: renderer result dictionary

```python
{
    "shot_id": "S03_SH02",
    "status": "completed",
    "video_path": "/content/drive/MyDrive/lost_words_project/visuals/<episode>/shots/S03_SH02.mp4",
    "frame_path": "/content/drive/MyDrive/lost_words_project/frames/<episode>/shots/S03_SH02.png",
    "duration_sec": 2.0,
    "width": 432,
    "height": 768,
    "fps": 24,
    "backend": "local",
    "device": "cuda:0",
    "lipsync_applied": false,
    "metadata_path": "/content/drive/MyDrive/lost_words_project/checkpoints/<episode>/S03_SH02.json"
}
```

The worker must return `status="completed"` only after the MP4 exists, is non-empty and can be probed. The clip is silent; notebook cell 7 lays the original Polish dialogue WAV continuously over the sequence of cuts. For dialogue shots, keep the speaking face visible in `medium_action` and `reaction` shots. If a local lip-sync method is implemented, it is optional and must not require a paid service.

## Google Drive layout

All paths are under `/content/drive/MyDrive/lost_words_project/`:

- `assets/<episode_id>_story.json` — normalized Polish story.
- `assets/<episode_id>_shot_manifest.json` — authoritative ordered input to the renderer.
- `assets/<episode_id>_visual_manifest.json` — results returned by renderer.
- `audio/<episode_id>/<scene_id>.wav` — full scene voice track.
- `frames/<episode_id>/shots/<shot_id>.png` — optional still/reference image per shot.
- `visuals/<episode_id>/shots/<shot_id>.mp4` — one short silent video per shot.
- `checkpoints/<episode_id>/<shot_id>.json` — atomic per-shot resume state.
- `models/...` — cached open local model weights.
- `output/<episode_id>.mp4` — final 1080x1920 video.

Write every finished shot and its checkpoint immediately to Drive. Do not keep the episode only in /content. On restart, skip shots with a valid completed checkpoint and valid MP4.

## Checkpoint and validation rules

- Render shots sequentially, batch size 1.
- Save each shot as soon as it completes; write checkpoint JSON atomically (temporary file then rename).
- Validate duration (1–3 s), video stream, nonzero file size, and portrait aspect ratio before marking a shot completed.
- A failed shot must return/raise a clear error with `shot_id`; already completed shots remain reusable.
- Renderer may adapt source resolution after CUDA OOM and retry the same shot once at a lower tier. It must not discard previous successful outputs.
- Never change manifest order or output paths while resuming an episode.
- The final montage owner can always upscale all clips to 1080x1920/30 fps with FFmpeg.

## Git collaboration contract

Use separate branches and never both edit the same notebook cells:
- Colab/story/TTS/montage owner: cells 1–5 and 7, plus this contract if interface changes.
- Visual owner: `visuals/shot_renderer.py` and notebook cell 6 only.
- Merge via PR or cherry-pick after checking changed paths and notebook cell ownership. Do not commit simultaneous whole-notebook rewrites. If an entire `.ipynb` must be merged, compare cell source arrays by cell index and manually combine only owned cells, then validate JSON and execute lightweight cells.
