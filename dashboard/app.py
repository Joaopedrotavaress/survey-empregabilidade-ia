"""Dashboard do survey: empregabilidade de devs após a IA generativa.

Executar:  streamlit run dashboard/app.py
Fonte dos dados: SHEET_URL (planilha de respostas do Google Forms) ou a exportação em dados/.
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
h2, h3 {letter-spacing: -0.01em;}
</style>
""", unsafe_allow_html=True)

PASTA = Path(__file__).resolve().parent
FUSO = ZoneInfo("America/Sao_Paulo")
ATUALIZA_SEG = 60


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


# ---------------------------------------------------------------- filtros (barra lateral)

def filtros(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    st.sidebar.header("Filtros por segmento")
    ativos = []
    opcoes = [
        ("grupo_mercado", "Situação no mercado", None),
        ("faixa_exp", "Tempo de experiência", [f[2] for f in C.FAIXAS_EXP]),
        ("senioridade", "Senioridade", C.SENIORIDADE_ORDEM),
        ("porte", "Porte da empresa", C.PORTE_ORDEM),
        ("area", "Área de atuação", None),
        ("antes2022", "Já atuava antes de dez/2022", None),
        ("regiao", "Região", None),
    ]
    for col, rotulo, ordem in opcoes:
        valores = list(df[col].dropna().unique())
        if ordem:
            valores = [o for o in ordem if o in valores] + [v for v in valores if v not in ordem]
        else:
            valores = sorted(valores)
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


def pct(v: float) -> str:
    return "—" if pd.isna(v) else f"{v * 100:.0f}%"


def fmt_p(p: float) -> str:
    if pd.isna(p):
        return "—"
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def num(v: float, casas: int = 2) -> str:
    return "—" if pd.isna(v) else f"{v:.{casas}f}".replace(".", ",")


# ---------------------------------------------------------------- testes das questões de pesquisa

EMP = "Empregabilidade percebida hoje"
IAI = "Atribuição das mudanças à IA"
PIORA = "Piora do mercado desde 2023"

QPS = {
    "QP1": "Como os desenvolvedores percebem a própria empregabilidade hoje?",
    "QP2": "A empregabilidade percebida mudou desde a popularização da IA generativa (2023 em diante)?",
    "QP3": "A empregabilidade percebida e a mudança diferem entre quem está dentro e fora do mercado?",
    "QP4": "A atribuição das mudanças à IA e o uso de IA estão associados à empregabilidade percebida?",
}


def rodar_testes(df: pd.DataFrame) -> list[E.Resultado]:
    r = [
        E.wilcoxon_vs_neutro(df[EMP], 3, "QP1", f"Índice de {EMP.lower()} vs. ponto neutro (3)"),
        E.wilcoxon_vs_neutro(df["emp_vs_antes_n"], 3, "QP2", "Empregabilidade hoje vs. antes de 2023 (3 = igual)"),
        E.wilcoxon_vs_neutro(df[PIORA], 3, "QP2", f"Índice de {PIORA.lower()} vs. ponto neutro (3)"),
        E.mann_whitney(df[EMP], df["grupo_mercado"], "QP3", f"{EMP}: dentro × fora do mercado"),
        E.mann_whitney(df["emp_vs_antes_n"], df["grupo_mercado"], "QP3",
                       "Mudança desde 2023: dentro × fora do mercado"),
        E.kruskal(df[EMP], df["senioridade"], "QP3", f"{EMP} entre níveis de senioridade"),
        E.spearman(df[IAI], df[EMP], "QP4", f"{IAI} × {EMP.lower()}"),
        E.spearman(df["uso_ia_n"], df[EMP], "QP4", f"Frequência de uso de IA × {EMP.lower()}"),
        E.spearman(df["prof_ia_n"], df[EMP], "QP4", f"Proficiência em IA × {EMP.lower()}"),
    ]
    E.holm(r)
    return r


def tabela_resultados(res: list[E.Resultado]) -> pd.DataFrame:
    return pd.DataFrame([{
        "QP": x.qp, "Hipótese testada": x.descricao, "Teste": x.teste, "n": x.n,
        "Estatística": num(x.estatistica), "p": fmt_p(x.p), "p (Holm)": fmt_p(x.p_holm),
        "Efeito": f"{x.efeito_nome} = {num(x.efeito)} ({x.efeito_mag})",
        "Significativo (Holm, α=0,05)": "—" if pd.isna(x.p_holm) else ("sim" if x.p_holm < C.ALFA else "não"),
        "Observação": x.aviso,
    } for x in res])


def cartao_teste(x: E.Resultado):
    with st.container(border=True):
        st.markdown(f"**{x.descricao}**")
        c = st.columns(5)
        c[0].metric("Teste", x.teste.split(" (")[0], help=x.teste)
        c[1].metric("n", x.n)
        c[2].metric("p-valor", fmt_p(x.p))
        c[3].metric("p ajustado (Holm)", fmt_p(x.p_holm))
        c[4].metric(x.efeito_nome, num(x.efeito), x.efeito_mag, delta_color="off")
        if "grupos" in x.extra:
            st.caption("Medianas: " + " · ".join(f"{g}: {num(m)} (n={n})" for g, (n, m) in x.extra["grupos"].items())
                       + ". Efeito positivo = primeiro grupo com valores maiores.")
        elif "mediana" in x.extra:
            st.caption(f"Mediana: {num(x.extra['mediana'])} · média: {num(x.extra['media'])}")
        if not pd.isna(x.p_holm):
            veredito = ("diferença/associação **significativa**" if x.p_holm < C.ALFA
                        else "**sem evidência** suficiente para rejeitar H0")
            st.caption(f"Com correção de Holm (α = 0,05): {veredito}." + (f" ⚠️ {x.aviso}" if x.aviso else ""))
        elif x.aviso:
            st.caption(f"⚠️ {x.aviso}")


def cartao_proporcao(rotulo: str, serie: pd.Series, condicao):
    p, e, n = E.proporcao(serie, condicao)
    with st.container(border=True):
        st.metric(rotulo, pct(p), help="Margem de erro de 95%: 1,96·√(p(1−p)/n)")
        if n:
            st.caption(f"Margem de erro ±{e * 100:.0f} p.p. (IC 95%: {max(0, p - e) * 100:.0f}% a "
                       f"{min(1, p + e) * 100:.0f}%) · n = {n}")


# ---------------------------------------------------------------- páginas

def pagina_perfil():
    st.markdown('<div class="hero"><h1>Empregabilidade de devs após a IA generativa</h1>'
                '<p>Survey pré-registrado · Medição e Experimentação em Engenharia de Software · PUC Minas · '
                f'dados lidos às {LIDO_EM:%H:%M} de {LIDO_EM:%d/%m}</p></div>', unsafe_allow_html=True)
    st.header("Perfil da amostra")
    recebidas, validas = len(TODOS), int(TODOS["valida"].sum())
    e_max = E.margem_erro(0.5, validas)
    c = st.columns(5)
    c[0].metric("Respostas recebidas", recebidas)
    c[1].metric("Descartadas", recebidas - validas)
    c[2].metric("Válidas", validas)
    c[3].metric("Meta do protocolo", 50, f"faltam {max(0, 50 - validas)}" if validas < 50 else "atingida",
                delta_color="inverse" if validas < 50 else "normal")
    c[4].metric("Margem de erro (pior caso)", f"±{e_max * 100:.1f} p.p.", help="p = 0,5; 95% de confiança")
    inicio, fim = TODOS["ts"].min(), TODOS["ts"].max()
    st.caption(f"Coleta: {inicio:%d/%m/%Y %H:%M} a {fim:%d/%m/%Y %H:%M}. "
               "Os números desta página usam todas as respostas, sem os filtros da barra lateral.")

    esq, dir_ = st.columns([1, 1])
    with esq:
        st.subheader("Descartes e motivos")
        st.caption("Cada resposta é contada uma vez, no primeiro critério em que falha (ordem abaixo).")
        ordem = [m for m, _ in D.MOTIVOS] + ["Resposta duplicada"]
        cont = TODOS["motivo_descarte"].value_counts()
        tab = pd.DataFrame({"Critério": ordem, "Descartadas": [int(cont.get(m, 0)) for m in ordem]})
        tab.loc[len(tab)] = ["= Válidas", validas]
        st.dataframe(tab, hide_index=True, width="stretch")
        alertas = D.alertas_qualidade(TODOS)
        if len(alertas):
            with st.expander(f"Alertas de qualidade em respostas válidas ({len(alertas)}): não descartadas"):
                st.caption("Inconsistências para o grupo decidir. Se alguma virar descarte, registre na página "
                           "de metodologia.")
                st.dataframe(alertas, hide_index=True, width="stretch")
    with dir_:
        st.subheader("Funil de limpeza")
        st.plotly_chart(G.funil_descartes(TODOS, [m for m, _ in D.MOTIVOS] + ["Resposta duplicada"]),
                        width="stretch")

    st.divider()
    aviso_filtro()
    st.subheader(f"Quem respondeu (n = {len(AMOSTRA)} válidas)")
    r = st.columns(3)
    with r[0]:
        st.markdown("**Dentro × fora do mercado**")
        st.plotly_chart(G.rosca(AMOSTRA["grupo_mercado"]), width="stretch", key="rosca_merc")
    with r[1]:
        st.markdown("**Já atuava antes de dez/2022**")
        st.plotly_chart(G.rosca(AMOSTRA["antes2022"], ["Sim", "Não"]), width="stretch", key="rosca_antes")
    with r[2]:
        st.markdown("**Empregabilidade comparada a antes de 2023**")
        st.plotly_chart(G.rosca(AMOSTRA["emp_vs_antes"], list(C.COMPARACAO)), width="stretch", key="rosca_cmp")
    graficos = [
        ("Situação atual", "situacao", None), ("Senioridade", "senioridade", C.SENIORIDADE_ORDEM),
        ("Tempo de experiência", "faixa_exp", [f[2] for f in C.FAIXAS_EXP]),
        ("Porte da empresa", "porte", C.PORTE_ORDEM), ("Área de atuação", "area", None),
        ("Faixa etária", "faixa_etaria", None), ("Formação", "formacao", None),
        ("Região", "regiao", None), ("Canal de divulgação", "canal_grupo", None),
        ("Desligado(a) em layoff desde 2023", "layoff", None),
        ("Já atuava antes de dez/2022", "antes2022", None),
        ("Uso de assistentes de IA", "uso_ia", list(C.USO_IA)),
    ]
    for i in range(0, len(graficos), 3):
        cols = st.columns(3)
        for col, (titulo, campo, ordem) in zip(cols, graficos[i:i + 3]):
            with col:
                st.markdown(f"**{titulo}**")
                faixa_etaria = sorted(AMOSTRA[campo].dropna().unique()) if campo == "faixa_etaria" else None
                st.plotly_chart(G.barras_contagem(AMOSTRA[campo], ordem or faixa_etaria),
                                width="stretch", key=f"perfil_{campo}")


def pagina_likert():
    st.title("Itens em escala Likert")
    aviso_filtro()
    st.caption("Discordância à esquerda, concordância à direita; o neutro fica dividido ao meio. "
               "Os percentuais nas pontas somam as duas opções de cada lado. "
               "Os itens marcados (inv.) aparecem com a resposta original; a inversão só é aplicada nos índices.")
    modo = st.segmented_control("Visualização", ["Todos os respondentes", "Comparar por segmento"],
                                default="Todos os respondentes")
    if modo == "Comparar por segmento":
        seg_rot = st.selectbox("Segmento", list(SEGMENTOS))
        seg, ordem = SEGMENTOS[seg_rot]
        for bloco, itens in C.BLOCOS_LIKERT.items():
            st.subheader(bloco)
            cols = st.columns(2)
            for i, item in enumerate(itens):
                with cols[i % 2]:
                    st.markdown(f"**{C.ROTULOS_ITENS[item]}**")
                    st.plotly_chart(G.likert_por_grupo(AMOSTRA, item, seg, ordem), width="stretch",
                                    key=f"lkg_{item}")
        return
    for bloco, itens in C.BLOCOS_LIKERT.items():
        st.subheader(bloco)
        st.plotly_chart(G.likert_divergente(AMOSTRA, itens), width="stretch", key=f"lk_{bloco}")
    st.subheader("Empregabilidade hoje comparada a antes de 2023")
    st.plotly_chart(G.barras_contagem(AMOSTRA["emp_vs_antes"], list(C.COMPARACAO)), width="stretch")


def pagina_qps():
    st.title("Questões de pesquisa")
    aviso_filtro()
    res = rodar_testes(AMOSTRA)
    st.caption("Testes não paramétricos porque as respostas são ordinais. Os índices dos construtos são a média "
               "dos itens (escala 1 a 5). A correção de Holm é aplicada sobre os "
               f"{sum(not np.isnan(r.p) for r in res)} testes desta página.")
    abas = st.tabs([f"{k}" for k in QPS] + ["Tabela com todos os testes"])

    with abas[0]:
        st.subheader(f"QP1 · {QPS['QP1']}")
        c = st.columns(3)
        with c[0]:
            cartao_proporcao("Percebem-se empregáveis (índice > 3)", AMOSTRA[EMP], lambda s: s > 3)
        with c[1]:
            cartao_proporcao("Conseguiriam emprego em pouco tempo (concorda)", AMOSTRA["emp1_n"], lambda s: s >= 4)
        with c[2]:
            cartao_proporcao("Acham que há muitas vagas para o perfil (concorda)", AMOSTRA["emp2_n"],
                             lambda s: s >= 4)
        cartao_teste(res[0])
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA.assign(_t="Todos"), EMP, "_t"), width="stretch")

    with abas[1]:
        st.subheader(f"QP2 · {QPS['QP2']}")
        sub = AMOSTRA[AMOSTRA["emp_vs_antes_n"].notna()]
        st.caption(f"Subamostra de quem já atuava ou buscava vaga antes de dez/2022 (n = {len(sub)}). "
                   "Só esse grupo vê as perguntas de comparação.")
        c = st.columns(3)
        with c[0]:
            cartao_proporcao("Empregabilidade pior ou muito pior", AMOSTRA["emp_vs_antes_n"], lambda s: s <= 2)
        with c[1]:
            cartao_proporcao("Empregabilidade melhor ou muito melhor", AMOSTRA["emp_vs_antes_n"], lambda s: s >= 4)
        with c[2]:
            cartao_proporcao("Concordam que diminuíram as vagas", AMOSTRA["cmp2_n"], lambda s: s >= 4)
        cartao_teste(res[1])
        cartao_teste(res[2])
        st.plotly_chart(G.barras_contagem(sub["emp_vs_antes"], list(C.COMPARACAO)), width="stretch")

    with abas[2]:
        st.subheader(f"QP3 · {QPS['QP3']}")
        st.caption("Dentro do mercado: CLT, PJ ou freelancer. Fora: desempregado(a) ou buscando o primeiro emprego.")
        cartao_teste(res[3])
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA, EMP, "grupo_mercado"), width="stretch")
        cartao_teste(res[4])
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA, "emp_vs_antes_n", "grupo_mercado"),
                        width="stretch", key="qp3b")
        cartao_teste(res[5])
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA, EMP, "senioridade", C.SENIORIDADE_ORDEM),
                        width="stretch", key="qp3c")

    with abas[3]:
        st.subheader(f"QP4 · {QPS['QP4']}")
        c = st.columns(2)
        with c[0]:
            cartao_proporcao("Atribuem as mudanças mais à IA (índice > 3)", AMOSTRA[IAI], lambda s: s > 3)
        with c[1]:
            cartao_proporcao("Usam IA diariamente ou mais", AMOSTRA["uso_ia_n"], lambda s: s >= 3)
        for i, (x, xlab) in zip((6, 7, 8), ((IAI, IAI), ("uso_ia_n", "Uso de IA (0 = nunca … 4 = várias vezes/dia)"),
                                          ("prof_ia_n", "Proficiência em IA (1 = básica … 4 = especialista)"))):
            cartao_teste(res[i])
            st.plotly_chart(G.dispersao(AMOSTRA, x, EMP, xlab, EMP), width="stretch", key=f"qp4_{i}")

    with abas[4]:
        st.markdown("**Tamanho de efeito de cada teste** (azul = significativo após Holm; cinza = não)")
        st.plotly_chart(G.floresta_efeitos(res), width="stretch")
        st.dataframe(tabela_resultados(res), hide_index=True, width="stretch")
        st.caption("Tamanho de efeito: r rank-bisserial e ρ de Spearman (|0,1| pequeno, |0,3| médio, |0,5| grande); "
                   "ε² do Kruskal-Wallis (0,01 pequeno, 0,08 médio, 0,26 grande).")


