# 012 — Depth Dodge / Avoider Game

Depth Dodge / Avoider Game to interaktywna mini-gra OAK-D, w której gracz musi unikać stref zagrożenia opartych o dane głębi.

Widok RGB pełni rolę głównego HUD-u gry, natomiast kolorowa mapa dysparycji jest pokazana obok jako warstwa pomiarowa/debugowa. Jedna strefa jest podświetlana jako aktualna strefa zagrożenia. Gracz zdobywa punkty, utrzymując rękę lub obiekt poza tą strefą do momentu jej zmiany.

## Co pokazuje demo?

- Widok RGB jako warstwę prezentacyjną gry
- Dysparycję stereo jako warstwę pomiarową
- Dwumodalną prezentację split-screen
- Interaktywne strefy oparte o głębię
- Detekcję kolizji ze strefą zagrożenia
- Obsługę żyć, wyniku i liczby kolizji
- Czasową zmianę aktywnej strefy
- Logikę gry możliwą do testowania bez kamery

## Jak to działa?

Obraz jest dzielony na cztery pionowe strefy. Jedna z nich jest wybierana jako aktywna strefa zagrożenia.

Dla każdej strefy demo oblicza średnią niezerową dysparycję. Jeśli aktywna strefa zagrożenia przejdzie w stan `NEAR` albo `VERY_CLOSE`, gra rejestruje kolizję, a gracz traci jedno życie.

Jeśli gracz przetrwa do momentu zmiany strefy zagrożenia, wynik zostaje zwiększony.

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run depth-dodge-avoider-game
```

Można też użyć numeru dema:

```bash
uv run oakvl run 012
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/012_depth_dodge_avoider_game/run.py
```

Skrót Makefile:

```bash
make demo-012
```

## Sterowanie

- `R` — restart gry
- `Q` lub `ESC` — wyjście

## Oczekiwane działanie

Okno pokazuje dwa widoki obok siebie:

- podgląd RGB po lewej stronie
- kolorową mapę dysparycji po prawej stronie

Na obu widokach rysowane są cztery strefy. Jedna z nich jest oznaczona jako `DANGER`. Przesuwaj rękę, zeszyt, butelkę albo inny obiekt przez strefy bezpieczne i unikaj aktywnej strefy zagrożenia.

HUD pokazuje:

- wynik
- pozostałe życia
- liczbę kolizji
- aktywną strefę
- czas do kolejnej zmiany strefy
- aktualny komunikat gry
- sterowanie

## Uwagi

Demo wykorzystuje dysparycję jako względny sygnał bliskości, a nie skalibrowany pomiar metryczny.

Kamery RGB i stereo mają różne punkty widzenia, dlatego strefy pokazane na obrazie RGB i dysparycji należy traktować jako przybliżenie prezentacyjne. Jest to wystarczające dla interaktywnej mechaniki gry, ale nie służy do precyzyjnego śledzenia metrycznego.

## Pomysły na eksperymenty

- Zmień liczbę stref.
- Dostosuj szybkość zmiany strefy zagrożenia.
- Dostosuj cooldown kolizji.
- Zwiększaj poziom trudności wraz z czasem gry.
- Dodaj efekty dźwiękowe dla punktów, kolizji i końca gry.
- Dodaj tabelę najlepszych wyników.
- Rozbuduj grę w stronę pełnej gry ruchowej opartej o estymację pozy.