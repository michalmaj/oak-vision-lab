# Depth Hot Zone Game

> Mini-gra w czasie rzeczywistym, w której gracz zdobywa punkty, przesuwając rękę lub obiekt do strefy aktywnej opartej na dysparycji.

To demo zamienia wizualizację dysparycji stereo w prostą interaktywną grę.

Gracz ma ograniczony czas na przesuwanie obiektu do środkowej strefy aktywnej. Gdy obiekt jest wystarczająco blisko, gra nalicza punkty.

## Co robi to demo?

Aplikacja:

- tworzy pipeline dysparycji stereo,
- wizualizuje dysparycję za pomocą mapy barw OpenCV,
- wycina środkową strefę aktywną,
- oblicza średnią dysparycję w tej strefie,
- klasyfikuje bliskość do prostych poziomów,
- nalicza punkty, gdy gracz trafi do aktywnej strefy,
- używa cooldownu, aby nie naliczać punktów w każdej klatce,
- wyświetla wynik i pozostały czas,
- obsługuje restart oraz podstawową interakcję z klawiatury.

## Dlaczego to jest przydatne?

To demo pokazuje, jak computer vision może sterować prostą interakcją i logiką gry.

Jest przydatne dydaktycznie, ponieważ łączy kilka pojęć:

- percepcję,
- przetwarzanie regionu zainteresowania,
- klasyfikację opartą na progach,
- informację zwrotną w czasie rzeczywistym,
- stan aplikacji,
- prostą mechanikę gry.

Sprawdza się również podczas warsztatów i pokazów na żywo, ponieważ uczestnicy mogą natychmiast wejść w interakcję z systemem, używając tylko ręki lub niewielkiego obiektu.

## Czego można się nauczyć?

Demo wprowadza do następujących zagadnień:

- interakcja podobna do głębi z użyciem dysparycji stereo,
- wykrywanie strefy aktywnej,
- analiza średniej dysparycji,
- punktacja oparta na bliskości,
- logika gry z cooldownem,
- licznik czasu,
- informacja zwrotna w HUD-zie,
- oddzielanie czystej logiki gry od kodu zależnego od kamery.

## Jak to działa?

Demo wykorzystuje środkowy region zainteresowania jako aktywną strefę gry:

```text
+-------------------------+
|                         |
|         +-------+       |
|         |  HOT  |       |
|         | ZONE  |       |
|         +-------+       |
|                         |
+-------------------------+
```

Dla każdej klatki:

1. Pobierana jest ramka dysparycji.
2. Wycinana jest środkowa strefa aktywna.
3. Obliczana jest średnia dysparycja w tej strefie.
4. Wynik jest klasyfikowany jako `SAFE`, `NEAR` albo `VERY CLOSE`.
5. Jeśli obiekt jest wystarczająco blisko i minął cooldown, naliczane są punkty.
6. HUD pokazuje wynik, pozostały czas, status i sterowanie.

## Jak uruchomić?

Z katalogu głównego repozytorium:

```bash
uv sync
uv run python examples/005_depth_hot_zone_game/run.py
```

## Sterowanie

```text
q  - zamknięcie dema
h  - pokazanie/ukrycie pomocy
r  - restart gry
```

## Oczekiwany rezultat

Powinna pojawić się kolorowa wizualizacja dysparycji.

W centrum obrazu powinna być widoczna strefa aktywna.

Gdy ręka lub obiekt zbliży się wystarczająco do tej strefy:

- wynik powinien wzrosnąć,
- kolor alertu powinien się zmienić,
- panel gry powinien pokazać komunikat trafienia.

Po zakończeniu czasu HUD powinien wyświetlić końcowy wynik.

## Pomysły na eksperymenty

Można zmodyfikować:

- czas gry,
- liczbę punktów za trafienie,
- cooldown trafień,
- rozmiar strefy aktywnej,
- progi bliskości,
- kolory alertów,
- rozmiar tekstu,
- zasady punktacji.

Możliwe rozszerzenia:

- poziomy trudności,
- ruchome strefy aktywne,
- wiele stref aktywnych,
- efekty dźwiękowe,
- tabela najlepszych wyników,
- ekran startowy,
- odliczanie przed rozpoczęciem gry,
- tryb wieloosobowy ze strefą po lewej i prawej stronie.