def pagina_confiabilidade():
    st.title("Confiabilidade dos construtos")
    aviso_filtro()
    st.caption("Alfa de Cronbach calculado com os casos completos de cada construto, depois de inverter os itens "
               "negativos. Intervalo de confiança de 95% por bootstrap (2.000 reamostragens). "
               "Referência: ≥ 0,7 aceitável; 0,6 a 0,7 questionável; < 0,6 fraco.")
    linhas = []
    for nome, cfg in C.CONSTRUTOS.items():
        itens = AMOSTRA[[i + "_n" for i in cfg["itens"]]]
        itens.columns = [C.ROTULOS_ITENS[i] for i in cfg["itens"]]
        r = E.cronbach(itens)
        linhas.append({"Construto": nome, "Itens": r["k"], "n (casos completos)": r["n"],
                       "Alfa de Cronbach": num(r["alfa"]),
                       "IC 95%": f"{num(r['ic'][0])} a {num(r['ic'][1])}",
                       "Leitura": E.leitura_alfa(r["alfa"]), "Interpretação do índice": cfg["leitura"]})
        with st.container(border=True):
            st.subheader(nome)
            c = st.columns(3)
            c[0].metric("Alfa de Cronbach", num(r["alfa"]), E.leitura_alfa(r["alfa"]), delta_color="off")
            c[1].metric("IC 95% (bootstrap)", f"{num(r['ic'][0])} a {num(r['ic'][1])}")
            c[2].metric("Casos completos", r["n"])
            st.plotly_chart(G.barra_alfa(r["alfa"], r["ic"]), width="stretch", key=f"alfa_{nome}")
            if len(r["itens"]):
                t = r["itens"].copy()
                for col in ("correlação item-total", "alfa se excluído"):
                    t[col] = t[col].map(num)
                st.dataframe(t, hide_index=True, width="stretch")
    st.subheader("Resumo")
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")


