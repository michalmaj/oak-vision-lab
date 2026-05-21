# OAK-D Camera Preview HUD

> Kolorowe demo podglądu obrazu w czasie rzeczywistym dla klasycznych kamer OAK-D z użyciem DepthAI v2.

To demo pokazuje obraz RGB z kamery OAK-D oraz prosty HUD rysowany na obrazie.

Jest to pierwsza interaktywna demonstracja w projekcie `oak-vision-lab`.

## Co robi to demo?

Aplikacja:

- uruchamia strumień RGB z kamery OAK-D,
- wyświetla obraz w oknie OpenCV,
- rysuje kolorowy HUD na obrazie,
- pokazuje aktualną wartość FPS,
- wyświetla status strumienia kamery,
- obsługuje prostą interakcję z klawiatury.

## Czego można się nauczyć?

Demo wprowadza do następujących zagadnień:

- tworzenia prostego pipeline'u w DepthAI v2,
- pobierania obrazu RGB z kamery OAK-D,
- wyświetlania obrazu w czasie rzeczywistym w OpenCV,
- rysowania prostego HUD-a,
- obliczania FPS,
- obsługi klawiszy,
- oddzielania logiki testowalnej od kodu zależnego od sprzętu.

## Kompatybilność sprzętowa

Demo jest przygotowane z myślą o klasycznych kamerach OAK-D / RVC2.

Używana wersja DepthAI:

```text
depthai==2.32.0
```

DepthAI v3 nie jest używane w tym demie, ponieważ starsze urządzenia OAK-D mogą mieć problemy kompatybilnościowe z nowszym API oraz obsługą kalibracji.

## Wymagania

- kamera OAK-D,
- środowisko Python zarządzane przez `uv`,
- połączenie USB z kamerą,
- zależności projektu zainstalowane przez `uv sync`.

## Jak uruchomić?

Z katalogu głównego repozytorium:

```bash
uv sync
uv run python examples/001_camera_preview_hud/run.py
```

## Sterowanie

| Klawisz | Akcja |
| --- | --- |
| `q` | Zamknięcie dema |
| `h` | Pokazanie lub ukrycie pomocy |

## Oczekiwany rezultat

Powinno pojawić się okno z podglądem obrazu z kamery.

W oknie powinny być widoczne:

- obraz RGB z kamery OAK-D,
- nazwa projektu,
- wartość FPS,
- status strumienia,
- pomoc dotycząca klawiszy.

## Rozwiązywanie problemów

### Kamera się nie uruchamia

Sprawdź, czy:

- kamera OAK-D jest podłączona przez USB,
- żadna inna aplikacja nie korzysta z kamery,
- zainstalowana jest poprawna wersja DepthAI,
- urządzenie jest widoczne w systemie.

Wersję DepthAI można sprawdzić poleceniem:

```bash
uv run python -c "import depthai as dai; print(dai.__version__)"
```

Oczekiwana wersja:

```text
2.32.0.0
```

### Okno OpenCV się nie pojawia

Sprawdź, czy:

- program jest uruchamiany w środowisku z interfejsem graficznym,
- OpenCV jest zainstalowane,
- aplikacja nie działa w środowisku headless.

### FPS jest niestabilny

To normalne przy strumieniowaniu obrazu na żywo.

FPS może zależeć od:

- szybkości połączenia USB,
- warunków oświetleniowych,
- obciążenia systemu,
- konfiguracji kamery,
- rozdzielczości podglądu.

## Pomysły na eksperymenty

Można zmodyfikować:

- rozdzielczość podglądu,
- tekst wyświetlany w HUD-zie,
- pozycję tekstu,
- rozmiar czcionki,
- sposób wyświetlania FPS,
- obsługę klawiszy,
- efekty wizualne.

Możliwe rozszerzenia:

- tryb nagrywania,
- zapisywanie zrzutu ekranu,
- kolorowa ramka wokół obrazu,
- tryb prezentacyjny,
- efekty wizualne sterowane klawiszami.
