#!/usr/bin/env python3
"""Atualiza data/noticias.json a partir das fontes aprovadas em fontes.json.
Guarda apenas título, resumo curto e ligação para a fonte original."""
import json, re, sys, html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

MAX_POR_FONTE, MAX_TOTAL, RESUMO = 5, 12, 200
ATOM = "{http://www.w3.org/2005/Atom}"

def limpar(t):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= RESUMO else t[:RESUMO].rsplit(" ", 1)[0] + "…"

def data(t):
    try:
        d = parsedate_to_datetime(t)
    except Exception:
        try:
            d = datetime.fromisoformat(t.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def ler(fonte):
    req = Request(fonte["feed"], headers={"User-Agent": "NEXA-bot/1.0"})
    raiz = ET.fromstring(urlopen(req, timeout=20).read())
    itens = raiz.findall(".//item") or raiz.findall(".//" + ATOM + "entry")
    saida = []
    for i in itens[:MAX_POR_FONTE]:
        def g(nome):
            e = i.find(nome)
            if e is None:
                e = i.find(ATOM + nome)
            return (e.text or "") if e is not None else ""
        link = g("link").strip()
        if not link:
            e = i.find(ATOM + "link")
            link = e.get("href", "") if e is not None else ""
        if not link.startswith(("http://", "https://")):
            continue
        d = data(g("pubDate") or g("updated") or g("published"))
        saida.append({
            "t": limpar(g("title")), "d": limpar(g("description") or g("summary")),
            "c": fonte.get("credibilidade", "a"), "f": fonte["nome"],
            "u": link, "data": d.isoformat(),
        })
    return saida

def main():
    fontes = json.load(open("fontes.json", encoding="utf-8"))["fontes"]
    todas = []
    for f in fontes:
        try:
            todas += ler(f)
        except Exception as e:
            print(f"Falhou {f['nome']}: {e}", file=sys.stderr)
    vistos, unicas = set(), []
    for n in sorted(todas, key=lambda n: n["data"], reverse=True):
        if n["u"] not in vistos and n["t"]:
            vistos.add(n["u"]); unicas.append(n)
    if not unicas:
        sys.exit("Nenhuma notícia obtida. O ficheiro anterior foi mantido.")
    out = {"atualizado": datetime.now(timezone.utc).isoformat(), "noticias": unicas[:MAX_TOTAL]}
    json.dump(out, open("data/noticias.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(out['noticias'])} notícias guardadas.")

main()
