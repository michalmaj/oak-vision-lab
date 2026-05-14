# oak-vision-lab

> Interaktywne demonstracje computer vision dla kamer OAK-D, tworzone z myślą o dydaktyce, warsztatach i pokazach na żywo.

[English version](README.md)

`oak-vision-lab` to rozwijany zbiór kolorowych, interaktywnych i dydaktycznych demonstracji computer vision budowanych w Pythonie z użyciem kamer OAK-D.

Projekt ma trzy główne zastosowania:

- materiał dydaktyczny dla studentów,
- repozytorium pokazujące dobre praktyki inżynierskie,
- zestaw efektownych demonstracji na warsztaty i prezentacje.

## Cele projektu

- Tworzenie interaktywnych aplikacji, które są ciekawe, efektowne i łatwe do wyjaśnienia.
- Nauka zagadnień computer vision przez małe, konkretne przykłady.
- Praca z repozytorium w stylu zbliżonym do projektu komercyjnego.
- Utrzymanie czytelnej, testowalnej i dobrze udokumentowanej struktury.
- Przygotowanie przykładów zarówno dla małych grup warsztatowych, jak i większych pokazów.

## Stos technologiczny

- Python
- OAK-D / DepthAI
- OpenCV
- uv
- Ruff
- pytest
- GitHub Actions

## Planowane demonstracje

- Podgląd obrazu z OAK-D z kolorowym HUD-em
- Wizualizacja mapy głębi
- Detekcja obiektów
- Licznik osób
- Interakcja za pomocą dłoni
- Sterowanie interfejsem gestami
- Mini gry oparte na computer vision

## Sposób pracy nad projektem

Repozytorium jest rozwijane zgodnie z praktykami znanymi z projektów komercyjnych:

- każda większa zmiana powstaje na osobnej gałęzi,
- zmiany trafiają do `main` przez Pull Request,
- commity są małe i opisowe,
- testy i kontrola jakości kodu są automatyzowane,
- dokumentacja jest aktualizowana razem z kodem.

Przykładowe nazwy gałęzi:

```text
feature/001-project-bootstrap
feature/002-camera-preview-hud
feature/003-depth-map-viewer
docs/004-demo-readme-template
fix/005-camera-error-handling
```

## Lokalne notatki

Prywatne notatki, pliki robocze oraz linki do rozmów z ChatGPT można trzymać w katalogu:

```text
local/
```

Ten katalog jest ignorowany przez Git.

## Praca developerska

Instalacja zależności:

```bash
uv sync
```

Uruchomienie testów:

```bash
uv run pytest
```

Sprawdzenie kodu Ruffem:

```bash
uv run ruff check .
```

Formatowanie kodu:

```bash
uv run ruff format .
```

## Status

Wczesny etap rozwoju. Projekt jest budowany krok po kroku.
