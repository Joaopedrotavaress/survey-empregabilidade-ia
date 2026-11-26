"""Leitura dos dados brutos e limpeza (descartes com motivo)."""
from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

import config as C

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados"


# ---------------------------------------------------------------- leitura

def _sem_acento(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", str(txt))
    return "".join(ch for ch in txt if not unicodedata.combining(ch)).lower()


def url_csv_da_planilha(url: str) -> str:
    """Aceita o link normal do Google Sheets e devolve o link de exportação em CSV."""
    url = url.strip()
    if "output=csv" in url or "format=csv" in url:
        return url
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not m:
        return url
    gid = re.search(r"[#&?]gid=(\d+)", url)
    return (f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"
            + (f"&gid={gid.group(1)}" if gid else ""))


def origem_configurada() -> str | None:
    """Link da planilha: variável de ambiente SHEET_URL ou .streamlit/secrets.toml."""
    url = os.environ.get("SHEET_URL")
    if url:
        return url
    try:
        import streamlit as st
        return st.secrets.get("SHEET_URL")
    except Exception:
        return None


def arquivo_local() -> Path | None:
    for padrao in ("*.csv", "*.xlsx"):
        arquivos = sorted(PASTA_DADOS.glob(padrao), key=lambda p: p.stat().st_mtime, reverse=True)
        arquivos = [a for a in arquivos if not a.name.startswith(("codificacao", "~$"))]
        if arquivos:
            return arquivos[0]
    return None


def ler_bruto() -> tuple[pd.DataFrame, str]:
    """Lê a exportação bruta do formulário. Prioridade: planilha online > arquivo em dados/."""
    url = origem_configurada()
    if url:
        return pd.read_csv(url_csv_da_planilha(url), dtype=str), "Google Sheets (online)"
    arq = arquivo_local()
    if arq is None:
        raise FileNotFoundError(
            "Nenhuma fonte de dados: configure SHEET_URL ou coloque a exportação em dados/.")
    if arq.suffix == ".csv":
        return pd.read_csv(arq, dtype=str), f"arquivo local dados/{arq.name}"
    return pd.read_excel(arq, dtype=str), f"arquivo local dados/{arq.name}"


def renomear(bruto: pd.DataFrame) -> pd.DataFrame:
    normal = {col: _sem_acento(col) for col in bruto.columns}
    mapa = {}
    for chave, trecho in C.COLUNAS.items():
        achadas = [col for col, n in normal.items() if trecho in n and col not in mapa]
        if achadas:
            mapa[achadas[0]] = chave
    df = bruto.rename(columns=mapa)
    for chave in C.COLUNAS:
        if chave not in df.columns:
            df[chave] = np.nan
    return df[list(C.COLUNAS)].copy()


def _data_hora(serie: pd.Series) -> pd.Series:
    num = pd.to_numeric(serie, errors="coerce")
    if num.notna().all():  # número de série do Excel
        return pd.to_datetime(num, unit="D", origin="1899-12-30").dt.round("s")
    texto = serie.astype(str).str.strip()
    if texto.str.match(r"^\d{4}-\d{2}-\d{2}").all():  # ISO (lido do .xlsx)
        return pd.to_datetime(texto, format="ISO8601", errors="coerce").dt.round("s")
    return pd.to_datetime(texto, dayfirst=True, errors="coerce")  # dd/mm/aaaa hh:mm:ss (CSV do Sheets)


# ---------------------------------------------------------------- limpeza

def _limpa_texto(serie: pd.Series) -> pd.Series:
    s = serie.astype("string").str.strip()
    return s.mask(s.isin(["", "nan", "None"]))


def preparar(bruto: pd.DataFrame) -> pd.DataFrame:
    df = renomear(bruto)
    for col in df.columns:
        if col != "ts":
            df[col] = _limpa_texto(df[col])
    df["ts"] = _data_hora(df["ts"])
    df.insert(0, "id", range(1, len(df) + 1))

    for col in ("meses_busca", "candidaturas", "entrevistas", "exp_anos"):
        df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")

    # codificação numérica (sufixo _n)
    likert_cols = [c for b in C.BLOCOS_LIKERT.values() for c in b] + ["atencao"]
    for col in likert_cols:
        df[col + "_n"] = df[col].map(C.LIKERT)  # "Não sei avaliar" vira NaN
    for nome, cfg in C.CONSTRUTOS.items():
        for item in cfg["inv"]:
            df[item + "_n"] = 6 - df[item + "_n"]
    df["emp_vs_antes_n"] = df["emp_vs_antes"].map(C.COMPARACAO)
    df["uso_ia_n"] = df["uso_ia"].map(C.USO_IA)
    df["prof_ia_n"] = df["prof_ia"].map(C.PROF_IA)

    # índices dos construtos (média dos itens respondidos; exige ao menos metade)
    for nome, cfg in C.CONSTRUTOS.items():
        itens = df[[i + "_n" for i in cfg["itens"]]]
        minimo = int(np.ceil(len(cfg["itens"]) / 2))
        df[nome] = itens.mean(axis=1).where(itens.notna().sum(axis=1) >= minimo)

    # segmentos
    df["grupo_mercado"] = np.select(
        [df["situacao"].isin(C.DENTRO_MERCADO), df["situacao"].isin(C.FORA_MERCADO)],
        ["Dentro do mercado", "Fora do mercado"], default=None)
    faixas = pd.Series(pd.NA, index=df.index, dtype="object")
    for lo, hi, rot in C.FAIXAS_EXP:
        faixas[(df["exp_anos"] > lo) & (df["exp_anos"] <= hi)] = rot
    df["faixa_exp"] = faixas
    canais_conhecidos = {"Indicação de amigo(a) ou colega", "WhatsApp", "LinkedIn",
                         "Discord", "Telegram", "Reddit"}
    df["canal_grupo"] = df["canal"].where(df["canal"].isin(canais_conhecidos) | df["canal"].isna(), "Outro")
    df["data"] = df["ts"].dt.date
    return df


MOTIVOS = [
    ("Não aceitou o termo de consentimento",
     lambda d: d["consentimento"].isna() | ~d["consentimento"].fillna("").str.contains("aceito", case=False)
     | d["consentimento"].fillna("").str.contains("não aceito", case=False)),
    ("Menor de 18 anos", lambda d: d["maior18"].ne("Sim")),
    ("Colega da turma (regra da disciplina)", lambda d: d["turma"].eq("Sim")),
    ("Fora da população (não atua nem busca atuar como dev)",
     lambda d: d["situacao"].isna() | d["situacao"].fillna("").str.startswith(C.FORA_POPULACAO_PREFIXO)),
    ("Errou a pergunta de atenção", lambda d: d["atencao"].ne(C.RESPOSTA_ATENCAO)),
    ("Questionário principal incompleto",
     lambda d: d[[i + "_n" for i in C.CONSTRUTOS["Empregabilidade percebida hoje"]["itens"]]].isna().any(axis=1)),
]


def aplicar_descartes(df: pd.DataFrame) -> pd.DataFrame:
    """Marca cada resposta com o primeiro motivo de descarte que se aplica (ou 'Válida')."""
    df = df.copy()
    df["motivo_descarte"] = "Válida"
    for motivo, regra in MOTIVOS:
        alvo = (df["motivo_descarte"] == "Válida") & regra(df).fillna(True)
        df.loc[alvo, "motivo_descarte"] = motivo

    # duplicatas: mesmas respostas em todas as perguntas (exceto data/hora)
    resp = [c for c in C.COLUNAS if c != "ts"]
    validas = df["motivo_descarte"] == "Válida"
    dup = df[validas].duplicated(subset=resp, keep="first")
    df.loc[dup[dup].index, "motivo_descarte"] = "Resposta duplicada"
    df["valida"] = df["motivo_descarte"] == "Válida"
    return df


def alertas_qualidade(df: pd.DataFrame) -> pd.DataFrame:
    """Inconsistências que não geram descarte automático, mas são mostradas para decisão do grupo."""
    v = df[df["valida"]]
    linhas = []
    contraditorio = v["mudancas"].fillna("").str.contains("Não observei mudanças") & \
        v["mudancas"].fillna("").str.contains(",")
    for i in v.index[contraditorio]:
        linhas.append((v.at[i, "id"], "Marcou 'Não observei mudanças' junto com outras mudanças"))
    reto = v[[i + "_n" for i in ("emp1", "emp2", "emp3", "ia1", "ia2")]]
    for i in v.index[(reto.nunique(axis=1) == 1) & reto.notna().all(axis=1)]:
        linhas.append((v.at[i, "id"], "Mesma resposta em todos os itens Likert diretos (straight-lining)"))
    for i in v.index[v["entrevistas"] > v["candidaturas"]]:
        linhas.append((v.at[i, "id"], "Mais entrevistas do que candidaturas"))
    return pd.DataFrame(linhas, columns=["id", "alerta"])


def carregar() -> tuple[pd.DataFrame, str]:
    bruto, origem = ler_bruto()
    return aplicar_descartes(preparar(bruto)), origem
