"""Dashboard do survey: empregabilidade de devs após a IA generativa.

Executar:  streamlit run dashboard/app.py
Fonte dos dados: SHEET_URL (planilha de respostas do Google Forms) ou a exportação em dados/.
Questões, métricas, limpeza e testes seguem o protocolo pré-registrado (pasta protocolo/).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st

import config as C
import dados as D
import estatistica as E
import graficos as G

st.set_page_config(page_title="Survey · Empregabilidade de devs e IA", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stMetric"] {background: var(--secondary-background-color, #f3f2ef); border-radius: 0.7rem;
  padding: 0.8rem 1rem; border: 1px solid rgba(128,128,128,0.15);}
[data-testid="stMetricLabel"] p {font-size: 0.82rem; color: #6b6a65;}
[data-testid="stMetricValue"] {font-size: 1.7rem; font-weight: 650;}
.hero {padding: 1.2rem 1.4rem; border-radius: 0.9rem; margin-bottom: 1rem;
  background: linear-gradient(120deg, #104281 0%, #2a78d6 60%, #6da7ec 100%); color: white;}
.hero h1 {color: white; margin: 0; font-size: 1.9rem; padding: 0;}
.hero p {color: rgba(255,255,255,0.88); margin: 0.3rem 0 0 0;}
.hip {background: rgba(42,120,214,0.08); border-left: 4px solid #2a78d6; padding: 0.6rem 0.9rem;
  border-radius: 0.4rem; margin: 0.2rem 0 0.8rem 0;}
h2, h3 {letter-spacing: -0.01em;}
</style>
""", unsafe_allow_html=True)

PASTA = Path(__file__).resolve().parent
FUSO = ZoneInfo("America/Sao_Paulo")
ATUALIZA_SEG = 60
EPA, VPE, AIA, API = "EPA", "VPE", "AIA", "API"
NOME = {k: v["nome"] for k, v in C.CONSTRUTOS.items()}


# ---------------------------------------------------------------- dados (cache curto = atualização automática)

@st.cache_data(ttl=ATUALIZA_SEG, show_spinner="Lendo respostas…")
def carregar():
    df, origem = D.carregar()
    return df, origem, datetime.now(FUSO)


try:
    TODOS, ORIGEM, LIDO_EM = carregar()
except Exception as erro:  # noqa: BLE001
    st.error(f"Não foi possível ler os dados: {erro}")
    st.stop()

VALIDAS = TODOS[TODOS["valida"]]


# ---------------------------------------------------------------- formatação

def pct(v: float) -> str:
    return "—" if pd.isna(v) else f"{v * 100:.0f}%"


def fmt_p(p: float) -> str:
    if pd.isna(p):
        return "—"
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def num(v: float, casas: int = 2) -> str:
    return "—" if pd.isna(v) else f"{v:.{casas}f}".replace(".", ",")


def ordenar(valores, ordem):
    valores = list(valores)
    if ordem:
        return [o for o in ordem if o in valores] + sorted(v for v in valores if v not in ordem)
    return sorted(valores)


# ---------------------------------------------------------------- regra dos 5 (protocolo, seção 6)

OUTROS = f"Outros (menos de {C.MIN_SEGMENTO} cada)"


def agrupa_pequenos(serie: pd.Series) -> pd.Series:
    """Categorias com menos de 5 respostas viram 'Outros' (o dashboard não mostra segmentos menores)."""
    cont = serie.value_counts()
    pequenos = cont[cont < C.MIN_SEGMENTO].index
    return serie.where(~serie.isin(pequenos), OUTROS) if len(pequenos) else serie


def so_grupos_grandes(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, list[str]]:
    """Retira da comparação os grupos com menos de 5 respostas e devolve os nomes retirados."""
    cont = df[col].value_counts()
    pequenos = list(cont[cont < C.MIN_SEGMENTO].index)
    return df[~df[col].isin(pequenos)], pequenos


def aviso_pequenos(pequenos: list[str]):
    if pequenos:
        st.caption(f"Grupos com menos de {C.MIN_SEGMENTO} respostas não aparecem (regra de anonimização do "
                   f"protocolo): {', '.join(map(str, pequenos))}.")


# ---------------------------------------------------------------- filtros (barra lateral)

