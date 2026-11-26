"""Gráficos (Plotly). Paleta: divergente vermelho↔azul com cinza neutro; categórica em ordem fixa."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import config as C

CORES_LIKERT = {
    "Discordo totalmente": "#c93636",
    "Discordo parcialmente": "#f08f8e",
    "Nem concordo nem discordo": "#c9c8c2",
    "Concordo parcialmente": "#86b6ef",
    "Concordo totalmente": "#2a78d6",
}
CATEGORICA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
PRINCIPAL = CATEGORICA[0]
FONTE = dict(family="Inter, Segoe UI, sans-serif", size=13)


def _layout(fig: go.Figure, altura: int, **kw) -> go.Figure:
    fig.update_layout(height=altura, margin=dict(l=10, r=10, t=30, b=10), font=FONTE,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      hoverlabel=dict(font_size=13), **kw)
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig


def likert_divergente(df: pd.DataFrame, itens: list[str]) -> go.Figure:
    """Barras divergentes: discordância à esquerda, concordância à direita, neutro dividido ao meio.
    Usa a resposta original (sem inversão)."""
    linhas = []
    for item in itens:
        s = df[item].dropna()
        s = s[s.isin(C.LIKERT_ROTULOS)]
        n = len(s)
        cont = s.value_counts().reindex(C.LIKERT_ROTULOS, fill_value=0)
        pct = cont / n * 100 if n else cont * 0
        linhas.append((C.ROTULOS_ITENS.get(item, item) + f"  (n={n})", pct, cont, n))
    linhas = linhas[::-1]  # primeiro item no topo
    nomes = [l[0] for l in linhas]
    fig = go.Figure()
    neutro = "Nem concordo nem discordo"
    ordem_esq = ["Discordo parcialmente", "Discordo totalmente"]  # do centro para fora
    ordem_dir = ["Concordo parcialmente", "Concordo totalmente"]
    # metade do neutro de cada lado
    for lado, sinal in (("esq", -1), ("dir", 1)):
        fig.add_bar(y=nomes, x=[sinal * l[1][neutro] / 2 for l in linhas], orientation="h",
                    name=neutro, legendgroup=neutro, showlegend=lado == "dir",
                    marker=dict(color=CORES_LIKERT[neutro]),
                    customdata=[[l[1][neutro], l[2][neutro]] for l in linhas],
                    hovertemplate="%{y}<br>" + neutro + ": %{customdata[0]:.0f}% (%{customdata[1]})<extra></extra>")
    for rot in ordem_esq:
        fig.add_bar(y=nomes, x=[-l[1][rot] for l in linhas], orientation="h", name=rot,
                    marker=dict(color=CORES_LIKERT[rot]),
                    customdata=[[l[1][rot], l[2][rot]] for l in linhas],
                    hovertemplate="%{y}<br>" + rot + ": %{customdata[0]:.0f}% (%{customdata[1]})<extra></extra>")
    for rot in ordem_dir:
        fig.add_bar(y=nomes, x=[l[1][rot] for l in linhas], orientation="h", name=rot,
                    marker=dict(color=CORES_LIKERT[rot]),
                    customdata=[[l[1][rot], l[2][rot]] for l in linhas],
                    hovertemplate="%{y}<br>" + rot + ": %{customdata[0]:.0f}% (%{customdata[1]})<extra></extra>")
    # % discorda / concorda nas pontas
    for nome, pct, _, n in linhas:
        if not n:
            continue
        disc = pct["Discordo totalmente"] + pct["Discordo parcialmente"]
        conc = pct["Concordo totalmente"] + pct["Concordo parcialmente"]
        fig.add_annotation(y=nome, x=-102, text=f"{disc:.0f}%", showarrow=False, xanchor="right",
                           font=dict(size=12, color="gray"))
        fig.add_annotation(y=nome, x=102, text=f"{conc:.0f}%", showarrow=False, xanchor="left",
                           font=dict(size=12, color="gray"))
    fig.update_layout(barmode="relative", bargap=0.35,
                      legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", traceorder="normal"))
    fig.update_xaxes(range=[-115, 115], tickvals=[-100, -50, 0, 50, 100],
                     ticktext=["100%", "50%", "0", "50%", "100%"])
    fig.add_vline(x=0, line_width=1, line_color="gray")
    _layout(fig, 90 + 55 * len(itens))
    fig.update_layout(legend=dict(orientation="h", y=-0.12 - 0.25 / len(itens), x=0.5,
                                  xanchor="center", traceorder="normal"))
    return fig


def barras_contagem(serie: pd.Series, ordem: list[str] | None = None, altura: int | None = None) -> go.Figure:
    cont = serie.dropna().value_counts()
    if ordem:
        cont = cont.reindex([o for o in ordem if o in cont.index] + [i for i in cont.index if i not in ordem])
    else:
        cont = cont.sort_values(ascending=True)
    if ordem:
        cont = cont[::-1]
    total = cont.sum()
    fig = go.Figure(go.Bar(
        y=cont.index.astype(str), x=cont.values, orientation="h", marker_color=PRINCIPAL,
        text=[f"{v}  ({v / total:.0%})" for v in cont.values], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x}<extra></extra>"))
    fig.update_xaxes(range=[0, cont.max() * 1.35 if len(cont) else 1], title=None)
    return _layout(fig, altura or 60 + 32 * len(cont), bargap=0.3)


def caixa_por_grupo(df: pd.DataFrame, y: str, grupo: str, ordem: list[str] | None = None,
                    faixa: tuple[float, float] = (1, 5), ylab: str | None = None) -> go.Figure:
    dados = df[[y, grupo]].dropna()
    niveis = ordem or sorted(dados[grupo].unique())
    niveis = [n for n in niveis if n in set(dados[grupo])]
    fig = go.Figure()
    for i, nivel in enumerate(niveis):
        v = dados.loc[dados[grupo] == nivel, y]
        fig.add_box(y=v, name=f"{nivel}<br>(n={len(v)})", boxpoints="all", jitter=0.4, pointpos=0,
                    marker=dict(color=CATEGORICA[i % len(CATEGORICA)], size=8, opacity=0.7),
                    line=dict(width=2), fillcolor="rgba(0,0,0,0)",
                    hovertemplate="%{y:.2f}<extra></extra>")
    fig.update_yaxes(range=[faixa[0] - 0.3, faixa[1] + 0.3], showgrid=True,
                     gridcolor="rgba(128,128,128,0.15)", title=ylab or y)
    fig.add_hline(y=(faixa[0] + faixa[1]) / 2, line_dash="dot", line_color="gray",
                  annotation_text="neutro", annotation_position="top left")
    return _layout(fig, 360, showlegend=False)


def dispersao(df: pd.DataFrame, x: str, y: str, xlab: str, ylab: str) -> go.Figure:
    dados = df[[x, y]].dropna()
    cont = dados.groupby([x, y]).size().reset_index(name="n")
    fig = go.Figure(go.Scatter(
        x=cont[x], y=cont[y], mode="markers",
        marker=dict(size=8 + 5 * cont["n"], color=PRINCIPAL, opacity=0.65,
                    line=dict(width=2, color="white")),
        customdata=cont["n"],
        hovertemplate=f"{xlab}: %{{x:.2f}}<br>{ylab}: %{{y:.2f}}<br>respostas: %{{customdata}}<extra></extra>"))
    fig.update_xaxes(title=xlab)
    fig.update_yaxes(title=ylab, showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    return _layout(fig, 360)


def funil_descartes(df: pd.DataFrame, motivos: list[str]) -> go.Figure:
    """Funil: quantas respostas sobram depois de cada critério de descarte."""
    restante = len(df)
    etapas, valores, perdas = ["Recebidas"], [restante], [""]
    cont = df["motivo_descarte"].value_counts()
    curtos = {
        "D1 · Não aceitou o termo de consentimento": "D1 · Aceitou o termo",
        "D1 · Menor de 18 anos": "D1 · Maior de 18",
        "D2 · Colega da turma": "D2 · Não é da turma",
        "D2 · Fora da população (não atua nem busca atuar como dev)": "D2 · Na população-alvo",
        "D3 · Errou a pergunta de atenção (AT1)": "D3 · Acertou AT1",
        "D4 · Mesma resposta em todos os itens Likert": "D4 · Respostas variadas",
        "D5 · Resposta duplicada": "D5 · Sem duplicatas",
    }
    for m in motivos:
        k = int(cont.get(m, 0))
        restante -= k
        etapas.append(curtos.get(m, m))
        valores.append(restante)
        perdas.append(f"−{k} ({m.lower()})" if k else "sem descartes")
    fig = go.Figure(go.Funnel(
        y=etapas, x=valores, textinfo="value+percent initial",
        marker=dict(color=[PRINCIPAL] * (len(etapas) - 1) + [CATEGORICA[2]]),
        connector=dict(line=dict(color="rgba(128,128,128,0.3)", width=1)),
        customdata=perdas, hovertemplate="%{y}: %{x}<br>%{customdata}<extra></extra>"))
    return _layout(fig, 330)


def likert_por_grupo(df: pd.DataFrame, item: str, grupo: str, ordem: list[str] | None = None) -> go.Figure:
    """Um item Likert em barras divergentes, uma barra por segmento."""
    sub = df[[item, grupo]].dropna()
    niveis = ordem or sorted(sub[grupo].unique())
    niveis = [n for n in niveis if n in set(sub[grupo])]
    falso = pd.DataFrame({n: sub.loc[sub[grupo] == n, item].reset_index(drop=True) for n in niveis})
    return likert_divergente(falso, list(falso.columns))


def mapa_calor(a: pd.Series, b: pd.Series, ordem_a=None, ordem_b=None) -> go.Figure:
    """Tabela cruzada em % da linha, com a contagem no hover."""
    tab = pd.crosstab(a, b)
    if ordem_a:
        tab = tab.reindex([o for o in ordem_a if o in tab.index] + [i for i in tab.index if i not in ordem_a])
    if ordem_b:
        tab = tab[[o for o in ordem_b if o in tab.columns] + [c for c in tab.columns if c not in ordem_b]]
    pct = tab.div(tab.sum(axis=1), axis=0) * 100
    escala = [[0, "#f3f2ef"], [0.25, "#b7d3f6"], [0.5, "#6da7ec"], [0.75, "#2a78d6"], [1, "#104281"]]
    fig = go.Figure(go.Heatmap(
        z=pct.values, x=[str(c) for c in pct.columns], y=[f"{i} (n={tab.loc[i].sum()})" for i in pct.index],
        colorscale=escala, zmin=0, zmax=100, customdata=tab.values, xgap=2, ygap=2,
        text=[[f"{v:.0f}%" for v in linha] for linha in pct.values], texttemplate="%{text}",
        hovertemplate="%{y}<br>%{x}: %{z:.0f}% (%{customdata})<extra></extra>",
        colorbar=dict(title="% da linha", ticksuffix="%", thickness=12)))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(showgrid=False, tickangle=-20)
    return _layout(fig, 140 + 46 * len(pct))


def floresta_efeitos(res) -> go.Figure:
    """Tamanho de efeito de cada teste; cor indica significância após Holm."""
    import numpy as np
    linhas = [r for r in res if not np.isnan(r.efeito)][::-1]
    cores = [CATEGORICA[0] if r.p_holm < 0.05 else "#a3a29c" for r in linhas]
    fig = go.Figure()
    for lim, txt in ((0.1, "pequeno"), (0.3, "médio"), (0.5, "grande")):
        for s in (-1, 1):
            fig.add_vline(x=s * lim, line_dash="dot", line_color="rgba(128,128,128,0.35)")
        fig.add_annotation(x=lim, y=1.02, yref="paper", text=txt, showarrow=False,
                           font=dict(size=11, color="gray"))
    fig.add_vline(x=0, line_color="gray", line_width=1)
    fig.add_scatter(
        x=[r.efeito for r in linhas], y=[f"{r.qp} · {r.descricao}" for r in linhas], mode="markers",
        marker=dict(size=14, color=cores, line=dict(width=2, color="white"), symbol="diamond"),
        customdata=[[r.efeito_nome, r.p, r.p_holm, r.n] for r in linhas],
        hovertemplate="%{y}<br>%{customdata[0]} = %{x:.2f}<br>p = %{customdata[1]:.3f} · "
                      "p Holm = %{customdata[2]:.3f}<br>n = %{customdata[3]}<extra></extra>")
    fig.update_xaxes(range=[-1, 1], title="tamanho de efeito (r, ρ, φ, V ou ε²)")
    return _layout(fig, 90 + 42 * len(linhas), showlegend=False)


def barra_alfa(alfa: float, ic: tuple[float, float]) -> go.Figure:
    """Barra de referência do alfa: faixas de leitura, valor e intervalo de confiança."""
    fig = go.Figure()
    faixas = [(0, 0.6, "#f6d4d3", "fraco"), (0.6, 0.7, "#fbe7c2", "questionável"),
              (0.7, 0.8, "#d6e6fa", "aceitável"), (0.8, 1.0, "#b7d3f6", "bom")]
    for lo, hi, cor, nome in faixas:
        fig.add_shape(type="rect", x0=lo, x1=hi, y0=0, y1=1, fillcolor=cor, line_width=0, layer="below")
        fig.add_annotation(x=(lo + hi) / 2, y=1.35, text=nome, showarrow=False, font=dict(size=11, color="gray"))
    if ic[0] == ic[0]:
        fig.add_shape(type="line", x0=max(0, ic[0]), x1=ic[1], y0=0.5, y1=0.5, line=dict(color="#1b1b1a", width=2))
    if alfa == alfa:
        fig.add_scatter(x=[max(0, alfa)], y=[0.5], mode="markers", marker=dict(size=16, color=PRINCIPAL,
                        line=dict(width=2, color="white")), hovertemplate=f"α = {alfa:.2f}<extra></extra>")
    fig.update_xaxes(range=[0, 1], showgrid=False, tickvals=[0, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
    fig.update_yaxes(visible=False, range=[0, 1.6])
    return _layout(fig, 130, showlegend=False)


def rosca(serie: pd.Series, ordem: list[str] | None = None) -> go.Figure:
    cont = serie.dropna().value_counts()
    if ordem:
        cont = cont.reindex([o for o in ordem if o in cont.index])
    fig = go.Figure(go.Pie(labels=cont.index, values=cont.values, hole=0.6, sort=False,
                           marker=dict(colors=CATEGORICA[:len(cont)], line=dict(color="white", width=2)),
                           textinfo="percent", hovertemplate="%{label}: %{value} (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"<b>{cont.sum()}</b><br>respostas", showarrow=False, font=dict(size=14))
    return _layout(fig, 300, legend=dict(orientation="h", y=-0.1))


def proporcoes_por_grupo(tabela: pd.DataFrame, ordem_grupos: list[str]) -> go.Figure:
    """Proporção por categoria e estrato, com IC 95% de Wilson.
    tabela: colunas categoria, grupo, p, lo, hi, k, n."""
    fig = go.Figure()
    cats = list(dict.fromkeys(tabela["categoria"]))[::-1]
    for i, g in enumerate(ordem_grupos):
        t = tabela[tabela["grupo"] == g].set_index("categoria").reindex(cats)
        fig.add_bar(y=cats, x=t["p"] * 100, orientation="h", name=g,
                    marker_color=CATEGORICA[i % len(CATEGORICA)],
                    error_x=dict(type="data", symmetric=False, array=(t["hi"] - t["p"]) * 100,
                                 arrayminus=(t["p"] - t["lo"]) * 100, color="rgba(60,60,60,0.55)",
                                 thickness=1.5, width=3),
                    customdata=t[["k", "n", "lo", "hi"]].to_numpy(),
                    hovertemplate=g + "<br>%{y}: %{x:.0f}% (%{customdata[0]} de %{customdata[1]})"
                                  "<br>IC 95% Wilson: %{customdata[2]:.0%} a %{customdata[3]:.0%}<extra></extra>")
    fig.update_xaxes(range=[0, 105], ticksuffix="%", title=None)
    fig.update_layout(barmode="group", legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"))
    return _layout(fig, 120 + 34 * len(cats) * max(1, len(ordem_grupos)), bargap=0.25, bargroupgap=0.08)