SEGMENTOS = {
    "Situação no mercado": ("grupo_mercado", None),
    "Tempo de experiência": ("faixa_exp", [f[2] for f in C.FAIXAS_EXP]),
    "Senioridade": ("senioridade", C.SENIORIDADE_ORDEM),
    "Porte da empresa": ("porte", C.PORTE_ORDEM),
    "Área de atuação": ("area", None),
    "Já atuava antes de dez/2022": ("antes2022", None),
    "Desligado(a) em layoff": ("layoff", None),
    "Faixa etária": ("faixa_etaria", None),
    "Formação": ("formacao", None),
    "Uso de IA": ("uso_ia", list(C.USO_IA)),
    "Proficiência em IA": ("prof_ia", list(C.PROF_IA)),
}
VARIAVEIS_ORDINAIS = {
    "Índice: " + EMP: EMP, "Índice: " + IAI: IAI, "Índice: " + PIORA: PIORA,
    "Empregabilidade hoje vs. antes de 2023 (1 a 5)": "emp_vs_antes_n",
    **{C.ROTULOS_ITENS[i]: i + "_n" for b in C.BLOCOS_LIKERT.values() for i in b},
    "Candidaturas nos últimos 3 meses": "candidaturas",
    "Entrevistas nos últimos 3 meses": "entrevistas",
    "Meses buscando vaga": "meses_busca",
}


