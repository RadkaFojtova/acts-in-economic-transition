# ===============================================
# NRC analýza emocí s výpočtem n-gramů (1–3 slova)
# Autor: Radka Fojtová
# Popis: Skript načítá texty rozhovorů, lemmatizuje je pomocí UDPipe
# a provádí n-gramovou analýzu podle emocí ze slovníku NRC EmoLex.
# Výsledkem je tabulka četností (unigramy x emoce), uložená do HTML souboru.
# ===============================================

import os
import re
import csv
import ufal.udpipe
import pandas as pd
from collections import defaultdict, Counter
from itertools import islice

# ----------------------------
# Konfigurace
# ----------------------------

# Cesta k analyzované složce
FOLDER = ''

CSTA_NRC   = 'Czech-NRC-EmoLex.txt'
CSTA_MODEL = 'czech-pdt-ud-2.5-191206.udpipe'

# ----------------------------
# Stop-slovníky
# ----------------------------

# Seznamy ze skriptu '03_NRC_analýza.py' k ignorování jejich emocí:
# Slova, která nechceme zvažovat vůbec
IGNOROVAT_SLOVA_NRC = {}
# Emoce, které ignorujeme pro konkrétní slova
IGNOROVAT_EMOCE_PRO_SLOVO = {}

# Seznam slov, které nenesou důležitý význam a budou vyřazeny z výsledků, např. zájmena, spojky atd.
STOPWORDS_NGRAM = {}

# ----------------------------
# Načtení NRC lexikonu
# ----------------------------
def load_nrc(path):
    slovnik=defaultdict(set)
    with open(path,encoding='utf-8') as f:
        reader=csv.DictReader(f,delimiter='\t')
        emo_cols=[c for c in reader.fieldnames if c not in('English Word','Czech Word')]
        for row in reader:
            w=row['Czech Word'].strip().lower()
            if not w or w in IGNOROVAT_SLOVA_NRC: continue
            for emo in emo_cols:
                if row.get(emo)=='1': slovnik[w].add(emo.lower())
    return slovnik

# ----------------------------
# UDPipe a lemmatizace
# ----------------------------
def load_udpipe_model(path):
    model=ufal.udpipe.Model.load(path)
    if not model: raise Exception("Nepodařilo se načíst UDPipe model!")
    return model

def lemmatize_sentence(sent,model):
    pipeline=ufal.udpipe.Pipeline(model,'tokenize','tag','parse','conllu')
    err=ufal.udpipe.ProcessingError()
    out=pipeline.process(sent,err)
    lem = []
    for line in out.split('\n'):
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) <= 3:
            continue
        lemma = parts[2].lower()
        upos = parts[3]  # ← TADY doplněno

        if upos == 'NUM' or lemma.isdigit():
            lem.append(lemma)
        elif lemma not in STOPWORDS_NGRAM:
            lem.append(lemma)
    return lem

# ----------------------------
# N-gramy
# ----------------------------
def ngrams(tokens,n): return zip(*(islice(tokens,i,None) for i in range(n)))

# ----------------------------
# Čtení vět
# ----------------------------
def read_sentences(folder):
    s=[]
    for fn in os.listdir(folder):
        if fn.lower().endswith('.txt'):
            with open(os.path.join(folder,fn),encoding='utf-8') as f:
                s+=[l.strip() for l in f if l.strip()]
    return s

# ----------------------------
# Výpočet n-gramů podle emocí
# ----------------------------
def top_ngrams_by_emotion(nrc, model, sents, stopw, emo_filter):
    uni = defaultdict(Counter)
    bi = defaultdict(Counter)
    tri = defaultdict(Counter)

    for sent in sents:
        segments = re.split(r'[.,?!\-]', sent)
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            lem = lemmatize_sentence(seg, model)
            emos = {e for tok in lem for e in nrc.get(tok, []) if e not in emo_filter.get(tok, set())}
            toks = [t for t in lem if t.isalpha() and t not in stopw]
            for e in emos:
                uni[e].update(toks)
                for bg in ngrams(toks, 2):
                    bi[e][' '.join(bg)] += 1
                for tg in ngrams(toks, 3):
                    tri[e][' '.join(tg)] += 1

    return {
        'unigrams_raw': uni,
        'bigrams_raw': bi,
        'trigrams_raw': tri
    }

# ----------------------------
# Hlavní část skriptu
# ----------------------------
if __name__ == '__main__':
    print(f"Načítám NRC z '{CSTA_NRC}'…")
    nrc = load_nrc(CSTA_NRC)
    print(f"Načítám UDPipe model z '{CSTA_MODEL}'…")
    model = load_udpipe_model(CSTA_MODEL)
    print(f"Načítám věty ze složky '{FOLDER}'…")
    sents = read_sentences(FOLDER)
    print(f"Počet vět: {len(sents)}")

    results = top_ngrams_by_emotion(nrc, model, sents, STOPWORDS_NGRAM, IGNOROVAT_EMOCE_PRO_SLOVO)

    # Vytvoření matice emoce × n-gramy ze všech (uni + bi + tri)
    all_raw = defaultdict(Counter)
    for level in ['unigrams_raw', 'bigrams_raw', 'trigrams_raw']:
        for emo, ctr in results[level].items():
            all_raw[emo].update(ctr)

    cols = sorted({w for emo, counter in all_raw.items() for w, c in counter.items() if c > 6}) #Nastavení nejnižšího počtu výskytu
    pos = ['positive', 'joy', 'anticipation', 'surprise', 'trust']
    neg = ['negative', 'anger', 'sadness', 'disgust', 'fear']
    rows = [e for e in pos + neg if e in all_raw]
    df = pd.DataFrame(0, index=rows, columns=cols)
    for emo in rows:
        counter = all_raw.get(emo, Counter())
        for w in cols:
            df.at[emo, w] = counter.get(w, 0)

    # Styling a zápis do HTML
    def highlight(df):
        sty = pd.DataFrame('', index=df.index, columns=df.columns)
        maxv = df.values.max() or 1
        for emo in df.index:
            color = '0,128,0' if emo in pos else '255,0,0'
            for w in df.columns:
                v = df.at[emo, w]
                if v > 0:
                    alpha = v / maxv
                    sty.at[emo, w] = f'background-color: rgba({color},{alpha});'
        return sty

    styled = df.style.apply(highlight, axis=None)
    html = styled.to_html()
    with open('emocni_matice.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Vytvořena tabulka emocí ze všech n-gramů (uloženo jako 'emocni_matice.html')")
