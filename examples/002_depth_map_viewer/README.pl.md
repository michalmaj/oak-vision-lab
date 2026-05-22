# Depth Map Viewer

> Kolorowe demo stereo vision w czasie rzeczywistym, które wizualizuje informację podobną do głębi z kamery OAK-D.

To demo pokazuje, jak kamera stereo może estymować strukturę sceny na podstawie dwóch zsynchronizowanych kamer monochromatycznych.

Zamiast zwykłego obrazu RGB aplikacja wyświetla mapę dysparycji jako kolorową wizualizację przypominającą heatmapę. Efekt wygląda bardziej jak skaner głębi z filmu science fiction niż klasyczny podgląd z kamery.

## Co robi to demo?

Aplikacja:

- uruchamia strumienie z lewej i prawej kamery monochromatycznej,
- tworzy pipeline stereo vision,
- oblicza mapę dysparycji,
- normalizuje wartości dysparycji do wizualizacji,
- nakłada kolorową mapę barw OpenCV,
- wyświetla wynik w czasie rzeczywistym,
- rysuje prosty HUD z FPS i statusem strumienia,
- obsługuje podstawową interakcję z klawiatury.

## Dlaczego to jest przydatne?

To demo jest dobrym wprowadzeniem do stereo vision.

Pomaga pokazać studentom, że system kamer może estymować strukturę sceny nie tylko na podstawie wyglądu obiektów, ale także na podstawie geometrycznych różnic między dwoma widokami.

Wynik wizualny jest też atrakcyjny podczas pokazów na żywo, ponieważ informacja związana z głębią jest widoczna od razu i łatwo ją omówić.

## Czego można się nauczyć?

Demo wprowadza do następujących zagadnień:

- podstawy kamer stereo,
- mapy dysparycji,
- przetwarzanie obrazu w czasie rzeczywistym,
- normalizacja wartości obrazu,
- kolorowe mapy barw w OpenCV,
- nakładanie HUD-a na obraz,
- oddzielanie logiki wizualizacji od logiki możliwej do testowania.

## Jak to działa?

Kamera OAK-D ma dwie kamery monochromatyczne, które obserwują tę samą scenę z nieco różnych punktów widzenia.

Pipeline stereo porównuje te dwa widoki i estymuje dysparycję.

W uproszczeniu:

```text
większa dysparycja  -> obiekt jest bliżej
mniejsza dysparycja -> obiekt jest dalej
```

Surowy obraz dysparycji jest następnie skalowany do zakresu 0-255 i zamieniany na kolorową wizualizację przy użyciu mapy barw OpenCV.

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run depth-map-viewer
```

Można też użyć numeru dema:

```bash
uv run oakvl run 002
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/002_depth_map_viewer/run.py
```

Skrót Makefile:

```bash
make demo-002
```

## Sterowanie

```text
q  - zamknięcie dema
h  - pokazanie/ukrycie pomocy
```

## Oczekiwany rezultat

Powinno pojawić się okno z kolorową wizualizacją dysparycji w czasie rzeczywistym.

Bliskie obiekty powinny zwykle powodować silniejsze zmiany wizualne niż dalsze tło.

HUD powinien pokazywać:

- nazwę dema,
- wartość FPS,
- status strumienia,
- pomoc dotyczącą klawiszy.

## Pomysły na eksperymenty

Można zmodyfikować:

- typ mapy barw,
- preset stereo,
- tytuł okna podglądu,
- tekst HUD-a,
- sposób wyświetlania FPS,
- normalizację dysparycji,
- obsługę klawiszy.

Możliwe rozszerzenia:

- dodanie kilku trybów kolorowania,
- zapisywanie zrzutu ekranu,
- widok surowej dysparycji obok wersji kolorowej,
- tryb prezentacyjny,
- prosta interakcja zależna od odległości,
- widok dzielony RGB + depth/disparity.