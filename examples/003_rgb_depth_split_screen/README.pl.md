# RGB + Depth Split-Screen

> Demo w czasie rzeczywistym pokazujące zwykły obraz RGB obok kolorowej wizualizacji dysparycji stereo.

To demo łączy dwa sposoby patrzenia na scenę za pomocą kamery OAK-D:

- klasyczny podgląd z kamery RGB,
- kolorową wizualizację dysparycji stereo.

Celem dema jest pokazanie różnicy między tym, co widzi zwykła kamera, a tym, co można uzyskać z pipeline'u stereo vision analizującego geometrię sceny.

## Co robi to demo?

Aplikacja:

- uruchamia strumień z kamery RGB,
- uruchamia strumienie z lewej i prawej kamery monochromatycznej,
- tworzy pipeline dysparycji stereo,
- wizualizuje dysparycję za pomocą mapy barw OpenCV,
- pokazuje obraz RGB i dysparycję obok siebie,
- dodaje etykiety do obu paneli,
- rysuje prosty HUD z FPS i statusem strumienia,
- obsługuje podstawową interakcję z klawiatury.

## Dlaczego to jest przydatne?

To demo jest przydatne, ponieważ pokazuje dwa różne sposoby interpretowania tej samej sceny.

Obraz RGB jest intuicyjny i znany każdemu.  
Wizualizacja dysparycji pokazuje strukturę przestrzenną sceny i pozwala łatwiej odróżnić obszary bliższe od dalszych.

Podczas zajęć lub pokazów na żywo taki widok dzielony ułatwia wyjaśnienie, że systemy computer vision mogą korzystać nie tylko z koloru i tekstury, ale także z geometrii.

## Czego można się nauczyć?

Demo wprowadza do następujących zagadnień:

- strumieniowanie obrazu RGB,
- wizualizacja dysparycji stereo,
- składanie obrazów obok siebie,
- zmiana rozmiaru obrazów w OpenCV,
- mapy barw OpenCV,
- etykietowanie paneli,
- nakładanie HUD-a w czasie rzeczywistym,
- prosta obsługa klawiatury,
- łączenie wielu strumieni z kamery w jednej aplikacji.

## Jak to działa?

Demo buduje pipeline składający się z dwóch części:

```text
strumień RGB                    -> lewy panel
lewa + prawa kamera mono        -> pipeline stereo -> mapa dysparycji -> prawy panel
```

Mapa dysparycji jest normalizowana do zakresu 0-255, a następnie zamieniana na kolorową wizualizację.

Obraz RGB i pokolorowana dysparycja są dopasowywane rozmiarem i łączone poziomo w jeden widok dzielony.

## Jak uruchomić?

Z katalogu głównego repozytorium można uruchomić to demo na trzy sposoby.

Rekomendowana komenda CLI:

```bash
uv run oakvl run rgb-depth-split-screen
```

Można też użyć numeru dema:

```bash
uv run oakvl run 003
```

Bezpośredni punkt startowy przykładu:

```bash
uv run python examples/003_rgb_depth_split_screen/run.py
```

Skrót Makefile:

```bash
make demo-003
```

## Sterowanie

```text
q  - zamknięcie dema
h  - pokazanie/ukrycie pomocy
```

## Oczekiwany rezultat

Powinno pojawić się okno z dwoma panelami:

```text
+----------------------+----------------------+
| RGB camera           | Stereo disparity     |
|                      |                      |
| zwykły obraz kamery  | kolorowa wizualizacja|
|                      | podobna do głębi     |
+----------------------+----------------------+
```

HUD powinien pokazywać:

- nazwę dema,
- wartość FPS,
- status strumienia,
- pomoc dotyczącą klawiszy.

## Pomysły na eksperymenty

Można zmodyfikować:

- etykiety paneli,
- typ mapy barw,
- rozmiar podglądu RGB,
- preset stereo,
- pozycję HUD-a,
- sposób wyświetlania FPS,
- układ widoku dzielonego.

Możliwe rozszerzenia:

- dodanie pionowego trybu split-screen,
- przełączanie map barw klawiszem,
- zapisywanie zrzutu ekranu,
- tryby RGB-only i disparity-only,
- tryb prezentacyjny z większym tekstem,
- trzeci panel z surową dysparycją,
- prosta interakcja zależna od najbliższego widocznego obiektu.