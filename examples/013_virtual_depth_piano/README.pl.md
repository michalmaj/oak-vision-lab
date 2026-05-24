# 013 — Virtual Depth Piano

Virtual Depth Piano to interaktywne demo OAK-D, które łączy podgląd RGB, śledzenie dłoni przez MediaPipe, dysparycję stereo oraz dźwięk generowany przez pygame.

Demo rysuje pseudo-trójwymiarowe klawisze pianina na obrazie z kamery RGB. MediaPipe wykrywa czubek palca wskazującego, a dysparycja stereo służy jako dodatkowy sygnał głębi do określenia, czy klawisz został faktycznie wciśnięty.

## Co pokazuje demo?

- Widok RGB jako warstwę prezentacyjną dla użytkownika
- Pseudo-trójwymiarowe wirtualne klawisze
- Śledzenie dłoni z użyciem MediaPipe
- Wykrywanie najechania palcem na klawisz
- Wykrywanie wciśnięcia klawisza wspomagane głębią
- Lokalny pomiar dysparycji wokół czubka palca
- Dwumodalną prezentację RGB + dysparycja
- Dźwięki nut generowane przez pygame
- Testowalną geometrię i logikę interakcji oddzieloną od wejścia z kamery

## Wymagany lokalny model

Demo wykorzystuje MediaPipe Tasks Hand Landmarker i wymaga lokalnego pliku modelu:

```text
models/mediapipe/hand_landmarker.task
```

Plik modelu nie jest commitowany do repozytorium. Przed uruchomieniem dema należy umieścić pobrany plik `hand_landmarker.task` w tej ścieżce.

Ścieżka `models/mediapipe/*.task` jest ignorowana przez Git, ponieważ model jest zasobem binarnym.

## Jak to działa?

Obraz RGB jest używany jako główna warstwa prezentacyjna. W dolnej części kadru rysowany jest zestaw pseudo-trójwymiarowych klawiszy:

```text
C  D  E  G  A
```

MediaPipe wykrywa czubek palca wskazującego we współrzędnych obrazu RGB. Punkt palca jest sprawdzany względem wielokątów reprezentujących wirtualne klawisze, aby określić stan najechania.

W przypadku wciśnięcia wspomaganego głębią pozycja palca jest skalowana do obrazu dysparycji. Wokół tego punktu pobierany jest mały lokalny obszar ROI. Jeśli średnia lokalna dysparycja przekracza próg wciśnięcia, klawisz znajdujący się pod palcem jest traktowany jako wciśnięty i odtwarzana jest nuta.

Widok dysparycji po prawej stronie pełni rolę warstwy pomiarowej/debugowej i pokazuje lokalny ROI używany do pomiaru głębi wokół palca.

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run virtual-depth-piano
```

Można też użyć numeru dema:

```bash
uv run oakvl run 013
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/013_virtual_depth_piano/run.py
```

Skrót Makefile:

```bash
make demo-013
```

## Sterowanie

- `Q` lub `ESC` — wyjście

## Oczekiwane działanie

Okno pokazuje dwa widoki obok siebie:

- podgląd RGB po lewej stronie
- kolorową mapę dysparycji po prawej stronie

Przesuń palec wskazujący nad wirtualne klawisze. Klawisz powinien się podświetlić, gdy czubek palca znajdzie się nad nim. Zbliż palec do kamery, aby spełnić próg wciśnięcia oparty o głębię i wyzwolić nutę.

HUD pokazuje:

- liczbę wykrytych czubków palców
- liczbę palców spełniających warunek depth press
- maksymalną lokalną dysparycję palca
- próg wciśnięcia
- status audio
- łączną liczbę wyzwolonych nut
- ostatnią wyzwoloną nutę

## Uwagi

Demo wykorzystuje przybliżone mapowanie między współrzędnymi RGB i dysparycji. Kamery RGB i stereo mają różne punkty widzenia, dlatego mapowanie palca z RGB na dysparycję jest przybliżeniem prezentacyjnym.

Większy lokalny ROI wokół palca zwiększa tolerancję interakcji.

Jeśli inicjalizacja audio się nie powiedzie, demo nadal działa wizualnie.

## Pomysły na eksperymenty

- Dostosuj `DEFAULT_PRESS_DISPARITY_THRESHOLD`.
- Zmień układ klawiszy.
- Dodaj więcej nut.
- Włącz obsługę wielu palców.
- Dodaj czarne klawisze.
- Dodaj animacje zwolnienia klawisza.
- Dodaj tryb nagrywania krótkich melodii.
- Rozbuduj demo w stronę laser harp albo air piano.