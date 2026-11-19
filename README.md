# Lost-words / Zgubione słowa — AI Video + Lip-Sync Pipeline

Polski pipeline do pionowych shortów survival / dark apocalypse / analog found footage.

**Polski scenariusz dialogowy → osobne polskie głosy → realistyczny kadr FLUX → animacja Kling Image-to-Video → Sync Lipsync dla widocznych mówiących postaci → FFmpeg → MP4 1080×1920.**

## Otwórz w Google Colab

[Uruchom lost_words_pipeline.ipynb w Google Colab](https://colab.research.google.com/github/simonexex544/lost-words-video-pipeline/blob/main/notebooks/lost_words_pipeline.ipynb)

W Colab wybierz Środowisko wykonawcze → Uruchom wszystkie. Notebook montuje Google Drive pod /content/drive/MyDrive/lost_words_project.

## Tryby pracy i bezpieczeństwo kosztów

W komórce 2 domyślnie jest TEST_MODE = True.

W tym trybie:
- generowany jest polski scenariusz demonstracyjny;
- edge-tts tworzy osobne pliki głosu dla każdej kwestii;
- płatne zadania FLUX, Kling i Sync Lipsync są pomijane;
- zapisywany jest raport testowy;
- **nie powstaje MP4**, ponieważ notebook nie udaje pełnego materiału animowanego.

Pełny tryb:
1. Dodaj FAL_KEY w Colab Secrets.
2. Ustaw TEST_MODE = False.
3. Opcjonalnie dodaj OPENAI_API_KEY, jeśli chcesz generować nowy scenariusz dla własnego tematu/lokacji.
4. Uruchom wszystkie komórki.

Uwaga: pełny odcinek może wysłać wiele płatnych zadań. Dla każdej kwestii powstaje obraz FLUX i klip Kling I2V; każda scena talking_character uruchamia dodatkowo Sync Lipsync. Sprawdź aktualny cennik modeli fal.ai przed uruchomieniem. Domyślny test nie wysyła tych zadań.

## Używane modele i API

| Etap | Endpoint | Funkcja |
|---|---|---|
| Obraz startowy | fal-ai/flux/dev | realistyczny obraz pionowy |
| Ruch obrazu | fal-ai/kling-video/v3/standard/image-to-video | Image-to-Video, ruch postaci i kamery |
| Synchronizacja ust | fal-ai/sync-lipsync/v2 | dopasowanie ust do osobnego audio |
| Kolejka | fal Queue API | submit, status polling, result, retry |

Oficjalna dokumentacja:
- [FLUX.1 Dev API](https://fal.ai/models/fal-ai/flux/dev/api)
- [Kling Video 3 Standard Image-to-Video](https://fal.ai/models/fal-ai/kling-video/v3/standard/image-to-video/api)
- [Sync Lipsync 2](https://fal.ai/models/fal-ai/sync-lipsync/v2/api)
- [fal Queue submit](https://fal.ai/docs/api-reference/inference-api/queue/submit-path)
- [fal Queue status](https://fal.ai/docs/api-reference/inference-api/queue/status)
- [fal Python SDK / uploads](https://fal-ai.github.io/fal/client/fal_client.html)

## Wymagane i opcjonalne Colab Secrets

| Secret | Wymagany? | Zastosowanie |
|---|---|---|
| FAL_KEY | wymagany dla TEST_MODE=False | FLUX, Kling I2V, Sync Lipsync i przesyłanie plików |
| OPENAI_API_KEY | opcjonalny | dynamiczny scenariusz przez OpenAI-compatible API |
| OPENAI_BASE_URL | opcjonalny | domyślnie https://api.openai.com/v1 |
| OPENAI_CHAT_MODEL | opcjonalny | domyślnie gpt-4o-mini |
| FAL_WEBHOOK_URL | opcjonalny | publiczny HTTPS endpoint do powiadomień fal; notebook nadal używa pollingu |
| TTS_API_KEY | opcjonalny | placeholder pod własny adapter TTS; Edge TTS go nie wymaga |

Sekrety wczytywane są najpierw z google.colab.userdata, a potem z os.environ. Nigdy nie wpisuj kluczy w kodzie ani do repozytorium.

fal.ai przechowuje przesłane pliki i wyniki na swoim CDN zgodnie z ustawieniami retencji konta i usługi. Nie przesyłaj prywatnych nagrań, wizerunków ani materiałów, do których nie masz praw lub zgody.

## Scenariusz i struktura kwestii

Tytuły, hook, dialogi i napisy są po polsku. Prompty obrazów są po angielsku. Każda kwestia zawiera:

- scene_id
- speaker: narrator, ocalaly_1, ocalaly_2, glos_z_radia lub nieznany
- voice_role: calm_dark, tense_male, calm_female, radio_distorted lub unknown
- text
- visual_prompt
- shot_type: talking_character albo environment
- character_id i character_description

Każdy odcinek powinien zawierać kogoś/coś, czego nie powinno być w danej lokacji, oraz ukryte miejsce, obiekt albo zapis, którego nie ma w żadnym wykazie. Domyślny przykład to wagon, którego nie ma w rozkładzie.

## Głosy i montaż

Edge TTS tworzy osobne pliki audio dla kwestii. Profile wykorzystują polskie głosy Marek, Zofia i Agnieszka, z umiarkowanymi zmianami tempa i wysokości tonu. Głos z radia i nieznany otrzymują filtr pasmowy, kompresję oraz delikatny szum.

Sceny talking_character są animowane przez Kling, a następnie synchronizowane z odpowiednim plikiem audio przez Sync Lipsync. Sceny environment korzystają z samego klipu Kling, bez synchronizacji ust. Notebook nie wstawia geometrycznych plansz jako substytutu animacji.

Końcowy montaż:
- 9:16, 1080×1920, 30 fps;
- H.264 video i AAC audio;
- naturalne pauzy między kwestiami;
- cichy syntetyczny ambient pod dialogiem;
- polskie napisy z DejaVu Sans i bezpiecznym marginesem;
- ffprobe sprawdza obecność strumieni video/audio, rozdzielczość, kodeki i długość;
- FFmpeg volumedetect sprawdza, czy audio nie jest cyfrową ciszą.

## Pliki na Google Drive

- MP4: MyDrive/lost_words_project/output/
- Scenariusze i manifesty: MyDrive/lost_words_project/assets/
- Audio kwestii: MyDrive/lost_words_project/audio/
- Obrazy startowe: MyDrive/lost_words_project/frames/
- Klipy I2V/lip-sync: MyDrive/lost_words_project/video/
- Pliki tymczasowe: MyDrive/lost_words_project/temp/

## Debugowanie

Przy błędzie wklej numer komórki, pełny traceback od Traceback (most recent call last): do końca oraz komunikaty [INFO], [QUEUE], [OSTRZEŻENIE] i [BŁĄD]. Usuń klucze API, nagłówki Authorization i prywatne URL-e; zastąp je [UKRYTO].

Webhook jest opcjonalny. Colab nie uruchamia serwera webhook, dlatego notebook zawsze monitoruje kolejkę przez status polling. Jeśli podasz FAL_WEBHOOK_URL, fal dodatkowo wyśle powiadomienie na ten publiczny HTTPS adres.

## Uwaga o scenariuszu demo

Bez OPENAI_API_KEY albo w TEST_MODE używany jest demonstracyjny scenariusz o pociągu. Aby zmienić temat i otrzymać nowy scenariusz automatycznie, skonfiguruj OPENAI_API_KEY i wyłącz TEST_MODE. Własny adapter TTS można dodać w funkcji create_external_tts_segment w komórce TTS.