def pagina_explorar():
    st.title("Explorar cruzamentos")
    aviso_filtro()
    st.caption("Escolha um segmento e uma variável. O teste adequado à escala é escolhido sozinho: "
               "Kruskal-Wallis (ou Mann-Whitney com 2 grupos) para variáveis ordinais e numéricas; "
               "qui-quadrado (ou Fisher) para categóricas. Cruzamentos fora do plano de análise são exploratórios "
               "e não entram na correção de Holm.")
    c = st.columns([1, 1, 1])
    seg_rot = c[0].selectbox("Segmento (linhas)", list(SEGMENTOS))
    tipo = c[1].radio("Tipo de variável", ["Ordinal / numérica", "Categórica"], horizontal=True)
    seg, ordem_seg = SEGMENTOS[seg_rot]
    if tipo == "Ordinal / numérica":
        var_rot = c[2].selectbox("Variável", list(VARIAVEIS_ORDINAIS))
        var = VARIAVEIS_ORDINAIS[var_rot]
        grupos = AMOSTRA[[var, seg]].dropna()[seg].nunique()
        teste = E.mann_whitney if grupos == 2 else E.kruskal
        r = teste(AMOSTRA[var], AMOSTRA[seg], "Exploratório", f"{var_rot} por {seg_rot.lower()}")
        cartao_teste(r)
        maximo = AMOSTRA[var].max()
        faixa = (1, 5) if pd.isna(maximo) or maximo <= 5 else (0, float(maximo))
        st.plotly_chart(G.caixa_por_grupo(AMOSTRA, var, seg, ordem_seg, faixa), width="stretch")
        if var.endswith("_n") and var[:-2] in C.ROTULOS_ITENS:
            st.plotly_chart(G.likert_por_grupo(AMOSTRA, var[:-2], seg, ordem_seg), width="stretch")
    else:
        outras = {k: v for k, v in SEGMENTOS.items() if k != seg_rot}
        var_rot = c[2].selectbox("Variável (colunas)", list(outras))
        var, ordem_var = outras[var_rot]
        r = E.qui_quadrado(AMOSTRA[seg], AMOSTRA[var], "Exploratório", f"{seg_rot} × {var_rot.lower()}")
        cartao_teste(r)
        st.plotly_chart(G.mapa_calor(AMOSTRA[seg], AMOSTRA[var], ordem_seg, ordem_var), width="stretch")
    with st.expander("Ver as respostas usadas neste cruzamento"):
        st.dataframe(AMOSTRA[["id", "ts", seg, var]].dropna(), hide_index=True, width="stretch")


