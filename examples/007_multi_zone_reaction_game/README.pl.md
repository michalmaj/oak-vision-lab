# Multi-Zone Reaction Game

> Gra refleksowa w czasie rzeczywistym oparta na dysparycji, w której gracz zdobywa punkty, trafiając w aktualnie aktywną strefę.

To demo zamienia dysparycję stereo w prostą grę refleksową w stylu arcade.

Na ekranie widocznych jest kilka stref, ale tylko jedna jest aktywna w danym momencie. Gracz musi przesunąć rękę lub obiekt wystarczająco blisko aktywnej strefy. Po udanym trafieniu aktywna strefa zmienia się na inną.

## Co robi to demo?

Aplikacja:

- tworzy pipeline dysparycji stereo,
- wizualizuje dysparycję za pomocą mapy barw OpenCV,
- wyświetla kilka stref reakcji,
- wyróżnia aktualnie aktywną strefę,
- wycina dane dysparycji z aktywnej strefy,
- oblicza średnią dysparycję w tej strefie,
- klasyfikuje bliskość do prostych poziomów,
- nalicza punkty, gdy gracz trafi w aktywną strefę,
- zmienia aktywną strefę po udanym trafieniu,
- wyświetla wynik i pozostały czas,
- obsługuje restart oraz podstawową interakcję z klawiatury.

## Dlaczego to jest przydatne?

To demo pokazuje, jak computer vision może wspierać szybką, interaktywną informację zwrotną.

W porównaniu z jedną stałą strefą wiele stref sprawia, że interakcja jest bardziej dynamiczna. Gracz musi reagować na zmieniający się cel i przesuwać się w odpowiedni obszar.

Demo jest przydatne dydaktycznie, ponieważ łączy:

- percepcję,
- przetwarzanie regionów zainteresowania,
- prostą logikę decyzyjną,
- stan gry,
- interakcję opartą na refleksie,
- wizualną informację zwrotną w czasie rzeczywistym.

Dobrze sprawdza się także podczas pokazów na żywo, ponieważ uczestnicy mogą rywalizować o lepszy wynik.

## Czego można się nauczyć?

Demo wprowadza do następujących zagadnień:

- wiele stref interakcji,
- wybór aktywnego celu,
- wycinanie ROI na podstawie strefy,
- wykrywanie trafienia na podstawie informacji podobnej do głębi,
- mechanika gry refleksowej,
- logika wyniku i timera,
- punktacja z cooldownem,
- wykorzystanie wspólnych narzędzi `depth` i `game`.

## Jak to działa?

Demo definiuje cztery strefy reakcji:

```text
+-------------------------+
|     A           B       |
|                         |
|                         |
|     C           D       |
+-------------------------+
```

Dla każdej klatki:

1. Pobierana jest ramka dysparycji.
2. Wybierana jest aktualnie aktywna strefa.
3. Aktywna strefa jest przeliczana na współrzędne pikselowe.
4. ROI aktywnej strefy jest wycinane z ramki dysparycji.
5. Wewnątrz aktywnej strefy obliczana jest średnia dysparycja.
6. Wynik jest klasyfikowany jako `SAFE`, `NEAR` albo `VERY CLOSE`.
7. Jeśli obiekt jest wystarczająco blisko i minął cooldown, naliczane są punkty.
8. Po trafieniu aktywna strefa zmienia się na inną.

Celem gracza jest trafienie jak największej liczby aktywnych stref przed końcem czasu.

## Jak uruchomić?

Z katalogu głównego repozytorium:

```bash
uv sync
uv run python examples/007_multi_zone_reaction_game/run.py
```

## Sterowanie

```text
q  - zamknięcie dema
h  - pokazanie/ukrycie pomocy
r  - restart gry
```

## Oczekiwany rezultat

Powinna pojawić się kolorowa wizualizacja dysparycji.

Na ekranie powinny być widoczne cztery strefy. Jedna z nich powinna być oznaczona jako aktywna.

Gdy ręka lub obiekt znajdzie się wystarczająco blisko aktywnej strefy:

- wynik powinien wzrosnąć,
- inna strefa powinna stać się aktywna,
- kolor alertu powinien się zmienić,
- panel gry powinien pokazać komunikat trafienia.

Po zakończeniu czasu HUD powinien wyświetlić końcowy wynik.

## Pomysły na eksperymenty

Można zmodyfikować:

- liczbę stref,
- pozycje stref,
- rozmiar stref,
- czas gry,
- liczbę punktów za trafienie,
- cooldown trafień,
- progi bliskości,
- zasady wyboru aktywnej strefy.

Możliwe rozszerzenia:

- poziomy trudności,
- zmniejszające się strefy,
- strefy karne,
- strefy bonusowe,
- efekty dźwiękowe,
- tabela najlepszych wyników,
- pomiar czasu reakcji,
- tryb prezentacyjny z większymi etykietami.