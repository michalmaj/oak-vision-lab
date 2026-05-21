# Depth Proximity Alert

> Interaktywne demo w czasie rzeczywistym, które reaguje, gdy obiekt zbliża się do kamery.

To demo wykorzystuje informację o dysparycji stereo do oszacowania, czy coś znajduje się blisko środka obrazu z kamery.

Wizualizacja podobna do głębi zostaje zamieniona w prosty system alertów z trzema stanami:

```text
SAFE -> NEAR -> VERY CLOSE
```

## Co robi to demo?

Aplikacja:

- tworzy pipeline dysparycji stereo,
- wizualizuje dysparycję za pomocą mapy barw OpenCV,
- wycina środkowy region zainteresowania,
- oblicza średnią dysparycję w tym regionie,
- klasyfikuje bliskość do jednego z trzech poziomów,
- rysuje kolorowy region zainteresowania,
- rysuje ramkę alertu wokół obrazu,
- pokazuje FPS i status w HUD-zie,
- reaguje w czasie rzeczywistym, gdy obiekt zbliża się do kamery.

## Dlaczego to jest przydatne?

To demo pokazuje, jak surową informację wizualną można przekształcić w prostą decyzję.

Aplikacja nie tylko wyświetla obraz, ale interpretuje część sceny i zwraca czytelny stan.

Jest to dobre wprowadzenie do następujących zagadnień:

- interakcja oparta na percepcji,
- logika decyzyjna oparta na progach,
- przetwarzanie regionu zainteresowania,
- wizualna informacja zwrotna w czasie rzeczywistym.

Demo dobrze sprawdza się także podczas pokazów, ponieważ uczestnicy mogą zbliżać rękę lub obiekt do kamery i od razu widzieć reakcję systemu.

## Czego można się nauczyć?

Demo wprowadza do następujących zagadnień:

- wizualizacja dysparycji stereo,
- wycinanie środkowego regionu zainteresowania,
- proste statystyki obrazu,
- obliczanie średniej dysparycji,
- klasyfikacja oparta na progach,
- wizualne nakładki alertów,
- oddzielanie testowalnej logiki decyzyjnej od kodu zależnego od kamery.

## Jak to działa?

Demo wykorzystuje ramkę dysparycji generowaną przez pipeline stereo.

Ze środka obrazu wycinany jest region zainteresowania:

```text
+-------------------------+
|                         |
|         +-------+       |
|         |  ROI  |       |
|         +-------+       |
|                         |
+-------------------------+
```

Wewnątrz tego regionu obliczana jest średnia dysparycja.

Większa dysparycja zwykle oznacza, że obiekt znajduje się bliżej kamery.

Średnia wartość jest następnie klasyfikowana do jednego z trzech stanów:

```text
niska dysparycja    -> SAFE
średnia dysparycja  -> NEAR
wysoka dysparycja   -> VERY CLOSE
```

Aktualny stan zmienia kolor alertu oraz status wyświetlany w HUD-zie.

## Jak uruchomić?

Z katalogu głównego repozytorium:

```bash
uv sync
uv run python examples/004_depth_proximity_alert/run.py
```

## Sterowanie

```text
q  - zamknięcie dema
h  - pokazanie/ukrycie pomocy
```

## Oczekiwany rezultat

Powinno pojawić się okno z kolorową wizualizacją dysparycji.

W centrum obrazu powinien być widoczny region zainteresowania.

Gdy obiekt zbliża się do tego środkowego regionu:

- status powinien się zmieniać,
- kolor regionu zainteresowania powinien się zmieniać,
- kolor ramki wokół obrazu powinien się zmieniać.

## Pomysły na eksperymenty

Można zmodyfikować:

- rozmiar ROI,
- progi bliskości,
- kolory alertów,
- grubość ramki,
- tekst statusu w HUD-zie,
- typ mapy barw.

Możliwe rozszerzenia:

- dodanie alertów dźwiękowych,
- ekran kalibracji,
- sterowanie progami z klawiatury,
- wiele regionów zainteresowania,
- wskaźnik najbliższego obiektu,
- prosta gra oparta na zbliżaniu i oddalaniu się od kamery.