ARQ_CODIFICACAO = D.PASTA_DADOS / "codificacao_abertas.csv"


def pagina_abertas():
    st.title("Mudanças observadas e respostas abertas")
    aviso_filtro()
    st.subheader("Mudanças observadas em vagas e processos desde 2023 (múltipla escolha)")
    explodido = AMOSTRA["mudancas"].dropna().str.split(", ").explode()
    n = int(AMOSTRA["mudancas"].notna().sum())
    if n:
        cont = explodido.value_counts()
        tab = pd.DataFrame({"Mudança": cont.index, "Respostas": cont.values})
        tab["%"] = tab["Respostas"] / n
        tab["Margem de erro"] = [f"±{E.margem_erro(p, n) * 100:.0f} p.p." for p in tab["%"]]
        tab["%"] = tab["%"].map(pct)
        st.plotly_chart(G.barras_contagem(explodido), width="stretch")
        st.dataframe(tab, hide_index=True, width="stretch")
        st.caption(f"Percentual sobre {n} respondentes; cada pessoa pode marcar mais de uma opção.")

    st.subheader("Principal mudança que a IA trouxe (resposta aberta)")
    abertas = AMOSTRA.loc[AMOSTRA["aberta"].notna(), ["ts", "aberta"]].copy()
    abertas["carimbo"] = abertas["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    if ARQ_CODIFICACAO.exists():
        cod = pd.read_csv(ARQ_CODIFICACAO, dtype=str)
        abertas = abertas.merge(cod[["carimbo", "categoria"]], on="carimbo", how="left")
        codificadas = abertas["categoria"].notna().sum()
        st.caption(f"Codificação temática a partir de dados/codificacao_abertas.csv: "
                   f"{codificadas} de {len(abertas)} respostas codificadas.")
        if codificadas:
            st.plotly_chart(G.barras_contagem(abertas["categoria"].str.split(";").explode().str.strip()),
                            width="stretch")
    else:
        abertas["categoria"] = ""
        st.caption("Ainda não há codificação. Baixe o modelo abaixo, preencha a coluna 'categoria' "
                   "(duas pessoas codificam separadamente e depois resolvem as divergências) e salve como "
                   "dados/codificacao_abertas.csv. Várias categorias: separe com ';'.")
    st.dataframe(abertas[["carimbo", "aberta", "categoria"]].rename(columns={"aberta": "Resposta"}),
                 hide_index=True, width="stretch")
    st.download_button("Baixar modelo de codificação (CSV)",
                       abertas[["carimbo", "aberta", "categoria"]].to_csv(index=False).encode("utf-8-sig"),
                       "codificacao_abertas.csv", "text/csv")


def pagina_metodologia():
    st.title("Metodologia e desvios do protocolo")
    recebidas, validas = len(TODOS), int(TODOS["valida"].sum())
    canais = VALIDAS["canal_grupo"].value_counts()
    c = st.columns(4)
    c[0].metric("Período de coleta", f"{TODOS['ts'].min():%d/%m} a {TODOS['ts'].max():%d/%m/%Y}")
    c[1].metric("Válidas / meta", f"{validas} / 50")
    c[2].metric("Margem de erro (pior caso)", f"±{E.margem_erro(0.5, validas) * 100:.1f} p.p.")
    c[3].metric("Canal principal", canais.index[0] if len(canais) else "—",
                f"{canais.iloc[0] / canais.sum():.0%} das válidas" if len(canais) else None, delta_color="off")
    md = PASTA / "metodologia.md"
    st.markdown(md.read_text(encoding="utf-8") if md.exists() else "_Crie dashboard/metodologia.md._")

    with st.expander("Como os dados são tratados (gerado a partir do código)"):
        st.markdown(
            "**Leitura.** O dashboard lê a exportação bruta do Google Forms, sem edição manual. "
            f"A fonte atual é: {ORIGEM}.\n\n"
            "**Critérios de descarte, nesta ordem:** " + "; ".join(m for m, _ in D.MOTIVOS)
            + "; resposta duplicada (todas as respostas iguais às de outra resposta válida).\n\n"
            "**Codificação.** Likert: Discordo totalmente = 1 … Concordo totalmente = 5; 'Não sei avaliar' = "
            "ausente. Itens invertidos: " + ", ".join(
                C.ROTULOS_ITENS[i] for cfg in C.CONSTRUTOS.values() for i in cfg["inv"])
            + ". Índice de cada construto = média dos itens respondidos (exige ao menos metade).\n\n"
            "**Testes.** Wilcoxon de uma amostra (contra o ponto neutro), Mann-Whitney, Kruskal-Wallis e "
            "Spearman; efeitos por r rank-bisserial, ε² e ρ; correção de Holm; margem de erro "
            "1,96·√(p(1−p)/n) para cada proporção.")


paginas = [
    st.Page(pagina_perfil, title="Perfil da amostra", icon="👥", default=True),
    st.Page(pagina_likert, title="Escalas Likert", icon="📶", url_path="likert"),
    st.Page(pagina_qps, title="Questões de pesquisa", icon="🔬", url_path="qps"),
    st.Page(pagina_explorar, title="Explorar cruzamentos", icon="🧭", url_path="explorar"),
    st.Page(pagina_confiabilidade, title="Confiabilidade (alfa)", icon="🧮", url_path="confiabilidade"),
    st.Page(pagina_abertas, title="Mudanças e respostas abertas", icon="💬", url_path="abertas"),
    st.Page(pagina_metodologia, title="Metodologia e desvios", icon="📝", url_path="metodologia"),
]
st.navigation(paginas).run()