def filtros(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    st.sidebar.header("Filtros por segmento")
    ativos = []
    opcoes = [
        ("grupo_mercado", "Situação no mercado (M1)", C.M1_ORDEM),
        ("m3", "Senioridade (M3)", C.M3_ORDEM),
        ("faixa_exp", "Tempo de experiência", [f[2] for f in C.FAIXAS_EXP]),
        ("porte", "Porte da empresa", C.PORTE_ORDEM),
        ("area", "Área de atuação", None),
        ("antes2022", "Já atuava antes de dez/2022 (F1)", None),
        ("regiao", "Região", None),
    ]
    for col, rotulo, ordem in opcoes:
        valores = ordenar(df[col].dropna().unique(), ordem)
        escolha = st.sidebar.multiselect(rotulo, valores, key=f"f_{col}", placeholder="Todos")
        if escolha:
            df = df[df[col].isin(escolha)]
            ativos.append(f"{rotulo}: {', '.join(escolha)}")
    st.sidebar.divider()
    st.sidebar.caption(f"**Fonte:** {ORIGEM}  \n**Lido às:** {LIDO_EM:%d/%m/%Y %H:%M:%S}  \n"
                       f"Atualiza sozinho a cada {ATUALIZA_SEG} s ao interagir ou recarregar a página.")
    if st.sidebar.button("Atualizar agora", width="stretch"):
        carregar.clear()
        st.rerun()
    return df, ativos


AMOSTRA, FILTROS = filtros(VALIDAS)


def aviso_filtro():
    if FILTROS:
        st.info(f"Filtro ativo ({len(AMOSTRA)} de {len(VALIDAS)} respostas válidas): "
                + " · ".join(FILTROS) + ". Resultados de subgrupos são exploratórios.")
        if len(AMOSTRA) < C.MIN_SEGMENTO:
            st.warning(f"O filtro deixou menos de {C.MIN_SEGMENTO} respostas. Pelo protocolo, segmentos tão "
                       "pequenos não são mostrados. Afrouxe o filtro na barra lateral.")
            st.stop()


# ---------------------------------------------------------------- testes do plano de análise

QPS = {
    "QP1": ("A variação percebida da empregabilidade difere entre devs dentro e fora do mercado?",
            "H1: quem está fora percebe mais piora."),
    "QP2": ("A empregabilidade percebida e sua variação mudam com a senioridade e a experiência?",
            "H2: júniores percebem mais piora."),
    "QP3": ("Adoção e proficiência em IA se associam à empregabilidade percebida?",
            "H3: associação positiva."),
    "QP4": ("Que mudanças em vagas e processos seletivos os devs percebem, e quanto as atribuem à IA?",
            "Exploratória (sem hipótese)."),
}


def testes_confirmatorios(df: pd.DataFrame) -> list[E.Resultado]:
    """Família confirmatória do protocolo: 9 testes de QP1 a QP3, com Holm entre eles."""
    f1 = df[df["antes2022"] == "Sim"]
    r = [
        E.mann_whitney(df[EPA], df["grupo_mercado"], "QP1", "M4 (EPA): dentro × fora", C.M1_ORDEM),
        E.mann_whitney(f1[VPE], f1["grupo_mercado"], "QP1", "M5 (VPE): dentro × fora", C.M1_ORDEM),
        E.qui_quadrado(f1["g1_grupo"], f1["grupo_mercado"], "QP1", "G1 (pior/igual/melhor) × M1"),
        E.kruskal(df[EPA], df["m3"], "QP2", "M4 (EPA) entre senioridades (M3)", C.M3_ORDEM),
        E.kruskal(f1[VPE], f1["m3"], "QP2", "M5 (VPE) entre senioridades (M3)", C.M3_ORDEM),
        E.spearman(df["exp_anos"], df[EPA], "QP2", "M4 (EPA) × anos de experiência (M2)"),
        E.spearman(f1["exp_anos"], f1[VPE], "QP2", "M5 (VPE) × anos de experiência (M2)"),
        E.spearman(df[API], df[EPA], "QP3", "M8 (API) × M4 (EPA)"),
        E.spearman(f1[API], f1[VPE], "QP3", "M8 (API) × M5 (VPE)"),
    ]
    # direção esperada pela hipótese (sinal do efeito); None = ver medianas/tabela
    esperado = [+1, -1, None, None, None, +1, -1, +1, -1]
    for x, s in zip(r, esperado):
        x.extra["esperado"] = s
    E.holm(r)
    return r


def testes_exploratorios(df: pd.DataFrame) -> list[E.Resultado]:
    """Família exploratória (QP4): cada opção de S1 × M1 e M7 × M1, com Holm separado."""
    r = [E.qui_quadrado(df[f"s1_{i}"].map({1.0: "Marcou", 0.0: "Não marcou"}), df["grupo_mercado"], "QP4",
                        f"S1 · {op} × M1") for i, op in enumerate(C.OPCOES_S1)]
    r.append(E.mann_whitney(df[AIA], df["grupo_mercado"], "QP4", "M7 (AIA): dentro × fora", C.M1_ORDEM))
    E.holm(r)
    return r


def tabela_resultados(res: list[E.Resultado]) -> pd.DataFrame:
    linhas = []
    for x in res:
        efeito = f"{x.efeito_nome} = {num(x.efeito)} ({x.efeito_mag})"
        if "cliff" in x.extra:
            efeito += f"; δ de Cliff = {num(x.extra['cliff'])} ({x.extra['cliff_mag']})"
        linhas.append({
            "QP": x.qp, "Teste de": x.descricao, "Teste": x.teste, "n": x.n,
            "Estatística": num(x.estatistica), "p": fmt_p(x.p), "p (Holm)": fmt_p(x.p_holm), "Efeito": efeito,
            "Significativo (Holm, α=0,05)": "—" if pd.isna(x.p_holm) else ("sim" if x.p_holm < C.ALFA else "não"),
            "Direção vs. hipótese": direcao(x) or "—", "Observação": x.aviso,
        })
    return pd.DataFrame(linhas)


def direcao(x: E.Resultado) -> str:
    s = x.extra.get("esperado")
    if not s or pd.isna(x.efeito) or x.efeito == 0:
        return ""
    return "coerente" if np.sign(x.efeito) == s else "contrária"


def cartao_teste(x: E.Resultado):
    with st.container(border=True):
        st.markdown(f"**{x.descricao}**")
        c = st.columns(5)
        c[0].metric("Teste", x.teste.split(" (")[0], help=x.teste)
        c[1].metric("n", x.n)
        c[2].metric("p-valor", fmt_p(x.p))
        c[3].metric("p ajustado (Holm)", fmt_p(x.p_holm))
        c[4].metric(x.efeito_nome, num(x.efeito), x.efeito_mag, delta_color="off")
        notas = []
        if "grupos" in x.extra:
            notas.append("Medianas: " + " · ".join(f"{g}: {num(m)} (n={n})" for g, (n, m) in x.extra["grupos"].items()))
        if "cliff" in x.extra:
            notas.append(f"δ de Cliff = {num(x.extra['cliff'])} ({x.extra['cliff_mag']}); "
                         "efeito positivo = primeiro grupo com valores maiores")
        if direcao(x):
            notas.append(f"direção **{direcao(x)}** com a hipótese")
        if notas:
            st.caption(". ".join(notas) + ".")
        if not pd.isna(x.p_holm):
            veredito = ("diferença/associação **significativa**" if x.p_holm < C.ALFA
                        else "**sem evidência** suficiente para rejeitar H0")
            st.caption(f"Com correção de Holm (α = 0,05): {veredito}." + (f" ⚠️ {x.aviso}" if x.aviso else ""))
        elif x.aviso:
            st.caption(f"⚠️ {x.aviso}")
        if isinstance(x.extra.get("dunn"), pd.DataFrame) and len(x.extra["dunn"]):
            with st.expander("Pós-teste de Dunn (pares, Holm)"):
                t = x.extra["dunn"].copy()
                t["z"] = t["z"].map(num)
                t["p"] = t["p"].map(fmt_p)
                t["p (Holm)"] = t["p (Holm)"].map(fmt_p)
                st.dataframe(t, hide_index=True, width="stretch")
        if isinstance(x.extra.get("tabela"), pd.DataFrame):
            with st.expander("Tabela de contingência"):
                st.dataframe(x.extra["tabela"], width="stretch")


def cartao_proporcao(rotulo: str, serie: pd.Series, condicao):
    r = E.proporcao(serie, condicao)
    with st.container(border=True):
        st.metric(rotulo, pct(r["p"]), help="IC 95% de Wilson; margem de erro 1,96·√(p(1−p)/n)")
        if r["n"]:
            st.caption(f"{r['k']} de {r['n']} · IC 95% (Wilson): {pct(r['ic'][0])} a {pct(r['ic'][1])} · "
                       f"margem ±{r['e'] * 100:.0f} p.p.")


def hipotese(qp: str):
    pergunta, h = QPS[qp]
    st.subheader(f"{qp} · {pergunta}")
    st.markdown(f'<div class="hip">{h}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- páginas

def pagina_perfil():
    st.markdown('<div class="hero"><h1>Empregabilidade de devs após a IA generativa</h1>'
                '<p>Survey pré-registrado · Medição e Experimentação em Engenharia de Software · PUC Minas · '
                f'dados lidos às {LIDO_EM:%H:%M} de {LIDO_EM:%d/%m}</p></div>', unsafe_allow_html=True)
    st.header("Perfil da amostra")
    recebidas, validas = len(TODOS), len(VALIDAS)
    dentro = int((VALIDAS["grupo_mercado"] == "Dentro do mercado").sum())
    fora = int((VALIDAS["grupo_mercado"] == "Fora do mercado").sum())
    f1 = int((VALIDAS["antes2022"] == "Sim").sum())

    def meta(v, alvo):
        return ("atingida", "normal") if v >= alvo else (f"faltam {alvo - v}", "inverse")

    c = st.columns(4)
    c[0].metric("Respostas recebidas", recebidas)
    c[1].metric("Descartadas", recebidas - validas)
    d, cor = meta(validas, C.META_TOTAL)
    c[2].metric(f"Válidas (meta {C.META_TOTAL})", validas, d, delta_color=cor)
    c[3].metric("Margem de erro (pior caso)", f"±{E.margem_erro(0.5, validas) * 100:.1f} p.p.",
                help="p = 0,5; 95% de confiança")
    c = st.columns(4)
    d, cor = meta(dentro, C.META_DENTRO)
    c[0].metric(f"Dentro do mercado (meta {C.META_DENTRO})", dentro, d, delta_color=cor)
    d, cor = meta(fora, C.META_FORA)
    c[1].metric(f"Fora do mercado (meta {C.META_FORA})", fora, d, delta_color=cor)
    c[2].metric("Já atuavam antes de dez/2022 (F1 = Sim)", f1, help="Só esse grupo responde VPE e G1")
    c[3].metric("Coleta", f"{TODOS['ts'].min():%d/%m} a {TODOS['ts'].max():%d/%m}",
                f"{TODOS['ts'].max():%H:%M} última resposta", delta_color="off")

    with st.expander("Margem de erro por recorte (planejado × realizado)"):
        rec = [("Total", C.META_TOTAL, validas), ("Dentro", C.META_DENTRO, dentro),
               ("Fora", C.META_FORA, fora), ("Só F1 = Sim", 40, f1)]
        st.dataframe(pd.DataFrame([{
            "Recorte": r, "n planejado": p, "Margem planejada": f"±{E.margem_erro(0.5, p) * 100:.1f} p.p.",
            "n obtido": o, "Margem obtida": f"±{E.margem_erro(0.5, o) * 100:.1f} p.p." if o else "—",
        } for r, p, o in rec]), hide_index=True, width="stretch")
        st.caption("Fórmula e = 1,96·√(p(1−p)/n), pior caso p = 0,5. A amostra não é probabilística: "
                   "a margem cobre só o erro aleatório (protocolo, seção 2). O n planejado de F1 = Sim era uma estimativa.")

    esq, dir_ = st.columns([1, 1])
    with esq:
        st.subheader("Limpeza (D1 a D5)")
        st.caption("Ordem do protocolo. Cada resposta é contada uma vez, no primeiro critério em que falha.")
        cont = TODOS["motivo_descarte"].value_counts()
        tab = pd.DataFrame({"Critério": D.ORDEM_MOTIVOS,
                            "Descartadas": [int(cont.get(m, 0)) for m in D.ORDEM_MOTIVOS]})
        tab.loc[len(tab)] = ["= Válidas", validas]
        st.dataframe(tab, hide_index=True, width="stretch")
        alertas = D.alertas_qualidade(TODOS)
        if len(alertas):
            with st.expander(f"Alertas de qualidade em respostas válidas ({len(alertas)}): não descartadas"):
                st.caption("Inconsistências fora das regras D1 a D5, para o grupo avaliar. Se alguma virar "
                           "descarte, registre como desvio na página de metodologia.")
                st.dataframe(alertas, hide_index=True, width="stretch")
    with dir_:
        st.subheader("Funil de limpeza")
        st.plotly_chart(G.funil_descartes(TODOS, D.ORDEM_MOTIVOS), width="stretch")

    st.divider()
    aviso_filtro()
    st.subheader(f"Quem respondeu (n = {len(AMOSTRA)} válidas)")
    st.caption(f"Categorias com menos de {C.MIN_SEGMENTO} respostas aparecem juntas em \"{OUTROS}\" "
               "(regra de anonimização do protocolo).")
    r = st.columns(3)
    with r[0]:
        st.markdown("**Situação no mercado (M1)**")
        st.plotly_chart(G.rosca(AMOSTRA["grupo_mercado"], C.M1_ORDEM), width="stretch", key="rosca_merc")
    with r[1]:
        st.markdown("**Já atuava antes de dez/2022 (F1)**")
        st.plotly_chart(G.rosca(AMOSTRA["antes2022"], ["Sim", "Não"]), width="stretch", key="rosca_antes")
    with r[2]:
        st.markdown("**Empregabilidade comparada a antes de 2023 (G1)**")
        st.plotly_chart(G.rosca(AMOSTRA["g1_grupo"], ["Pior", "Igual", "Melhor"]), width="stretch",
                        key="rosca_cmp")
    graficos = [
        ("Situação atual (T3)", "situacao", None), ("Senioridade (M3)", "m3", C.M3_ORDEM),
        ("Tempo de experiência (M2)", "faixa_exp", [f[2] for f in C.FAIXAS_EXP]),
        ("Porte da empresa", "porte", C.PORTE_ORDEM), ("Área de atuação", "area", None),
        ("Faixa etária", "faixa_etaria", None), ("Formação", "formacao", None),
        ("Região", "regiao", None), ("Canal de divulgação (S3)", "canal_grupo", None),
        ("Desligado(a) em layoff desde 2023 (B4)", "layoff", None),
        ("Uso de assistentes de IA (API1)", "uso_ia", list(C.USO_IA)),
        ("Proficiência em IA (API2)", "prof_ia", list(C.PROF_IA)),
    ]
    for i in range(0, len(graficos), 3):
        cols = st.columns(3)
        for col, (titulo, campo, ordem) in zip(cols, graficos[i:i + 3]):
            with col:
                st.markdown(f"**{titulo}**")
                serie = agrupa_pequenos(AMOSTRA[campo])
                if campo == "faixa_etaria":
                    ordem = sorted(AMOSTRA[campo].dropna().unique())
                st.plotly_chart(G.barras_contagem(serie, (ordem or []) + [OUTROS] if ordem else None),
                                width="stretch", key=f"perfil_{campo}")


def pagina_likert():
    st.title("Itens em escala Likert")
    aviso_filtro()
    st.caption("Discordância à esquerda, concordância à direita; o neutro fica dividido ao meio. "
               "Os percentuais nas pontas somam as duas opções de cada lado. "
               "Itens (R) aparecem com a resposta original; a inversão só é aplicada nos escores.")
    modo = st.segmented_control("Visualização", ["Dentro × fora do mercado (M1)", "Todos os respondentes",
                                                 "Outro segmento"], default="Dentro × fora do mercado (M1)")
    if modo == "Todos os respondentes":
        for bloco, itens in C.BLOCOS_LIKERT.items():
            st.subheader(bloco)
            st.plotly_chart(G.likert_divergente(AMOSTRA, itens), width="stretch", key=f"lk_{bloco}")
        return
    if modo == "Outro segmento":
        seg_rot = st.selectbox("Segmento", [s for s in SEGMENTOS if s != "Situação no mercado (M1)"])
    else:
        seg_rot = "Situação no mercado (M1)"
    seg, ordem = SEGMENTOS[seg_rot]
    base, pequenos = so_grupos_grandes(AMOSTRA, seg)
    aviso_pequenos(pequenos)
    for bloco, itens in C.BLOCOS_LIKERT.items():
        st.subheader(bloco)
        cols = st.columns(2)
        for i, item in enumerate(itens):
            with cols[i % 2]:
                st.markdown(f"**{C.ROTULOS_ITENS[item]}**")
                st.plotly_chart(G.likert_por_grupo(base, item, seg, ordem), width="stretch", key=f"lkg_{item}")


def tabela_escores(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for sigla, cfg in C.CONSTRUTOS.items():
        linha = {"Métrica": f"{cfg['metrica']} · {cfg['nome']}", "Leitura": cfg["leitura"]}
        for rot, sub in [("Todos", df)] + [(g, df[df["grupo_mercado"] == g]) for g in C.M1_ORDEM]:
            r = E.resumo(sub[sigla])
            linha[rot] = (f"{num(r['mediana'])} [{num(r['q1'])}–{num(r['q3'])}] (n={r['n']})"
                          if r["n"] >= C.MIN_SEGMENTO else (f"n={r['n']} (< {C.MIN_SEGMENTO})" if r["n"] else "—"))
        linhas.append(linha)
    return pd.DataFrame(linhas)


def pagina_qps():
    st.title("Questões de pesquisa")
    aviso_filtro()
    conf = testes_confirmatorios(AMOSTRA)
    expl = testes_exploratorios(AMOSTRA)
    f1 = AMOSTRA[AMOSTRA["antes2022"] == "Sim"]
    st.caption("Plano de análise do protocolo: testes bilaterais, α = 0,05, não paramétricos ou de contagem. "
               "A família confirmatória (9 testes de QP1 a QP3) e a exploratória (QP4) recebem a correção de Holm "
               f"separadamente. VPE, G1 e M6 usam só quem respondeu F1 = Sim (n = {len(f1)}).")
    with st.expander("Escores por estrato: mediana [intervalo interquartil]", expanded=True):
        st.dataframe(tabela_escores(AMOSTRA), hide_index=True, width="stretch")
        st.caption("Escala de 1 a 5, média dos itens depois de inverter os (R). VPE exige 3 dos 4 itens "
                   "(\"Não sei avaliar\" conta como ausente).")
    abas = st.tabs(["QP1", "QP2", "QP3", "QP4 (exploratória)", "Todos os testes"])

    with abas[0]:
        hipotese("QP1")
        cartao_teste(conf[0])
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA, EPA, "grupo_mercado", C.M1_ORDEM, ylab=NOME[EPA]),
                        width="stretch", key="qp1a")
        cartao_teste(conf[1])
        st.plotly_chart(G.caixa_por_grupo(f1, VPE, "grupo_mercado", C.M1_ORDEM, ylab=NOME[VPE]),
                        width="stretch", key="qp1b")
        cartao_teste(conf[2])

        st.markdown("**M6 · Proporção que percebe piora (G1 = pior ou muito pior), por estrato**")
        c = st.columns(3)
        kn = {}
        for col, g in zip(c, C.M1_ORDEM):
            s = f1.loc[f1["grupo_mercado"] == g, "M6_piora"]
            r = E.proporcao(s, lambda v: v == 1)
            kn[g] = (r["k"], r["n"])
            with col:
                cartao_proporcao(g, s, lambda v: v == 1)
        (k1, n1), (k2, n2) = kn[C.M1_ORDEM[1]], kn[C.M1_ORDEM[0]]
        d, lo, hi = E.diferenca_proporcoes(k1, n1, k2, n2)
        with c[2]:
            with st.container(border=True):
                st.metric("Diferença (fora − dentro)", "—" if pd.isna(d) else f"{d * 100:+.0f} p.p.")
                if not pd.isna(d):
                    st.caption(f"IC 95% (Newcombe): {lo * 100:+.0f} a {hi * 100:+.0f} p.p.")

        fora = AMOSTRA[AMOSTRA["grupo_mercado"] == "Fora do mercado"]
        st.markdown("**M9 · Busca por vaga (B1 a B3, só quem está fora do mercado; descritiva)**")
        if len(fora) < C.MIN_SEGMENTO:
            st.info(f"Menos de {C.MIN_SEGMENTO} respostas de quem está fora do mercado com os filtros atuais.")
        else:
            tot_cand, tot_ent = fora["candidaturas"].sum(), fora["entrevistas"].sum()
            taxa = (fora["entrevistas"] / fora["candidaturas"].replace(0, np.nan)).dropna()
            rb, rc = E.resumo(fora["meses_busca"]), E.resumo(fora["candidaturas"])
            c = st.columns(4)
            c[0].metric("Respondentes", len(fora))
            c[1].metric("Meses buscando", num(rb["mediana"], 0), f"IIQ {num(rb['q1'], 0)}–{num(rb['q3'], 0)}",
                        delta_color="off")
            c[2].metric("Candidaturas em 3 meses", num(rc["mediana"], 0), f"IIQ {num(rc['q1'], 0)}–{num(rc['q3'], 0)}",
                        delta_color="off")
            c[3].metric("Entrevistas por candidatura", pct(tot_ent / tot_cand) if tot_cand else "—",
                        f"mediana individual {pct(taxa.median())}" if len(taxa) else None, delta_color="off",
                        help="Total de entrevistas dividido pelo total de candidaturas do grupo")

    with abas[1]:
        hipotese("QP2")
        st.caption("M3 em três grupos: até júnior (inclui estágio e quem ainda não trabalhou como dev), "
                   "pleno e sênior ou acima.")
        cartao_teste(conf[3])
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA, EPA, "m3", C.M3_ORDEM, ylab=NOME[EPA]), width="stretch",
                        key="qp2a")
        cartao_teste(conf[4])
        st.plotly_chart(G.caixa_por_grupo(f1, VPE, "m3", C.M3_ORDEM, ylab=NOME[VPE]), width="stretch", key="qp2b")
        c = st.columns(2)
        with c[0]:
            cartao_teste(conf[5])
            st.plotly_chart(G.dispersao(AMOSTRA, "exp_anos", EPA, "Anos de experiência (M2)", NOME[EPA]),
                            width="stretch", key="qp2c")
        with c[1]:
            cartao_teste(conf[6])
            st.plotly_chart(G.dispersao(f1, "exp_anos", VPE, "Anos de experiência (M2)", NOME[VPE]),
                            width="stretch", key="qp2d")

    with abas[2]:
        hipotese("QP3")
        st.caption("API = média de API1 (frequência de uso), API2 (proficiência) e API3 (entregar mais rápido), "
                   "todos na escala 1–5. Como VPE maior significa mais piora, a hipótese de associação positiva "
                   "com a empregabilidade corresponde a ρ > 0 com EPA e ρ < 0 com VPE.")
        c = st.columns(2)
        with c[0]:
            cartao_teste(conf[7])
            st.plotly_chart(G.dispersao(AMOSTRA, API, EPA, NOME[API], NOME[EPA]), width="stretch", key="qp3a")
        with c[1]:
            cartao_teste(conf[8])
            st.plotly_chart(G.dispersao(f1, API, VPE, NOME[API], NOME[VPE]), width="stretch", key="qp3b")

    with abas[3]:
        hipotese("QP4")
        n = int(AMOSTRA["mudancas"].notna().sum())
        st.markdown(f"**M10 · Proporção que relata cada mudança (S1), por estrato** · n = {n}")
        linhas = []
        for i, op in enumerate(C.OPCOES_S1):
            for g, sub in [("Todos", AMOSTRA)] + [(g, AMOSTRA[AMOSTRA["grupo_mercado"] == g]) for g in C.M1_ORDEM]:
                s = sub[f"s1_{i}"].dropna()
                if len(s) < C.MIN_SEGMENTO:
                    continue
                k, m = int(s.sum()), len(s)
                lo, hi = E.wilson(k, m)
                linhas.append({"categoria": op, "grupo": g, "p": k / m, "lo": lo, "hi": hi, "k": k, "n": m})
        tab = pd.DataFrame(linhas)
        if len(tab):
            ordem_ops = (tab[tab["grupo"] == "Todos"].sort_values("p", ascending=False)["categoria"].tolist())
            tab["categoria"] = pd.Categorical(tab["categoria"], ordem_ops, ordered=True)
            tab = tab.sort_values("categoria")
            grupos = [g for g in C.M1_ORDEM if g in set(tab["grupo"])]
            st.plotly_chart(G.proporcoes_por_grupo(tab[tab["grupo"] != "Todos"], grupos), width="stretch")
            larga = tab.assign(v=[f"{pct(p)} ({pct(lo)}–{pct(hi)})" for p, lo, hi in zip(tab.p, tab.lo, tab.hi)]) \
                .pivot(index="categoria", columns="grupo", values="v").reset_index()
            larga = larga[["categoria"] + [g for g in ["Todos"] + C.M1_ORDEM if g in larga.columns]]
            st.dataframe(larga.rename(columns={"categoria": "Mudança"}), hide_index=True, width="stretch")
            st.caption("Percentual (IC 95% de Wilson). Cada pessoa pode marcar mais de uma opção.")
        st.markdown("**Cada opção de S1 × M1 e M7 (AIA) × M1** · família exploratória, Holm próprio")
        st.dataframe(tabela_resultados(expl).drop(columns=["Direção vs. hipótese"]), hide_index=True,
                     width="stretch")
        cartao_teste(expl[-1])
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA, AIA, "grupo_mercado", C.M1_ORDEM, ylab=NOME[AIA]),
                        width="stretch", key="qp4a")
        st.caption("M11 (temas das respostas abertas) está na página Respostas abertas.")

    with abas[4]:
        st.markdown("**Família confirmatória (QP1 a QP3)** · azul = significativo após Holm; cinza = não")
        st.plotly_chart(G.floresta_efeitos(conf), width="stretch", key="fl_conf")
        st.dataframe(tabela_resultados(conf), hide_index=True, width="stretch")
        st.markdown("**Família exploratória (QP4)**")
        st.plotly_chart(G.floresta_efeitos(expl), width="stretch", key="fl_expl")
        st.dataframe(tabela_resultados(expl).drop(columns=["Direção vs. hipótese"]), hide_index=True,
                     width="stretch")
        st.caption("Magnitudes (protocolo): r, ρ, φ e V em 0,1 / 0,3 / 0,5; ε² em 0,01 / 0,06 / 0,14; "
                   "δ de Cliff em 0,147 / 0,33 / 0,474 (Romano et al., 2006). Fisher é usado quando alguma "
                   "frequência esperada é menor que 5 (Monte Carlo para tabelas maiores que 2×2).")


