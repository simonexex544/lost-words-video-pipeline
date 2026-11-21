# Visual renderer contract — Lost-words

This is the stable interface between the Colab notebook owner and the visual animation owner.

## Ownership and no-overwrite rules

- Notebook cells 1–5 and 7 are maintained by the Colab/story/TTS/montage owner.
- Notebook cell 6 is the stable adapter: hardware detection, VRAM policy, resume, output validation and checkpoints. Do not edit it for model implementation changes.
- Claude owns `visuals/shot_renderer.py` and any helper files in `visuals/`. Claude must not rewrite the notebook or modify cells 1–5 or 7.
- This document defines the shared API. Any signature/schema changes must be agreed before editing both sides.
- Use separate branches and PRs; never force-push or rewrite another collaborator's commits.

## Runtime goals and compute policy

- Accepted episode duration: 40–120 seconds. Target at least 60 seconds; notebook default target is 75 seconds.
- Each visual cut is a separate 1–3 second clip. Notebook writes the clip to Drive immediately after success.
- Local inference only. Do not call paid hosted inference APIs.
- Preferred hardware: CUDA, especially Colab NVIDIA T4; CPU fallback is mandatory.
- Colab TPU v5e-1 is not used by this first interface. The notebook probes CUDA and chooses CPU if CUDA is unavailable.
- Detect free VRAM at runtime. Use batch size 1, FP16 when supported, attention/VAE slicing, and CPU offload when appropriate.
- The notebook refreshes free VRAM before each shot. Conservative presets are 432x768 when at least about 11 GB is free, 360x640 when at least 7 GB is free, otherwise 288x512. If less than 3 GB is free, it switches to CPU. The maximum VRAM budget is never set above the measured free VRAM minus a 2 GB safety margin. CPU uses 288x512. All are portrait.
- Final delivery is 1080x1920 at 30 fps via FFmpeg. The renderer must not attempt full-resolution 1080x1920 diffusion generation on a 16 GB T4.
- Model weights may be downloaded once and cached under `models/` on Drive, but model license must allow local use. No paid API key is expected.

## Input: one shot dictionary

Notebook cell 5 writes `assets/<episode_id>_shot_manifest.json` and calls the renderer sequentially with:

```python
render_shot(shot: dict, runtime: dict) -> dict
```

Required `shot` fields:

| Field | Type | Meaning |
|---|---|---|
| schema_version | string | `1.0` |
| episode_id | string | episode ID |
| shot_id | string | unique ID, e.g. `S03_SH02` |
| scene_id | string | source dialogue segment |
| order | integer | global order from zero |
| timeline_start_sec | number | start in final episode |
| duration_sec | number | 1–3 seconds |
| shot_index | integer | index within dialogue scene |
| shot_count_in_scene | integer | number of cuts for this scene |
| shot_type | string | `talking_character` or `environment` |
| shot_kind | string | framing/action kind such as `medium_action`, `insert_detail`, `side_follow`, `reaction`, `wide`, `tracking`, `reveal` |
| visual_prompt_en | string | English visual prompt, no text on image |
| motion_prompt_en | string | English action/movement prompt |
| speaker / voice_role | string | speaker and Polish TTS profile |
| character_id | string | stable identity ID, or `none` |
| character_description_en | string | English visual identity description |
| audio_path | string | full Polish WAV for this scene |
| audio_offset_sec | number | local offset in that WAV |
| audio_duration_sec | number | duration of the cut |
| audio_clip_path | string | pre-cut WAV for this shot |
| frame_path | string | optional starting/reference PNG on Drive |
| output_path | string | required MP4 output path on Drive |
| checkpoint_path | string | required per-shot JSON checkpoint path |
| render_width / render_height | integer | source resolution chosen based on free VRAM |
| output_width / output_height | integer | 1080×1920 |
| output_fps | integer | 30 |

The `runtime` dictionary contains `device`, `device_name`, `cuda_available`, free/total VRAM, render resolution, dtype, batch size, max VRAM budget, CPU offload, attention/VAE slicing, decode chunk size, Drive model-cache path, checkpoint path, and `allow_paid_apis=False`.

## Output: renderer result dictionary

Return a dictionary only after the video file is complete:

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

Requirements:
- Write one silent MP4 per shot at `output_path`, and optional PNG at `frame_path`.
- Duration must be 1–3 seconds and portrait 9:16 (source resolution can be lower than final).
- For `talking_character`, character itself must visibly move; camera motion alone is insufficient. Keep the face/mouth visible for `medium_action` and `reaction` shots.
- `audio_clip_path` is provided for optional local lip-sync; lip-sync must not require a paid service. Notebook will overlay the original uninterrupted dialogue WAV during final montage.
- Return `status="completed"` only after the MP4 exists, is non-empty and probes successfully.
- Save model/cache state under Drive `models/`; never use `/content` as the only storage location for completed shots.

## Google Drive layout

All paths are under `/content/drive/MyDrive/lost_words_project/`:

- `assets/<episode_id>_story.json` — normalized Polish story.
- `assets/<episode_id>_shot_manifest.json` — authoritative ordered input manifest.
- `assets/<episode_id>_visual_manifest.json` — renderer result list.
- `audio/<episode_id>/<scene_id>.wav` — full Polish voice track.
- `audio/<episode_id>/shots/<shot_id>.wav` — shot-level audio crop.
- `frames/<episode_id>/shots/<shot_id>.png` — optional reference frame.
- `visuals/<episode_id>/shots/<shot_id>.mp4` — one short silent clip per shot.
- `checkpoints/<episode_id>/<shot_id>.json` — atomic per-shot resume state.
- `models/...` — cached open model weights.
- `output/<episode_id>.mp4` — final 1080x1920 H.264/AAC.

## Checkpoint and validation rules

- Render shots sequentially, batch size 1.
- Save each MP4 and its metadata to Drive immediately; write checkpoint JSON atomically (temporary file then rename).
- Validate duration, video stream, nonzero file size, and portrait aspect ratio before marking completed.
- A failed shot must raise a clear error containing `shot_id`; already completed outputs must remain reusable.
- On CUDA OOM, retry the same shot at a lower resolution or CPU; do not discard successful outputs.
- Never change manifest order, shot IDs, or output paths when resuming an episode.
- Final montage code upscales clips to 1080x1920/30 fps using FFmpeg.

## Colab and free-resource caveat

The notebook contains no paid hosted video inference calls. However, Colab's free hardware availability and session duration are not guaranteed; the notebook persists each shot so work can resume across sessions. CPU fallback may be very slow. A local model must use an OSI-compatible or otherwise permitted model license for its use case.
