# Moving Depth Target Game

> Mini-gra w czasie rzeczywistym oparta na dysparycji, w której gracz zdobywa punkty, trafiając w ruchome strefy celu.

To demo rozwija pomysł stałej strefy aktywnej w bardziej dynamiczną grę.

Zamiast jednej nieruchomej strefy na środku obrazu aktywny cel pojawia się w różnych miejscach. Gracz zdobywa punkty, przesuwając rękę lub obiekt wystarczająco blisko aktualnej strefy celu.

## Co robi to demo?

Aplikacja:

- tworzy pipeline dysparycji stereo,
- wizualizuje dysparycję za pomocą mapy barw OpenCV,
- generuje strefę celu w losowej pozycji,
- wycina dane dysparycji z aktualnego regionu celu,
- oblicza średnią dysparycję w obszarze celu,
- klasyfikuje bliskość do prostych poziomów,
- nalicza punkty, gdy gracz trafi w aktywny cel,
- przesuwa cel po udanym trafieniu,
- wyświetla wynik i pozostały czas,
- obsługuje restart oraz podstawową interakcję z klawiatury.

## Dlaczego to jest przydatne?

To demo pokazuje, jak computer vision można wykorzystać do stworzenia prostej interaktywnej gry.

W porównaniu ze stałą strefą aktywną ruchomy cel sprawia, że interakcja jest bardziej angażująca. Gracz musi reagować, poruszać się i celować w aktualną pozycję.

Demo jest przydatne dydaktycznie, ponieważ łączy:

- percepcję,
- losowe generowanie celów,
- przetwarzanie regionu zainteresowania,
- logikę decyzyjną w czasie rzeczywistym,
- stan gry,
- wizualną informację zwrotną.

Dobrze sprawdza się także podczas pokazów na żywo, bo uczestnicy mogą rywalizować o lepszy wynik.

## Czego można się nauczyć?

Demo wprowadza do następujących zagadnień:

- ruchome strefy celu,
- znormalizowane współrzędne celu,
- wycinanie ROI dla celu,
- wykrywanie trafienia na podstawie dysparycji,
- logika wyniku i timera,
- przenoszenie celu po zdobyciu punktów,
- punktacja z cooldownem,
- oddzielanie czystej logiki gry od kodu zależnego od kamery.

## Jak to działa?

Gra przechowuje aktywny cel jako znormalizowane współrzędne:

```text
TargetZone(center_x, center_y, scale)
```

Dla każdej klatki:

1. Pobierana jest ramka dysparycji.
2. Aktualna strefa celu jest przeliczana na współrzędne pikselowe.
3. Region celu jest wycinany z ramki dysparycji.
4. Wewnątrz celu obliczana jest średnia dysparycja.
5. Wynik jest klasyfikowany jako `SAFE`, `NEAR` albo `VERY CLOSE`.
6. Jeśli obiekt jest wystarczająco blisko i minął cooldown, naliczane są punkty.
7. Po trafieniu cel przenosi się w nową losową pozycję.

Celem gracza jest trafienie jak największej liczby stref przed końcem czasu.

## Jak uruchomić?

Z katalogu głównego repozytorium:

```bash
uv sync
uv run python examples/007_moving_depth_target_game/run.py
```

## Sterowanie

```text
q  - zamknięcie dema
h  - pokazanie/ukrycie pomocy
r  - restart gry
```

## Oczekiwany rezultat

Powinna pojawić się kolorowa wizualizacja dysparycji.

W obrazie powinna być widoczna strefa celu.

Gdy ręka lub obiekt znajdzie się wystarczająco blisko aktualnego celu:

- wynik powinien wzrosnąć,
- cel powinien przenieść się w nowe miejsce,
- kolor alertu powinien się zmienić,
- panel gry powinien pokazać komunikat trafienia.

Po zakończeniu czasu HUD powinien wyświetlić końcowy wynik.

## Pomysły na eksperymenty

Można zmodyfikować:

- czas gry,
- rozmiar celu,
- zakres pozycji celu,
- liczbę punktów za trafienie,
- cooldown trafień,
- progi bliskości,
- kolory alertów,
- zasady punktacji.

Możliwe rozszerzenia:

- poziomy trudności,
- zmniejszanie celu z czasem,
- zwiększanie szybkości gry po każdym trafieniu,
- efekty dźwiękowe,
- tabela najlepszych wyników,
- ekran startowy,
- odliczanie przed rozpoczęciem gry,
- cele bonusowe,
- strefy karne.