def pagina_confiabilidade():
    st.title("Confiabilidade dos construtos")
    aviso_filtro()
    st.caption(f"Alfa de Cronbach por construto, com os casos completos e os itens (R) invertidos. Meta do "
               f"protocolo: α ≥ {num(C.META_ALFA)}. API usa o alfa padronizado (itens em escalas diferentes). "
               "IC 95% por bootstrap (2.000 reamostragens).")
    linhas = []
    for sigla, cfg in C.CONSTRUTOS.items():
        itens = AMOSTRA[[i + "_n" for i in cfg["itens"]]]
        itens.columns = [C.ROTULOS_ITENS[i] for i in cfg["itens"]]
        r = E.cronbach(itens, padronizado=cfg["padronizado"])
        linhas.append({"Construto": cfg["nome"], "Métrica": cfg["metrica"], "Itens": r["k"],
                       "n (casos completos)": r["n"], "Alfa": num(r["alfa"]),
                       "IC 95%": f"{num(r['ic'][0])} a {num(r['ic'][1])}",
                       "Meta (≥ 0,70)": "atingida" if r["alfa"] >= C.META_ALFA else "abaixo"})
        with st.container(border=True):
            st.subheader(f"{cfg['nome']}" + (" · alfa padronizado" if cfg["padronizado"] else ""))
            c = st.columns(3)
            c[0].metric("Alfa de Cronbach", num(r["alfa"]), E.leitura_alfa(r["alfa"]), delta_color="off")
            c[1].metric("IC 95% (bootstrap)", f"{num(r['ic'][0])} a {num(r['ic'][1])}")
            c[2].metric("Casos completos", r["n"])
            st.plotly_chart(G.barra_alfa(r["alfa"], r["ic"]), width="stretch", key=f"alfa_{sigla}")
            if len(r["itens"]):
                t = r["itens"].copy()
                if r["alfa"] < C.META_ALFA and r["k"] > 2:
                    pior = t.loc[t["correlação item-total"].idxmin()]
                    st.warning(f"Abaixo da meta. O protocolo permite retirar o item com menor correlação "
                               f"item-total ({pior['item']}); sem ele, α = {num(pior['alfa se excluído'])}. "
                               "Se o grupo retirar o item, registre como desvio na página de metodologia.")
                for col in ("correlação item-total", "alfa se excluído"):
                    t[col] = t[col].map(num)
                st.dataframe(t, hide_index=True, width="stretch")
    st.subheader("Resumo")
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")


