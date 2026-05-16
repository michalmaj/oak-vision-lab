# oak-vision-lab

[![CI](https://github.com/michalmaj/oak-vision-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/michalmaj/oak-vision-lab/actions/workflows/ci.yml)

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

## Dostępne demonstracje

| Nr | Demo | Opis | Dokumentacja |
| --- | --- | --- | --- |
| 002 | Camera Preview HUD | Podgląd obrazu RGB w czasie rzeczywistym z FPS, statusem strumienia i HUD-em sterowanym z klawiatury. | [EN](examples/002_camera_preview_hud/README.md) / [PL](examples/002_camera_preview_hud/README.pl.md) |
| 003 | Depth Map Viewer | Kolorowa wizualizacja dysparycji stereo pokazująca informację podobną do głębi w czasie rzeczywistym. | [EN](examples/003_depth_map_viewer/README.md) / [PL](examples/003_depth_map_viewer/README.pl.md) |
| 004 | RGB + Depth Split-Screen | Widok dzielony w czasie rzeczywistym porównujący zwykły obraz RGB z kolorową wizualizacją dysparycji stereo. | [EN](examples/004_rgb_depth_split_screen/README.md) / [PL](examples/004_rgb_depth_split_screen/README.pl.md) |
| 005 | Depth Proximity Alert | Interaktywne demo oparte na dysparycji, które reaguje, gdy obiekt zbliża się do środka obrazu z kamery. | [EN](examples/005_depth_proximity_alert/README.md) / [PL](examples/005_depth_proximity_alert/README.pl.md) |

## Planowane demonstracje

- Widok dzielony RGB + depth
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

## Kompatybilność sprzętowa i DepthAI

Projekt jest obecnie rozwijany z myślą o klasycznych kamerach OAK-D / urządzeniach RVC2 i używa DepthAI v2.

Aktualna bazowa zależność projektu to:

```text
depthai==2.32.0
```

Wsparcie dla DepthAI v3 może zostać rozważone później jako osobna warstwa kompatybilności.

## Status

Wczesny etap rozwoju. Projekt jest budowany krok po kroku.
