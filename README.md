# Lost-words / Zgubione słowa — polski dialogowy pipeline wideo

Automatyczne tworzenie pionowych odcinków survival / dark apocalypse / analog found footage:
**polski scenariusz dialogowy → kilka polskich głosów → kadry 9:16 → napisy PL → ambient → MP4 1080×1920**.

Każda kwestia ma pola line_id, speaker, voice_role, text i visual_prompt. Wypowiedzi są krótkie, rozdzielone naturalnymi pauzami. Obrazowe prompty pozostają po angielsku, ale wszystkie tytuły, dialogi, narracja i napisy są po polsku.

## Uruchomienie w Google Colab

[Otwórz notebook Lost-words w Google Colab](https://colab.research.google.com/github/simonexex544/lost-words-video-pipeline/blob/main/notebooks/lost_words_pipeline.ipynb)

W Colab wybierz **Środowisko wykonawcze → Uruchom wszystkie** i zaakceptuj montowanie Dysku Google. Edytuj temat i lokację w komórce 2 przed uruchomieniem.

## Co robi pipeline

1. Montuje Google Drive w /content/drive/MyDrive/lost_words_project.
2. Konfiguruje temat i lokację odcinka, liczbę kwestii (4–10), czas 35–45 s i styl wizualny.
3. Tworzy polskie tytuły, hooki, narrację i dialogi. JSON zawiera tytuł, obiekt hook oraz tablicę lines z polami line_id, speaker, voice_role, text i visual_prompt.
4. Używa polskich głosów Edge TTS z osobnym tempem i pitch dla postaci, naturalnych pauz oraz delikatnego filtra pasmowego i szumu dla głosów z radia/interkomu.
5. Generuje jeden pionowy kadr na każdą kwestię, z retry i testowym fallbackiem.
6. Montuje ujęcia z lekkim zoom/pan, cichym ambientem, polskimi napisami SRT w bezpiecznej strefie i czcionką DejaVu Sans.
7. Eksportuje H.264/AAC, MP4 1080×1920, 30 fps do folderu lost_words_project/output na Google Drive.

## Konfiguracja odcinka

Edytuj komórkę 2:

- EPISODE_TOPIC — np. pociąg przez pustkowie, podziemny schron, opuszczony port, stacja meteorologiczna albo zrujnowane miasto.
- EPISODE_LOCATION — lokacja fabularna.
- NUM_SCENES — liczba kwestii po hooku (4–10); każda kwestia dostaje własny kadr.
- TARGET_SECONDS — 35–45 s.
- PAUSE_BETWEEN_LINES — przerwy między wypowiedziami.
- IMAGE_PROVIDER — fallback do testu albo openai do generowania obrazów.
- LLM_PROVIDER — template albo openai_compatible.

Każdy odcinek ma zawierać obecność kogoś/czegoś, czego nie powinno tam być, oraz ukryty obiekt, pomieszczenie lub zapis nieobecny w oficjalnym wykazie. Prompt scenariusza wymusza ten motyw.

## Głosy i język

Dostępne polskie głosy w domyślnym mapowaniu:

| Rola | Głos Edge TTS | Brzmienie |
|---|---|---|
| calm_dark | pl-PL-MarekNeural | spokojny, obniżony |
| tense_male | pl-PL-MarekNeural | bardziej napięty, niższy pitch |
| calm_female | pl-PL-ZofiaNeural | spokojny żeński |
| radio_distorted | pl-PL-AgnieszkaNeural | pasmo krótkofalówki i szum |
| unknown | pl-PL-MarekNeural | wolniejszy, niższy i przefiltrowany |

Głosy pochodzą z polskiej listy Microsoft Azure Speech: [Language and voice support](https://learn.microsoft.com/en-us/azure/ai-services/Speech-Service/language-support). Edge TTS nie wymaga klucza API, ale wymaga internetu. Różne role są realizowane głosem, tempem, wysokością i filtrami — to nie jest klonowanie głosu.

## Colab Secrets

W panelu **Secrets** (ikona klucza) dodaj tylko te sekrety, których używasz:

| Sekret | Wymagany? | Przeznaczenie |
|---|---|---|
| OPENAI_API_KEY | opcjonalny | scenariusz przez OpenAI-compatible API; także obrazy przy IMAGE_PROVIDER='openai' |
| OPENAI_BASE_URL | opcjonalny | domyślnie https://api.openai.com/v1 |
| OPENAI_CHAT_MODEL | opcjonalny | domyślnie gpt-4o-mini |
| OPENAI_IMAGE_MODEL | opcjonalny | domyślnie gpt-image-2.5-flare |
| TTS_API_KEY | opcjonalny | miejsce na własny adapter TTS; Edge TTS go nie potrzebuje |

Po dodaniu sekretu włącz przełącznik udostępniania go temu notebookowi. Nie wpisuj kluczy do komórek kodu ani do repozytorium.

## Tryby domyślne i pliki

Domyślne wartości to LLM_PROVIDER='openai_compatible', IMAGE_PROVIDER='fallback', TTS_PROVIDER='edge'. Bez klucza LLM pipeline użyje polskiego scenariusza demonstracyjnego. Fallback obrazów tworzy syntetyczne plansze Pillow do testowania montażu, a nie fotorealistyczne obrazy. Aby generować obrazy przez API, ustaw IMAGE_PROVIDER='openai' i skonfiguruj sekret.

**Uwaga o własnych tematach:** EPISODE_TOPIC i EPISODE_LOCATION są przekazywane do generatora scenariusza, gdy dostępny jest OPENAI_API_KEY. Bez klucza działa stały scenariusz demonstracyjny o pociągu; aby testować inny motyw bez API, zmień również treść funkcji fallback_story w komórce 3.

- Film: MyDrive/lost_words_project/output/
- Scenariusze JSON: MyDrive/lost_words_project/assets/
- Audio segmentów: MyDrive/lost_words_project/audio/
- Kadry: MyDrive/lost_words_project/frames/

Jeśli Edge TTS nie wygeneruje mowy, notebook zatrzyma się i pokaże błąd — domyślnie nie zapisze niemej wersji udającej gotowy odcinek.

## Debugowanie

Przy błędzie wklej numer komórki, cały traceback od Traceback (most recent call last): do ostatniej linii oraz komunikaty [INFO], [OSTRZEŻENIE] i [BŁĄD] bezpośrednio przed tracebackiem. Nie wklejaj sekretów, tokenów ani nagłówków Authorization — zastąp je [UKRYTO].

## Uwagi

- Napisy powstają bezpośrednio z tekstu dialogów, dlatego moduł rozpoznawania mowy (ASR/faster-whisper) nie jest potrzebny.
- Użycie zewnętrznych API może wiązać się z opłatami według cenników dostawców.