SEGMENTOS = {
    "Situação no mercado (M1)": ("grupo_mercado", C.M1_ORDEM),
    "Senioridade (M3)": ("m3", C.M3_ORDEM),
    "Tempo de experiência": ("faixa_exp", [f[2] for f in C.FAIXAS_EXP]),
    "Porte da empresa": ("porte", C.PORTE_ORDEM),
    "Área de atuação": ("area", None),
    "Já atuava antes de dez/2022 (F1)": ("antes2022", None),
    "Desligado(a) em layoff (B4)": ("layoff", None),
    "Faixa etária": ("faixa_etaria", None),
    "Formação": ("formacao", None),
    "Canal de divulgação (S3)": ("canal_grupo", None),
    "Uso de IA (API1)": ("uso_ia", list(C.USO_IA)),
    "Proficiência em IA (API2)": ("prof_ia", list(C.PROF_IA)),
}
VARIAVEIS_ORDINAIS = {
    **{f"{cfg['metrica']} · {cfg['nome']}": s for s, cfg in C.CONSTRUTOS.items()},
    "G1 · Empregabilidade hoje vs. antes de 2023 (1 a 5)": "emp_vs_antes_n",
    **{C.ROTULOS_ITENS[i]: i + "_n" for i in C.ITENS_LIKERT},
    "B1 · Meses buscando vaga": "meses_busca",
    "B2 · Candidaturas nos últimos 3 meses": "candidaturas",
    "B3 · Entrevistas nos últimos 3 meses": "entrevistas",
}


