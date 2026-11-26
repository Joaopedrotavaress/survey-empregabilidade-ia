"""Testes estatísticos, tamanhos de efeito, margem de erro e alfa de Cronbach."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

Z95 = 1.96


def margem_erro(p: float, n: int) -> float:
    """Margem de erro de uma proporção, 95% de confiança: 1,96·√(p(1−p)/n)."""
    if n <= 0:
        return float("nan")
    return Z95 * np.sqrt(p * (1 - p) / n)


def proporcao(serie: pd.Series, condicao) -> tuple[float, float, int]:
    s = serie.dropna()
    n = len(s)
    if n == 0:
        return float("nan"), float("nan"), 0
    p = float(condicao(s).mean())
    return p, margem_erro(p, n), n


def magnitude_r(r: float) -> str:
    a = abs(r)
    return "desprezível" if a < 0.1 else "pequeno" if a < 0.3 else "médio" if a < 0.5 else "grande"


def magnitude_eps2(e: float) -> str:
    return "desprezível" if e < 0.01 else "pequeno" if e < 0.08 else "médio" if e < 0.26 else "grande"


@dataclass
class Resultado:
    qp: str
    descricao: str
    teste: str
    n: int
    estatistica: float
    p: float
    efeito_nome: str
    efeito: float
    efeito_mag: str
    p_holm: float = float("nan")
    aviso: str = ""
    extra: dict = field(default_factory=dict)


def wilcoxon_vs_neutro(x: pd.Series, neutro: float, qp: str, descricao: str) -> Resultado:
    """Wilcoxon de uma amostra contra o ponto neutro. Efeito: correlação rank-bisserial."""
    d = (x.dropna() - neutro)
    d = d[d != 0]
    n_total = int(x.notna().sum())
    if len(d) < 2:
        return Resultado(qp, descricao, "Wilcoxon (1 amostra)", n_total, np.nan, np.nan,
                         "r rank-bisserial", np.nan, "—", aviso="amostra insuficiente")
    w = stats.wilcoxon(d, zero_method="wilcox", alternative="two-sided")
    ranks = stats.rankdata(d.abs())
    w_pos, w_neg = ranks[d > 0].sum(), ranks[d < 0].sum()
    r = (w_pos - w_neg) / (w_pos + w_neg)
    aviso = "n < 10: resultado frágil" if n_total < 10 else ""
    return Resultado(qp, descricao, f"Wilcoxon (1 amostra, H0: mediana = {neutro:g})", n_total,
                     float(w.statistic), float(w.pvalue), "r rank-bisserial", float(r), magnitude_r(r),
                     aviso=aviso, extra={"mediana": float(x.median()), "media": float(x.mean())})


def mann_whitney(y: pd.Series, grupo: pd.Series, qp: str, descricao: str) -> Resultado:
    """Mann-Whitney entre dois grupos. Efeito: rank-bisserial (positivo = 1º grupo maior)."""
    dados = pd.DataFrame({"y": y, "g": grupo}).dropna()
    niveis = sorted(dados["g"].unique())
    if len(niveis) != 2:
        return Resultado(qp, descricao, "Mann-Whitney U", len(dados), np.nan, np.nan,
                         "r rank-bisserial", np.nan, "—", aviso="é preciso ter os dois grupos")
    a = dados.loc[dados.g == niveis[0], "y"]
    b = dados.loc[dados.g == niveis[1], "y"]
    u = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = 2 * u.statistic / (len(a) * len(b)) - 1
    aviso = "grupo com menos de 5 respostas: resultado frágil" if min(len(a), len(b)) < 5 else ""
    return Resultado(qp, descricao, "Mann-Whitney U", len(dados), float(u.statistic), float(u.pvalue),
                     "r rank-bisserial", float(r), magnitude_r(r), aviso=aviso,
                     extra={"grupos": {niveis[0]: (len(a), float(a.median())),
                                       niveis[1]: (len(b), float(b.median()))}})


def kruskal(y: pd.Series, grupo: pd.Series, qp: str, descricao: str) -> Resultado:
    """Kruskal-Wallis. Efeito: ε² = H / (n − 1)."""
    dados = pd.DataFrame({"y": y, "g": grupo}).dropna()
    grupos = [g["y"].values for _, g in dados.groupby("g") if len(g) > 0]
    if len(grupos) < 2:
        return Resultado(qp, descricao, "Kruskal-Wallis H", len(dados), np.nan, np.nan,
                         "ε²", np.nan, "—", aviso="é preciso ter dois ou mais grupos")
    h = stats.kruskal(*grupos)
    n = len(dados)
    eps2 = h.statistic / (n - 1)
    menores = dados.groupby("g").size()
    aviso = "há grupos com menos de 5 respostas" if (menores < 5).any() else ""
    return Resultado(qp, descricao, "Kruskal-Wallis H", n, float(h.statistic), float(h.pvalue),
                     "ε²", float(eps2), magnitude_eps2(eps2), aviso=aviso)


def spearman(x: pd.Series, y: pd.Series, qp: str, descricao: str) -> Resultado:
    dados = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(dados) < 3:
        return Resultado(qp, descricao, "Correlação de Spearman", len(dados), np.nan, np.nan,
                         "ρ", np.nan, "—", aviso="amostra insuficiente")
    rho, p = stats.spearmanr(dados["x"], dados["y"])
    return Resultado(qp, descricao, "Correlação de Spearman", len(dados), float(rho), float(p),
                     "ρ (Spearman)", float(rho), magnitude_r(rho),
                     aviso="n < 10: resultado frágil" if len(dados) < 10 else "")


def holm(resultados: list[Resultado]) -> None:
    """Correção de Holm-Bonferroni sobre todos os testes inferenciais (preenche p_holm)."""
    validos = [r for r in resultados if not np.isnan(r.p)]
    m = len(validos)
    ordem = sorted(validos, key=lambda r: r.p)
    anterior = 0.0
    for k, r in enumerate(ordem):
        ajustado = min(1.0, max(anterior, (m - k) * r.p))
        r.p_holm = ajustado
        anterior = ajustado


def cronbach(itens: pd.DataFrame) -> dict:
    """Alfa de Cronbach (casos completos), alfa se o item for excluído e correlação item-total."""
    x = itens.dropna()
    k, n = x.shape[1], len(x)
    if k < 2 or n < 3:
        return {"alfa": np.nan, "n": n, "k": k, "ic": (np.nan, np.nan), "itens": pd.DataFrame()}

    def alfa(m: np.ndarray) -> float:
        var_total = m.sum(axis=1).var(ddof=1)
        if var_total == 0:
            return np.nan
        return m.shape[1] / (m.shape[1] - 1) * (1 - m.var(axis=0, ddof=1).sum() / var_total)

    m = x.to_numpy(float)
    a = alfa(m)
    rng = np.random.default_rng(42)
    boot = [alfa(m[rng.integers(0, n, n)]) for _ in range(2000)]
    boot = np.array([b for b in boot if not np.isnan(b)])
    ic = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))) if len(boot) else (np.nan, np.nan)

    linhas = []
    for j, col in enumerate(x.columns):
        resto = np.delete(m, j, axis=1)
        a_sem = alfa(resto) if resto.shape[1] >= 2 else np.nan
        r_it = stats.pearsonr(m[:, j], resto.sum(axis=1))[0] if m[:, j].std() > 0 else np.nan
        linhas.append({"item": col, "correlação item-total": r_it, "alfa se excluído": a_sem})
    return {"alfa": float(a), "n": n, "k": k, "ic": ic, "itens": pd.DataFrame(linhas)}


def leitura_alfa(a: float) -> str:
    if np.isnan(a):
        return "não calculável"
    return ("excelente" if a >= 0.9 else "boa" if a >= 0.8 else "aceitável" if a >= 0.7
            else "questionável" if a >= 0.6 else "fraca" if a >= 0.5 else "inaceitável")


def qui_quadrado(a: pd.Series, b: pd.Series, qp: str, descricao: str) -> Resultado:
    """χ² de independência. Efeito: V de Cramér. Tabelas 2×2 com esperado < 5 usam Fisher."""
    tab = pd.crosstab(a, b)
    tab = tab.loc[tab.sum(axis=1) > 0, tab.sum(axis=0) > 0]
    n = int(tab.values.sum())
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return Resultado(qp, descricao, "Qui-quadrado", n, np.nan, np.nan, "V de Cramér", np.nan, "—",
                         aviso="é preciso ao menos 2 categorias em cada variável")
    chi2, p, gl, esperado = stats.chi2_contingency(tab, correction=False)
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    teste, aviso = f"Qui-quadrado (gl = {gl})", ""
    if (esperado < 5).mean() > 0.2:
        if tab.shape == (2, 2):
            p = stats.fisher_exact(tab.values)[1]
            teste = "Exato de Fisher"
        else:
            aviso = "mais de 20% das células com frequência esperada < 5: interpretar com cautela"
    mag = "desprezível" if v < 0.1 else "pequeno" if v < 0.3 else "médio" if v < 0.5 else "grande"
    return Resultado(qp, descricao, teste, n, float(chi2), float(p), "V de Cramér", float(v), mag, aviso=aviso)
