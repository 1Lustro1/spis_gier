# Spis gier – instrukcja

## Pliki

| Plik | Zawartość |
|---|---|
| `main.py` | interfejs aplikacji (Kivy) |
| `storage.py` | zapis i odczyt pliku statystyk CSV |
| `theme.py` | motyw kolorów „Zielone sukno” |
| `buildozer.spec` | konfiguracja budowania aplikacji na Androida |
| `.github/workflows/build-apk.yml` | automatyczne budowanie APK na GitHubie |

## 1. Uruchomienie na komputerze (test)

```
pip install kivy==2.3.0
python main.py
```

Na komputerze plik statystyk domyślnie trafia do folderu `SpisGier` w katalogu użytkownika.
Przycisk Esc działa jak przycisk „wstecz” w telefonie.

## 2. Zbudowanie APK – sposób najprostszy (GitHub, bez instalowania niczego)

1. Załóż darmowe konto na github.com i utwórz nowe repozytorium (np. `spis-gier`).
2. Wgraj do niego **całą zawartość folderu SpisGier**, razem z ukrytym folderem `.github`
   (przycisk *Add file → Upload files*; folder `.github/workflows` musi zostać zachowany –
   jeśli przeglądarka go pominie, utwórz plik `.github/workflows/build-apk.yml`
   ręcznie przez *Add file → Create new file* i wklej jego treść).
3. Wejdź w zakładkę **Actions** – budowanie rusza samo (pierwsze trwa ok. 20–40 min).
4. Po zakończeniu kliknij przebieg i pobierz **SpisGier-apk** (plik zip z APK).
5. Skopiuj APK na telefon i zainstaluj (Android zapyta o zgodę na instalację z nieznanego źródła).

## 3. Zbudowanie APK na Windows (alternatywa)

Buildozer działa tylko w Linuksie, więc na Windows potrzebny jest WSL (Ubuntu):

```
wsl --install -d Ubuntu
# w Ubuntu:
sudo apt update && sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev cmake libffi-dev libssl-dev
pip install --user buildozer "cython<3"
cd /mnt/c/.../SpisGier
buildozer -v android debug
```

Gotowy plik pojawi się w folderze `bin/`.

## Gdzie aplikacja trzyma dane na telefonie

Domyślnie: `Pamięć wewnętrzna/Documents/SpisGier/`. Plik można skopiować na komputer
i otworzyć w Excelu (separator `;`). Przy pierwszym uruchomieniu aplikacja poprosi
o utworzenie nowego pliku lub wskazanie istniejącego i zapamięta wybór.

Uwaga: na Androidzie 11+ aplikacja widzi bez problemu pliki, które sama utworzyła.
Plik wgrany z komputera najlepiej otworzyć z folderu „Pobrane”; jeżeli system
go nie pokaże, utwórz nowy plik w aplikacji i podmień jego zawartość.

## Zasady działania

- Karta główna: lista gier (nazwa, uczestnicy, liczba rozgrywek, lider). Dotknięcie otwiera kartę gry.
- Karta gry: klasyfikacja (suma punktów, liczba wygranych rozgrywek, LIDER), lista rozgrywek
  (otwarcie do poprawy, zmiana nazwy, usunięcie), zmiana nazwy i usunięcie gry.
- Karta rozgrywki: tabela wyników, nagłówek z imionami i sumami zawsze widoczny,
  zwycięzca rozgrywki podświetlony na złoto. Wpisanie wartości w ostatnim wierszu
  dodaje kolejny. Dopuszczalne ułamki (przecinek lub kropka) i liczby ujemne;
  błędna wartość podświetla się na czerwono. Wyjście bez zapisu – pytanie „Zapisać?”.
- Przy tworzeniu gry wybierasz, czy wygrywa najwięcej, czy najmniej punktów (np. golf).
- Zapis do pliku następuje po każdej zmianie, przy zamknięciu karty gry i karty głównej.