def pagina_explorar():
    st.title("Explorar cruzamentos")
    aviso_filtro()
    st.caption("Análises fora do plano, rotuladas como exploratórias (protocolo, seção 5): não entram nas famílias "
               "de Holm. O teste é escolhido pela escala: Mann-Whitney (2 grupos) ou Kruskal-Wallis para variáveis "
               "ordinais e numéricas; qui-quadrado ou Fisher para categóricas.")
    c = st.columns([1, 1, 1])
    seg_rot = c[0].selectbox("Segmento (linhas)", list(SEGMENTOS))
    tipo = c[1].radio("Tipo de variável", ["Ordinal / numérica", "Categórica"], horizontal=True)
    seg, ordem_seg = SEGMENTOS[seg_rot]
    base, pequenos = so_grupos_grandes(AMOSTRA, seg)
    if tipo == "Ordinal / numérica":
        var_rot = c[2].selectbox("Variável", list(VARIAVEIS_ORDINAIS))
        var = VARIAVEIS_ORDINAIS[var_rot]
        base, pequenos = so_grupos_grandes(AMOSTRA[AMOSTRA[var].notna()], seg)
        aviso_pequenos(pequenos)
        grupos = base[seg].dropna().nunique()
        if grupos < 2:
            st.info("É preciso ao menos dois grupos com 5 ou mais respostas para comparar.")
            return
        teste = E.mann_whitney if grupos == 2 else E.kruskal
        cartao_teste(teste(base[var], base[seg], "Exploratório", f"{var_rot} por {seg_rot.lower()}", ordem_seg))
        maximo = base[var].max()
        faixa = (1, 5) if pd.isna(maximo) or maximo <= 5 else (0, float(maximo))
        st.plotly_chart(G.caixa_por_grupo(base, var, seg, ordem_seg, faixa, ylab=var_rot), width="stretch")
        if var.endswith("_n") and var[:-2] in C.ROTULOS_ITENS and var[:-2] in C.ITENS_LIKERT:
            st.plotly_chart(G.likert_por_grupo(base, var[:-2], seg, ordem_seg), width="stretch")
    else:
        aviso_pequenos(pequenos)
        outras = {k: v for k, v in SEGMENTOS.items() if k != seg_rot}
        var_rot = c[2].selectbox("Variável (colunas)", list(outras))
        var, ordem_var = outras[var_rot]
        coluna = agrupa_pequenos(base[var])
        cartao_teste(E.qui_quadrado(base[seg], coluna, "Exploratório", f"{seg_rot} × {var_rot.lower()}"))
        st.plotly_chart(G.mapa_calor(base[seg], coluna, ordem_seg, (ordem_var or []) + [OUTROS]), width="stretch")


