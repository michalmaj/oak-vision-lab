# 008 — Reaction Time Game

Reaction Time Game to interaktywne demo OAK-D, które mierzy szybkość reakcji użytkownika na strefę celu opartą o dane głębi.

Demo wyświetla centralną strefę celu na kolorowej wizualizacji dysparycji stereo. Gracz musi poczekać, aż cel stanie się aktywny, a następnie jak najszybciej zbliżyć rękę lub obiekt do kamery w zaznaczonym obszarze.

## Co pokazuje demo?

- Wizualizację dysparycji stereo
- Interakcję opartą o głębię
- Analizę obszaru zainteresowania
- Pomiar czasu reakcji
- Zarządzanie stanem gry
- Logikę gry możliwą do testowania bez kamery

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run reaction-time-game
```

Można też użyć numeru dema:

```bash
uv run oakvl run 008
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/008_reaction_time_game/run.py
```

Skrót Makefile:

```bash
make demo-008
```

## Sterowanie

- `R` — restart gry
- `Q` lub `ESC` — wyjście

## Oczekiwane działanie

Gra zaczyna się od krótkiego losowego oczekiwania. Gdy cel zmieni stan na `HIT NOW!`, należy jak najszybciej przesunąć rękę lub obiekt w zaznaczony obszar i zbliżyć go do kamery.

HUD pokazuje:

- pozostały czas
- wynik
- aktualną fazę
- ostatni czas reakcji
- najlepszy czas reakcji
- średni czas reakcji
- średnią dysparycję w obszarze celu
- poziom bliskości

## Pomysły na eksperymenty

- Sprawdź reakcję ręką, zeszytem lub innym obiektem.
- Zmień rozmiar strefy celu.
- Dostosuj próg bliskości.
- Dodaj karę za zbyt wczesny ruch.
- Dodaj efekty dźwiękowe przy trafieniu i końcu gry.