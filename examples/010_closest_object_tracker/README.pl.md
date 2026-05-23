# 010 — Closest Object Tracker

Closest Object Tracker to interaktywne demo OAK-D, które wyszukuje najbliższy region w obrazie dysparycji stereo i prezentuje wynik na HUD-zie z kamery RGB.

Widok RGB pełni rolę głównej warstwy prezentacyjnej dla użytkownika, natomiast kolorowa mapa dysparycji pokazuje warstwę pomiarową/debugową z siatką śledzenia.

## Co pokazuje demo?

- Widok RGB jako warstwę prezentacyjną dla użytkownika
- Dysparycję stereo jako warstwę pomiarową
- Dwumodalną prezentację split-screen
- Analizę dysparycji w siatce regionów
- Wybór regionu najbliższego obiektu
- Klasyfikację bliskości
- Skalowanie regionu między obrazem dysparycji i RGB
- Proste statystyki trackera

## Jak to działa?

Obraz dysparycji jest dzielony na regularną siatkę. Dla każdej komórki demo oblicza średnią niezerową dysparycję. Komórka z największą średnią dysparycją jest traktowana jako region, w którym najprawdopodobniej znajduje się najbliższy widoczny obiekt.

Wybrany region jest podświetlany na obrazie dysparycji i skalowany do widoku RGB na potrzeby prezentacji.

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run closest-object-tracker
```

Można też użyć numeru dema:

```bash
uv run oakvl run 010
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/010_closest_object_tracker/run.py
```

Skrót Makefile:

```bash
make demo-010
```

## Sterowanie

- `R` — reset statystyk
- `Q` lub `ESC` — wyjście

## Oczekiwane działanie

Okno pokazuje dwa widoki obok siebie:

- podgląd RGB po lewej stronie
- kolorową mapę dysparycji po prawej stronie

Na obrazie dysparycji rysowana jest delikatna siatka. Region z największą średnią dysparycją jest podświetlany jako najbliższy wykryty region. Odpowiadający mu przeskalowany region jest również rysowany na HUD-zie RGB.

Przesuń rękę, zeszyt, butelkę albo inny obiekt bliżej kamery. Podświetlony region powinien przesuwać się do tej komórki siatki, w której znajduje się najbliższy obiekt.

HUD pokazuje:

- status detekcji
- średnią dysparycję wybranego regionu
- poziom bliskości
- liczbę przetworzonych klatek
- liczbę detekcji
- współczynnik detekcji
- maksymalną zaobserwowaną dysparycję
- najwyższy poziom bliskości
- krótki komunikat trackera

## Uwagi

Demo wykorzystuje prosty tracker oparty o siatkę regionów. Nie wykonuje semantycznej detekcji obiektów i nie wie, czym jest obiekt. Szacuje jedynie, w której komórce siatki występuje najsilniejsza odpowiedź dysparycji.

Kamery RGB i stereo mają różne punkty widzenia, dlatego region rysowany na RGB jest przybliżoną warstwą prezentacyjną, uzyskaną przez skalowanie z obrazu dysparycji. W późniejszym demie można wykorzystać głębię wyrównaną do RGB albo współrzędne przestrzenne do dokładniejszego śledzenia.

## Pomysły na eksperymenty

- Przesuwaj obiekty przez różne części kadru.
- Zmień rozmiar siatki z `3 x 4` na drobniejszy układ.
- Zwiększ `DEFAULT_MIN_MEAN_DISPARITY`, aby ograniczyć fałszywe detekcje.
- Porównaj, jak małe i duże obiekty wpływają na wybrany region.
- Dodaj wygładzanie, aby podświetlany region zmieniał się mniej gwałtownie.
- Rozbuduj tracker w stronę efektu cząsteczkowego albo mechaniki gry.