ARQ_CODIFICACAO = D.PASTA_DADOS / "codificacao_abertas.csv"


def pagina_abertas():
    st.title("Respostas abertas (S2 → M11)")
    aviso_filtro()
    st.caption("Análise temática (Braun e Clarke, 2006): dois integrantes criam o livro de códigos com 20% das "
               "respostas e codificam outros 20% de forma independente (meta: kappa de Cohen ≥ 0,60); um terceiro "
               "resolve divergências e o restante é codificado. Nomes de pessoas ou empresas não são exibidos.")
    abertas = AMOSTRA.loc[AMOSTRA["aberta"].notna(), ["ts", "grupo_mercado", "aberta"]].copy()
    abertas["carimbo"] = abertas["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    c = st.columns(3)
    c[0].metric("Respostas abertas", len(abertas))
    c[1].metric("Taxa de preenchimento", pct(len(abertas) / len(AMOSTRA)) if len(AMOSTRA) else "—")

    if ARQ_CODIFICACAO.exists():
        cod = pd.read_csv(ARQ_CODIFICACAO, dtype=str).fillna("")
        cols = [k for k in ("codificador_1", "codificador_2", "categoria_final", "categoria") if k in cod.columns]
        abertas = abertas.merge(cod[["carimbo"] + cols], on="carimbo", how="left")
        final = pd.Series("", index=abertas.index)
        for k in ("codificador_1", "categoria", "categoria_final"):  # a última preenchida prevalece
            if k in abertas.columns:
                final = abertas[k].where(abertas[k].fillna("").str.strip() != "", final)
        abertas["tema"] = final.replace("", pd.NA)
        if {"codificador_1", "codificador_2"} <= set(abertas.columns):
            principal = lambda s: s.fillna("").str.split(";").str[0].str.strip().replace("", pd.NA)  # noqa: E731
            kappa, n_k = E.kappa_cohen(principal(abertas["codificador_1"]), principal(abertas["codificador_2"]))
            c[2].metric("Kappa de Cohen (meta ≥ 0,60)", num(kappa), f"{n_k} respostas codificadas por ambos",
                        delta_color="off")
        temas = abertas.dropna(subset=["tema"]).assign(tema=lambda d: d["tema"].str.split(";")).explode("tema")
        temas["tema"] = temas["tema"].str.strip()
        st.caption(f"Codificação lida de dados/codificacao_abertas.csv: {abertas['tema'].notna().sum()} de "
                   f"{len(abertas)} respostas com tema.")
        if len(temas):
            linhas = []
            for g in C.M1_ORDEM:
                n_g = int((abertas["tema"].notna() & (abertas["grupo_mercado"] == g)).sum())
                if n_g < C.MIN_SEGMENTO:
                    continue
                for t, k in temas[temas["grupo_mercado"] == g]["tema"].value_counts().items():
                    lo, hi = E.wilson(k, n_g)
                    linhas.append({"categoria": t, "grupo": g, "p": k / n_g, "lo": lo, "hi": hi, "k": k, "n": n_g})
            st.markdown("**M11 · Frequência dos temas por estrato**")
            if linhas:
                tab = pd.DataFrame(linhas)
                st.plotly_chart(G.proporcoes_por_grupo(tab, [g for g in C.M1_ORDEM if g in set(tab["grupo"])]),
                                width="stretch")
            else:
                st.plotly_chart(G.barras_contagem(temas["tema"]), width="stretch")
    else:
        abertas["tema"] = pd.NA
        st.info("Codificação ainda não feita. Baixe o modelo abaixo, preencha codificador_1 e codificador_2 "
                "(e categoria_final depois de resolver as divergências) e salve como dados/codificacao_abertas.csv. "
                "Vários temas na mesma resposta: separe com ';'.")
    st.dataframe(abertas[["carimbo", "grupo_mercado", "aberta", "tema"]]
                 .rename(columns={"grupo_mercado": "Estrato", "aberta": "Resposta", "tema": "Tema"}),
                 hide_index=True, width="stretch")
    modelo = abertas[["carimbo", "grupo_mercado", "aberta"]].rename(
        columns={"grupo_mercado": "estrato", "aberta": "resposta"}).assign(
        codificador_1="", codificador_2="", categoria_final="")
    st.download_button("Baixar modelo de codificação (CSV)", modelo.to_csv(index=False).encode("utf-8-sig"),
                       "codificacao_abertas.csv", "text/csv")


def pagina_metodologia():
    st.title("Metodologia e desvios do protocolo")
    validas = len(VALIDAS)
    dentro = int((VALIDAS["grupo_mercado"] == "Dentro do mercado").sum())
    fora = int((VALIDAS["grupo_mercado"] == "Fora do mercado").sum())
    canais = VALIDAS["canal_grupo"].value_counts()
    inicio, fim = TODOS["ts"].min(), TODOS["ts"].max()
    ini_prev, fim_prev = pd.Timestamp(C.INICIO_PREVISTO), pd.Timestamp(C.FIM_PREVISTO)

    st.subheader("Metas do protocolo × realizado")
    top2 = canais.head(2)
    metas = pd.DataFrame([
        {"Item": "Respostas válidas", "Planejado": f"≥ {C.META_TOTAL}", "Realizado": validas,
         "Situação": "ok" if validas >= C.META_TOTAL else "abaixo"},
        {"Item": "Estrato dentro do mercado", "Planejado": f"≥ {C.META_DENTRO}", "Realizado": dentro,
         "Situação": "ok" if dentro >= C.META_DENTRO else "abaixo"},
        {"Item": "Estrato fora do mercado", "Planejado": f"≥ {C.META_FORA} (40%)",
         "Realizado": f"{fora} ({fora / validas:.0%})" if validas else fora,
         "Situação": "ok" if fora >= C.META_FORA else "abaixo"},
        {"Item": "Início da coleta", "Planejado": f"{ini_prev:%d/%m/%Y}", "Realizado": f"{inicio:%d/%m/%Y %H:%M}",
         "Situação": "ok" if inicio.normalize() <= ini_prev else f"{(inicio.normalize() - ini_prev).days} dias depois"},
        {"Item": "Encerramento da coleta", "Planejado": f"{fim_prev:%d/%m/%Y %H:%M}",
         "Realizado": f"última resposta em {fim:%d/%m/%Y %H:%M}",
         "Situação": "em andamento" if fim < fim_prev else "encerrada"},
        {"Item": "Canais", "Planejado": "LinkedIn, Discord, Telegram, WhatsApp, Reddit",
         "Realizado": " · ".join(f"{k} {v / canais.sum():.0%}" for k, v in top2.items()),
         "Situação": f"{top2.sum() / canais.sum():.0%} em 2 canais" if len(canais) else "—"},
    ])
    st.dataframe(metas.astype(str), hide_index=True, width="stretch")

    md = PASTA / "metodologia.md"
    st.markdown(md.read_text(encoding="utf-8") if md.exists() else "_Crie dashboard/metodologia.md._")

    with st.expander("Como os dados são tratados (gerado a partir do código)"):
        st.markdown(
            "**Leitura.** O dashboard lê a exportação bruta do Google Forms. A única alteração antes da análise é "
            f"retirar textos com nomes de pessoas ({sum(len(v) for v in C.TEXTOS_RETIRADOS.values())} campos, em "
            f"{len(C.TEXTOS_RETIRADOS)} respostas que continuam na amostra). Fonte atual: {ORIGEM}.\n\n"
            "**Limpeza, nesta ordem:** " + "; ".join(D.ORDEM_MOTIVOS)
            + f" (respostas idênticas enviadas com até {C.JANELA_DUPLICATA_MIN} min de diferença).\n\n"
            "**Codificação.** Likert: Discordo totalmente = 1 … Concordo totalmente = 5; \"Não sei avaliar\" = "
            "ausente. API1 e API2 vão para 1–5. Itens (R) invertidos (6 − x): "
            + ", ".join(C.ROTULOS_ITENS[i].split(" · ")[0] for cfg in C.CONSTRUTOS.values() for i in cfg["inv"])
            + ". Escores = média dos itens; VPE exige 3 dos 4. M3 = até júnior / pleno / sênior ou acima.\n\n"
            "**Testes.** Mann-Whitney (r = Z/√N e δ de Cliff), Kruskal-Wallis + Dunn (ε²), Spearman (ρ), "
            "qui-quadrado ou Fisher (V de Cramér ou φ); IC 95% de Wilson para proporções e de Newcombe para a "
            "diferença; Holm separado para a família confirmatória (QP1 a QP3) e a exploratória (QP4). "
            f"Segmentos com menos de {C.MIN_SEGMENTO} respostas não são exibidos.")


paginas = [
    st.Page(pagina_perfil, title="Perfil da amostra", icon="👥", default=True),
    st.Page(pagina_qps, title="Questões de pesquisa", icon="🔬", url_path="qps"),
    st.Page(pagina_likert, title="Escalas Likert", icon="📶", url_path="likert"),
    st.Page(pagina_confiabilidade, title="Confiabilidade (alfa)", icon="🧮", url_path="confiabilidade"),
    st.Page(pagina_abertas, title="Respostas abertas", icon="💬", url_path="abertas"),
    st.Page(pagina_explorar, title="Explorar cruzamentos", icon="🧭", url_path="explorar"),
    st.Page(pagina_metodologia, title="Metodologia e desvios", icon="📝", url_path="metodologia"),
]
st.navigation(paginas).run()
