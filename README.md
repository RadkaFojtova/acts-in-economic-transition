# Chování subjektů v ekonomické transformaci – Analýza emocí a sentimentu

Tato složka obsahuje skripty a notebooky k bakalářské práci Radky Fojtové, která se zabývá analýzou emocí a sentimentu ve výpovědích respondentů k ekonomické transformaci po roce 1989.

## Obsah

| Soubor | Typ | Popis |
|--------|-----|-------|
| `01_trenink_sentiment_modelu.ipynb` | Colab notebook | Trénink sentimentového modelu RobeCzech |
| `02_analyza_rozhovorů.ipynb` | Colab notebook | Aplikace modelu na transkripty rozhovorů |
| `03_NRC_analýza.py` | Python skript | Lexikonová analýza emocí podle skupin respondentů |
| `04_NRC_ngramy.py` | Python skript | N-gramová analýza emocí a výstupní tabulka v HTML |

## Požadavky

Python 3.7+  
Instalace knihoven:
```
pip install -r requirements.txt
```
## Model

Natrénovaný sentimentový model (na bázi RobeCzech) je dostupný zde:  
[Stáhnout model na Google Drive](https://drive.google.com/drive/folders/1D1UUh75EKOWrwWnNvBBrSIuV3_RBCr-k?usp=sharing)

Model obsahuje:
- konfigurační a tokenizer soubory,
- checkpoint natrénovaných vah (`model.safetensors`).

Model není nahrán přímo na GitHub z důvodu velikosti souborů.

## Externí soubory (ke stažení ručně)

Pro správné spuštění skriptů je třeba ručně stáhnout následující soubory:

- [NRC Czech EmoLex lexikon](https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm)
  
- [UDPipe 2 – modely ke stažení](https://ufal.mff.cuni.cz/udpipe/2/models)  
  Doporučený model: `czech-pdt-ud-2.5-191206.udpipe`

## Licence

Skripty a poznámkové bloky jsou dostupné pro nekomerční použití a další výzkum.  
Externí data (lexikony, modely) mají vlastní licence – viz jejich původní zdroje.

