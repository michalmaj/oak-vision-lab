# 009 — Object Distance Meter

Object Distance Meter to interaktywne demo OAK-D, które łączy podgląd z kamery RGB z pomiarem opartym o dysparycję stereo.

Widok RGB pełni rolę głównej warstwy prezentacyjnej i HUD-u, natomiast kolorowa mapa dysparycji jest pokazana obok jako warstwa pomiarowa/debugowa. Demo mierzy średnią dysparycję w centralnym obszarze zainteresowania i zamienia ją na prosty wskaźnik bliskości.

## Co pokazuje demo?

- Widok RGB jako warstwę prezentacyjną dla użytkownika
- Dysparycję stereo jako warstwę pomiarową
- Dwumodalną prezentację split-screen
- Analizę dysparycji w obszarze zainteresowania
- Klasyfikację bliskości opartą o dane głębi
- Wizualizację wskaźnika bliskości w czasie rzeczywistym
- Proste statystyki: liczba próbek, minimalna/maksymalna dysparycja oraz najwyższy poziom bliskości

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run object-distance-meter
```

Można też użyć numeru dema:

```bash
uv run oakvl run 009
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/009_object_distance_meter/run.py
```

Skrót Makefile:

```bash
make demo-009
```

## Sterowanie

- `R` — reset statystyk
- `Q` lub `ESC` — wyjście

## Oczekiwane działanie

Okno pokazuje dwa widoki obok siebie:

- podgląd RGB po lewej stronie
- kolorową mapę dysparycji po prawej stronie

Centralny obszar zainteresowania jest rysowany na obu widokach. Pomiar jest obliczany na podstawie obrazu dysparycji, a wynik jest prezentowany na HUD-zie RGB.

Zbliż rękę, zeszyt, butelkę albo inny obiekt do kamery. Wskaźnik bliskości powinien rosnąć wraz ze zbliżaniem obiektu.

HUD pokazuje:

- średnią dysparycję
- poziom bliskości
- liczbę próbek
- minimalną i maksymalną zaobserwowaną dysparycję
- najwyższy poziom bliskości
- krótki komunikat zależny od bliskości

## Uwagi

Demo wykorzystuje dysparycję jako względny sygnał bliskości, a nie skalibrowany pomiar metryczny w centymetrach lub metrach.

Kamery RGB i stereo mają różne punkty widzenia, dlatego obszary pokazane na obrazie RGB i obrazie dysparycji należy traktować jako przybliżenie prezentacyjne. W późniejszym demie można wykorzystać głębię wyrównaną do RGB albo współrzędne przestrzenne do dokładniejszego pomiaru metrycznego.

## Pomysły na eksperymenty

- Przesuwaj różne obiekty przez obszar zainteresowania.
- Porównaj, jak ręka, zeszyt, butelka i większe obiekty wpływają na średnią dysparycję.
- Zmień rozmiar obszaru zainteresowania.
- Dostosuj progi `near` i `very close`.
- Spróbuj użyć tylko widoku RGB jako warstwy prezentacyjnej.
- Rozbuduj demo w stronę skalibrowanej taśmy mierniczej 3D.