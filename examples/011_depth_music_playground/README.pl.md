# 011 — Depth Music Playground

Depth Music Playground to interaktywne demo OAK-D, które zamienia strefy oparte o dane głębi w wizualny instrument muzyczny.

Widok RGB pełni rolę głównej warstwy prezentacyjnej i HUD-u, natomiast kolorowa mapa dysparycji jest pokazana obok jako warstwa pomiarowa/debugowa. Przesunięcie ręki lub obiektu do jednej ze stref wyzwala wizualne zdarzenie nuty.

## Co pokazuje demo?

- Widok RGB jako warstwę prezentacyjną dla użytkownika
- Dysparycję stereo jako warstwę pomiarową
- Dwumodalną prezentację split-screen
- Interaktywne strefy oparte o głębię
- Analizę dysparycji w obszarach zainteresowania
- Wizualne wyzwalanie nut
- Logikę cooldownu dla każdej strefy
- Logikę interakcji możliwą do testowania bez kamery

## Jak to działa?

Obraz jest dzielony na poziome strefy muzyczne, z których każda odpowiada jednej nucie:

```text
C  D  E  G  A
```

Dla każdej strefy demo oblicza średnią niezerową dysparycję. Jeśli strefa przechodzi w stan `NEAR` albo `VERY_CLOSE`, staje się aktywna i może wyzwolić zdarzenie nuty. Każda strefa ma krótki cooldown, aby zapobiec wyzwalaniu nuty w każdej klatce.

Aktualna wersja zapewnia wizualne wyzwalanie nut. Wyjście audio można dodać jako opcjonalne rozszerzenie.Aktualna wersja zapewnia wizualne wyzwalanie nut oraz opcjonalne wyjście audio oparte o pygame. Jeśli inicjalizacja audio się nie powiedzie, demo nadal działa wizualnie.

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run depth-music-playground
```

Można też użyć numeru dema:

```bash
uv run oakvl run 011
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/011_depth_music_playground/run.py
```

Skrót Makefile:

```bash
make demo-011
```

## Sterowanie

- `R` — reset stanu
- `Q` lub `ESC` — wyjście

## Oczekiwane działanie

Okno pokazuje dwa widoki obok siebie:

- podgląd RGB po lewej stronie
- kolorową mapę dysparycji po prawej stronie
- Jeśli audio jest dostępne, każda zaznaczona strefa odtwarza również krótką nutę.

Na obu widokach rysowanych jest pięć stref muzycznych. Przesuń rękę, zeszyt, butelkę albo inny obiekt do jednej ze stref i zbliż go do kamery. Aktywna strefa powinna się rozświetlić i wyzwolić wizualne zdarzenie nuty.

HUD pokazuje:

- łączną liczbę wyzwolonych zdarzeń
- ostatnią wyzwoloną nutę
- aktualny komunikat muzyczny
- sterowanie

## Uwagi

Demo wykorzystuje dysparycję jako względny sygnał bliskości, a nie skalibrowany pomiar metryczny.

Kamery RGB i stereo mają różne punkty widzenia, dlatego strefy pokazane na obrazie RGB i dysparycji należy traktować jako przybliżenie prezentacyjne. Jest to wystarczające dla interaktywnego instrumentu wizualnego, ale nie służy do precyzyjnego śledzenia metrycznego.

## Pomysły na eksperymenty

- Zmień sekwencję nut.
- Dodaj więcej albo mniej stref.
- Dostosuj cooldown wyzwalania.
- Dodaj wyjście audio dla każdej nuty.
- Dodaj różne efekty wizualne dla poszczególnych nut.
- Rozbuduj demo w stronę interakcji typu laser harp.
- Dodaj tryb nagrywania krótkiej sekwencji wyzwolonych nut.