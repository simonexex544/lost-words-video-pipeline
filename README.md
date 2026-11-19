# Lost-words / Zgubione słowa — Colab Video Pipeline

Gotowy pipeline do tworzenia pionowych odcinków survival / analog found-footage: scenariusz JSON → lektor → kadry 9:16 → napisy → MP4 1080×1920, 30 fps, H.264/AAC.

> **Repozytorium docelowe:** `simonexex544/lost-words-video-pipeline`  
> Utwórz nowe repozytorium GitHub o tej nazwie i wgraj zawartość paczki. Nie wymaga to zmian w Twoim dotychczasowym repozytorium.

## Otwórz notebook w Google Colab

Repozytorium jest już utworzone. Notebook możesz uruchamiać jednym kliknięciem:

**[Open Lost-words in Google Colab](https://colab.research.google.com/github/simonexex544/lost-words-video-pipeline/blob/main/notebooks/lost_words_pipeline.ipynb)**

## Co robi pipeline

1. Montuje Google Drive w `/content/drive/MyDrive/lost_words_project`.
2. Ustawia serię `Lost-words / Zgubione słowa`, temat, lokalizację, PL/EN, 4–10 scen i docelowe 35–45 sekund.
3. Generuje scenariusz w JSON (`title`, `hook`, `scenes[]`) przez endpoint zgodny z OpenAI; bez klucza lub przy błędzie używa scenariusza demonstracyjnego.
4. Generuje lektora segmentami przez `edge-tts`.
5. Generuje kadry pionowe z retry. Domyślnie działa syntetyczny fallback Pillow — do sprawdzenia kompletnego montażu bez klucza do obrazów.
6. Montuje materiał przez `ffmpeg`: delikatny zoom, napisy SRT w dolnej bezpiecznej strefie, H.264/AAC, MP4.

## Uruchomienie

1. Wgraj pliki repozytorium (układ niżej) do nowego repozytorium GitHub `lost-words-video-pipeline`.
2. Otwórz link Colab powyżej.
3. Wybierz **Runtime → Run all** i zaakceptuj dostęp do Google Drive.
4. Zmień temat, lokalizację i język w komórce 2. Na pierwszy test zostaw `IMAGE_PROVIDER = 'fallback'`.
5. Gotowy film znajdziesz w `MyDrive/lost_words_project/output/`.

### Układ plików

```text
lost-words-video-pipeline/
├── README.md
├── requirements-colab.txt
└── notebooks/
    └── lost_words_pipeline.ipynb
```

## Sekrety Colab

W panelu **Secrets** (ikona klucza w Colab) dodaj tylko te, których faktycznie używasz:

| Nazwa | Wymagane? | Zastosowanie |
|---|---|---|
| `OPENAI_API_KEY` | Opcjonalny | Scenariusz przez OpenAI-compatible API; także kadry, gdy `IMAGE_PROVIDER = 'openai'`. |
| `OPENAI_BASE_URL` | Opcjonalny | Domyślnie `https://api.openai.com/v1`; można wskazać inny kompatybilny endpoint. |
| `OPENAI_CHAT_MODEL` | Opcjonalny | Domyślnie `gpt-4o-mini`. |
| `OPENAI_IMAGE_MODEL` | Opcjonalny | Domyślnie `gpt-image-2.5-flare`. |
| `TTS_API_KEY` | Tylko przy własnym TTS | Miejsce na sekret własnego adaptera TTS; standardowy `edge-tts` go nie wymaga. |

Po dodaniu sekretu włącz przełącznik udostępniania go temu notebookowi. Nie wpisuj kluczy w kodzie i nie commituj ich do repozytorium.

**Darmowy start / test:** pozostaw `IMAGE_PROVIDER = 'fallback'`, `TTS_PROVIDER = 'edge'`. Bez `OPENAI_API_KEY` LLM przejdzie na gotowy scenariusz demonstracyjny. `edge-tts` wymaga połączenia z internetem. Jeśli TTS nie zadziała, `ALLOW_SILENT_TEST_AUDIO = True` pozwoli przetestować sam obraz i montaż, ale taki plik nie jest gotowym odcinkiem z narracją.

## Podmiana dostawców

- **LLM:** `generate_story_openai()` — zachowaj format i walidację w `validate_story()`.
- **TTS:** `create_external_tts_segment()` — wstaw wywołanie własnego API i zapisz segment audio w podanej ścieżce.
- **Obrazy:** `generate_openai_image()` / `generate_frame_with_retry()` — adapter Gemini, Hugging Face lub Together powinien zwrócić obraz, który następnie przejdzie przez `normalize_image_9x16()`.

## Debugowanie

W razie błędu skopiuj:

1. nazwę komórki (1–6), którą uruchamiałeś;
2. cały traceback — od `Traceback (most recent call last):` do ostatniej linii;
3. komunikaty `[INFO]`, `[OSTRZEŻENIE]` i `[BŁĄD]` tuż przed tracebackiem;
4. informację o ustawieniach `LLM_PROVIDER`, `IMAGE_PROVIDER`, `TTS_PROVIDER` oraz czy audio było z TTS, czy z trybu ciszy testowej.

**Usuń przed wysłaniem** wartości kluczy API, tokeny, nagłówki `Authorization`, prywatne adresy i dane konta. Zastąp je `[UKRYTO]`.

## Uwagi

- `faster-whisper` nie jest instalowany, ponieważ napisy powstają bezpośrednio z tekstu narracji; ASR nie jest potrzebny w tym pipeline.
- Kadry fallback są syntetycznymi planszami do testu montażu, a nie ilustracjami wygenerowanymi przez model.
- Użycie zewnętrznych API może wiązać się z opłatami według cenników ich dostawców.