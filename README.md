# Lost-words / Zgubione słowa — Colab local video pipeline

Polski pipeline do pionowych filmów 40–120 s, z celem co najmniej 60 s (domyślnie około 75 s). Historia ma mroczny klimat survival/apokalipsy, polskie dialogi i narrację, wyraźny deadline, ukryty element nieobecny w oficjalnym spisie oraz finałową konsekwencję lub zwrot.

## Otwórz w Google Colab

[Uruchom notebook w Google Colab](https://colab.research.google.com/github/simonexex544/lost-words-video-pipeline/blob/main/notebooks/lost_words_pipeline.ipynb)

Notebook montuje Google Drive pod `/content/drive/MyDrive/lost_words_project`.

## Długość i montaż

- Akceptowany czas: 40–120 sekund.
- Cel: minimum 60 sekund; domyślne `TARGET_SECONDS = 75`.
- Każde ujęcie trwa 1–3 sekundy. Każda wypowiedź jest dzielona na kilka ujęć: średni plan, detal, ujęcie boczne, reakcja, plan szeroki lub reveal.
- Każde ujęcie otrzymuje własny MP4 na Drive. Nie tworzymy jednego długiego klipu i nie symulujemy większej liczby cięć przez zmianę FPS.
- Finalny plik: 1080×1920, 30 fps, H.264/AAC, polskie napisy DejaVu Sans.

## Darmowy lokalny rendering — T4, CPU fallback

Warstwa wizualna jest uruchamiana lokalnie w Colabie, bez płatnych inference API i bez wymaganego FAL_KEY. Notebook wykrywa CUDA, odczytuje wolną pamięć VRAM i przekazuje profil do modułu `visuals/shot_renderer.py`.

- Preferowany GPU: NVIDIA T4 (16 GB VRAM według specyfikacji GPU); renderer ma używać batch size 1, FP16, attention/VAE slicing i CPU offload, gdy potrzebne.
- Konserwatywne rozdzielczości startowe: 432×768 na GPU z odpowiednią ilością wolnej VRAM; 360×640 przy mniejszym zapasie; 288×512 na CPU.
- Finalne 1080×1920 powstaje przez FFmpeg. Nie renderujemy całej generatywnej sekwencji natywnie w 1080×1920 na T4.
- TPU v5e-1 nie jest obecnie używany: preferujemy CUDA/T4, a gdy CUDA nie jest dostępna, wybieramy CPU.
- Model może wymagać pierwszego pobrania wag; cache modelu zapisuje się na Drive w `models/`.

Ważne: Google Colab opisuje zasoby jako zmienne i niegwarantowane. Dostępność GPU, limity i długość sesji mogą się zmieniać. Notebook zapisuje checkpoint po każdym ujęciu, aby po ponownym uruchomieniu wznowić pracę bez ponownego renderowania gotowych plików. To nie oznacza gwarancji dostępności bezpłatnego GPU przez całą noc ani dokładnie 20–30 minut pracy.

## Tryb testowy i pełny render

W komórce 2 domyślnie ustawiono `TEST_MODE = True`. Ten tryb generuje scenariusz, Edge TTS, fragmenty audio i manifest ujęć, ale nie uruchamia modelu wizualnego i nie tworzy MP4.

Aby uruchomić lokalny renderer:
1. Upewnij się, że `visuals/shot_renderer.py` został dodany do głównej gałęzi repo zgodnie z [kontraktem renderera](docs/visual_renderer_contract.md).
2. Ustaw `TEST_MODE = False`.
3. Uruchom komórki w kolejności.
4. Zapisz wyświetlony `EPISODE_ID`. Po przerwaniu sesji wpisz ten sam identyfikator w `EPISODE_ID_OVERRIDE`; `RESUME_RENDERING = True` pominie prawidłowe checkpointy.

Domyślny scenariusz jest lokalny i darmowy. Opcjonalne `OPENAI_API_KEY` może być użyte do dynamicznego scenariusza, ale zewnętrzne API może naliczać opłaty. Edge TTS nie wymaga klucza.

## Kontrakt renderer ↔ notebook

Claude rozwija wyłącznie `visuals/shot_renderer.py`; notebook nie zna wnętrza modelu. Wejściem jest jeden słownik `shot` i `runtime`, wywołanie:

```python
render_shot(shot: dict, runtime: dict) -> dict
```

Wejście zawiera m.in. `shot_id`, `scene_id`, `duration_sec` (1–3), `visual_prompt_en`, `motion_prompt_en`, `audio_clip_path`, `output_path`, `frame_path`, `checkpoint_path`, `render_width` i `render_height`. Wyjściem jest wynik zawierający `status="completed"`, `video_path`, `duration_sec`, `width`, `height`, `fps`, `backend`, `device` i opcjonalne `lipsync_applied`.

Szczegółowa specyfikacja: [docs/visual_renderer_contract.md](docs/visual_renderer_contract.md).

## Właściciele sekcji — bez kolizji

| Obszar | Właściciel |
|---|---|
| Notebook: komórki 1–5 i 7 | ChatGPT — Drive, runtime, config, scenariusz, TTS, manifest, montaż i walidacja |
| Notebook: komórka 6 | ChatGPT — stabilny adapter i kontrola sprzętu/checkpointów |
| `visuals/shot_renderer.py` | Claude — lokalny model, animacja, oszczędzanie VRAM, zapis jednego klipu na ujęcie |
| `docs/visual_renderer_contract.md` | Wspólny kontrakt; zmiany interfejsu tylko po uzgodnieniu |

Nie edytujcie równocześnie tych samych sekcji notebooka. Zalecane są osobne gałęzie i PR-y. Claude commituję tylko `visuals/shot_renderer.py` oraz jego prywatne pliki modułu; ChatGPT commituję notebook/README/requirements. Merge PR-ów, sprawdzenie diffów i walidacja JSON notebooka przed użyciem.

## Google Drive — struktura

Wszystkie pliki są w `/content/drive/MyDrive/lost_words_project/`:

- `assets/<episode_id>_story.json` — scenariusz.
- `assets/<episode_id>_shot_manifest.json` — kolejność i parametry wszystkich ujęć.
- `assets/<episode_id>_visual_manifest.json` — wyniki renderera.
- `audio/<episode_id>/<scene_id>.wav` — pełny głos sceny.
- `audio/<episode_id>/shots/<shot_id>.wav` — fragment audio dla konkretnego ujęcia.
- `frames/<episode_id>/shots/<shot_id>.png` — opcjonalna klatka referencyjna.
- `visuals/<episode_id>/shots/<shot_id>.mp4` — osobny krótki klip.
- `checkpoints/<episode_id>/<shot_id>.json` — checkpoint po każdym gotowym klipie.
- `models/` — lokalny cache wag.
- `output/<episode_id>.mp4` — finalny film.

## Debugowanie

Wklej numer komórki i pełny traceback. Usuń klucze API, nagłówki Authorization i prywatne URL-e. Nie wysyłaj sekretów ani prywatnych nagrań do repozytorium.
