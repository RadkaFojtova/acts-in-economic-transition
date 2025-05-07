# ===============================================
# Lexikonová analýza emocí v rozhovorech
# Autor: Radka Fojtová
# Popis: Skript načítá transkripty rozhovorů, provádí lemmatizaci pomocí UDPipe
# a následně přiřazuje emoce ze slovníku NRC Czech EmoLex. Věty jsou analyzovány
# podle výskytu emocí a výsledky jsou agregovány podle kategorií respondentů.
# ===============================================

import os
import pandas as pd
import ufal.udpipe
import re
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

# ----------------------------
# Nastaveni cest a modelu
# ----------------------------

#Seznam složek s texty rozhovorů rozdělenými podle skupin
SLOZKY_ANALYZA = []

CSTA_NRC = 'Czech-NRC-EmoLex.txt'
CSTA_MODELU = 'czech-pdt-ud-2.5-191206.udpipe'

# Seznam slov ze slovniku, ktere nenesou žádnou emoci
IGNOROVAT_SLOVA = {}

# Emoce k ignorovani pro konkretni slova, např. 'dobrý': {'fear'}
IGNOROVAT_EMOCE_PRO_SLOVO = {}

# Barvy pro grafy, např. 'Bankéři': 'blue'
BARVY = {}

# Preklad emoci do cestiny
PREKLAD_EMOCI = {
    'anger': 'hněv',
    'anticipation': 'očekávání',
    'disgust': 'odpor',
    'fear': 'strach',
    'joy': 'radost',
    'sadness': 'smutek',
    'surprise': 'překvapení',
    'trust': 'důvěra',
    'positive': 'pozitivní',
    'negative': 'negativní'
}

# ----------------------------
# Funkce
# ----------------------------

# Načtení slovníku
def nacti_nrc(cesta):
    df = pd.read_csv(cesta, sep='\t')
    slovnik = defaultdict(set)         
    emoce = ['anger','anticipation','disgust','fear',
             'joy','negative','positive','sadness',
             'surprise','trust']
    for _, row in df.iterrows():
        w = row['Czech Word'].strip().lower()
        for emo in emoce:
            if row[emo] == 1:
                slovnik[w].add(emo)     
    return slovnik


# Načtení modelu UDPipe
def nacti_model(cesta_modelu):
    model = ufal.udpipe.Model.load(cesta_modelu)
    if not model:
        raise Exception("Nepodarilo se nacist model UDPipe!")
    return model

# Lemmatizace
def lemmatizuj_vetu(text, model):
    pipeline = ufal.udpipe.Pipeline(model, 'tokenize', 'tag', 'parse', 'conllu')
    error = ufal.udpipe.ProcessingError()
    processed = pipeline.process(text, error)
    lemmata = []
    for line in processed.split('\n'):
        if line and not line.startswith('#'):
            cols = line.split('\t')
            if len(cols) > 2:
                lemma = cols[2]
                lemmata.append(lemma)
    return lemmata

# ----------------------------
# Spuštění analýzy
# ----------------------------

if __name__ == '__main__':
    print("\n✅ Načítám NRC slovník...")
    nrc_slovnik = nacti_nrc(CSTA_NRC)

    print("\n✅ Načítám UDPipe model...")
    model = nacti_model(CSTA_MODELU)

    vysledky_graf = defaultdict(dict)
    celkem_vet_slovnik = {}

    for slozka in SLOZKY_ANALYZA:
        print(f"\n\U0001F4C2 Pripravuji analyzu slozky: {slozka}")

        cesta_slozka = slozka
        emoce_counter = Counter()
        slova_podle_emoci = defaultdict(Counter)
        celkem_vet = 0

        for soubor in os.listdir(cesta_slozka):
            if soubor.endswith('.txt'):
                cesta = os.path.join(cesta_slozka, soubor)
                with open(cesta, 'r', encoding='utf-8') as f:
                    texty = f.readlines()

                for veta in texty:
                    veta = veta.strip()
                    if not veta:
                        continue

                    lemmata = lemmatizuj_vetu(veta, model)

                    aktualni_emoce = set()

                    for slovo in lemmata:
                        slovo_ciste = slovo.lower()
                        if re.match(r'^[a-zá-žÁ-Ž]+$', slovo_ciste) and slovo_ciste not in IGNOROVAT_SLOVA:
                            if slovo_ciste in nrc_slovnik:
                                zakazane = IGNOROVAT_EMOCE_PRO_SLOVO.get(slovo_ciste, set())
                                for emo in nrc_slovnik[slovo_ciste]:
                                    if emo not in zakazane:
                                        emoce_counter[emo] += 1
                                        slova_podle_emoci[emo][slovo_ciste] += 1
                                        aktualni_emoce.add(emo)

                    celkem_vet += 1
                    for emo in aktualni_emoce:
                        vysledky_graf[emo][slozka] = vysledky_graf[emo].get(slozka, 0) + 1

        celkem_vet_slovnik[slozka] = celkem_vet

        print(f"\nShrnutí pro složku {slozka}:")
        print(f"Celkový počet vět: {celkem_vet}")

        vsechny_emoce = sorted(set(emoce_counter.keys()))
        
        #Výpis nejčastějších emočních slov pro kontrolu
        for emo in vsechny_emoce:
            print(f"\nEmoce: {emo}")
            print(f"Výskyt: {emoce_counter[emo]}x")
            print("Top 10 slov pro tuto emoci:")
            for slovo, pocet in slova_podle_emoci[emo].most_common(10):
                print(f"{slovo}: {pocet}x")

    print("\n✅ Analyza vsech slozek dokoncena.")

    # ----------------------------
    # Vykreslení grafu
    # ----------------------------
    print("\n\U0001F4CA Vykresluji graf emocí...")

    emoce = sorted(vysledky_graf.keys())
    slozky = SLOZKY_ANALYZA

    data = {slozka: [vysledky_graf[emo].get(slozka, 0) for emo in emoce] for slozka in slozky}
    total = celkem_vet_slovnik

    x = range(len(emoce))
    bar_width = 0.2

    center_offset = bar_width * (len(slozky) - 1) / 2

    plt.figure(figsize=(14, 6))
    for i, slozka in enumerate(slozky):
        positions = [val + bar_width * i for val in x]
        y = [data[slozka][j] / total[slozka] if total[slozka] > 0 else 0 for j in range(len(emoce))]
        plt.bar(positions, y, width=bar_width, label=slozka, color=BARVY[slozka])

    plt.xticks([val + center_offset for val in x], [PREKLAD_EMOCI.get(emo, emo) for emo in emoce], rotation=45, fontsize=16)
    plt.legend()
    plt.tight_layout()
    plt.show()