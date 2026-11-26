"""Testes estatísticos, tamanhos de efeito, intervalos e alfa de Cronbach (plano de análise do protocolo)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

Z95 = 1.96


# ---------------------------------------------------------------- proporções

def margem_erro(p: float, n: int) -> float:
    """Margem de erro de uma proporção, 95% de confiança: 1,96·√(p(1−p)/n)."""
    if n <= 0:
        return float("nan")
    return Z95 * np.sqrt(p * (1 - p) / n)


def wilson(k: float, n: int, z: float = Z95) -> tuple[float, float]:
    """IC 95% de Wilson para uma proporção k/n."""
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    meia = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return float(max(0.0, centro - meia)), float(min(1.0, centro + meia))


def proporcao(serie: pd.Series, condicao) -> dict:
    """Proporção, margem de erro e IC de Wilson."""
    s = serie.dropna()
    n = len(s)
    if n == 0:
        return {"p": np.nan, "k": 0, "n": 0, "e": np.nan, "ic": (np.nan, np.nan)}
    k = int(condicao(s).sum())
    p = k / n
    return {"p": p, "k": k, "n": n, "e": margem_erro(p, n), "ic": wilson(k, n)}


def diferenca_proporcoes(k1: float, n1: int, k2: float, n2: int) -> tuple[float, float, float]:
    """Diferença p1 − p2 com IC 95% de Newcombe (combinação dos ICs de Wilson)."""
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan"), float("nan")
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return d, d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def resumo(x: pd.Series) -> dict:
    """Mediana e intervalo interquartil."""
    s = x.dropna()
    if not len(s):
        return {"n": 0, "mediana": np.nan, "q1": np.nan, "q3": np.nan}
    return {"n": len(s), "mediana": float(s.median()), "q1": float(s.quantile(0.25)),
            "q3": float(s.quantile(0.75))}


# ---------------------------------------------------------------- magnitudes

def magnitude_r(r: float) -> str:
    """r, ρ, φ e V: 0,1 / 0,3 / 0,5."""
    if r != r:
        return "—"
    a = abs(r)
    return "desprezível" if a < 0.1 else "pequeno" if a < 0.3 else "médio" if a < 0.5 else "grande"


def magnitude_eps2(e: float) -> str:
    """ε²: 0,01 / 0,06 / 0,14."""
    return "desprezível" if e < 0.01 else "pequeno" if e < 0.06 else "médio" if e < 0.14 else "grande"


def magnitude_cliff(d: float) -> str:
    """Delta de Cliff (Romano et al., 2006): 0,147 / 0,33 / 0,474."""
    a = abs(d)
    return "desprezível" if a < 0.147 else "pequeno" if a < 0.33 else "médio" if a < 0.474 else "grande"


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


# ---------------------------------------------------------------- testes

def mann_whitney(y: pd.Series, grupo: pd.Series, qp: str, descricao: str,
                 ordem: list[str] | None = None) -> Resultado:
    """Mann-Whitney entre dois grupos. Efeitos: r = Z/√N e delta de Cliff (positivo = 1º grupo maior)."""
    dados = pd.DataFrame({"y": y, "g": grupo}).dropna()
    niveis = [n for n in (ordem or sorted(dados["g"].unique())) if n in set(dados["g"])]
    if len(niveis) != 2:
        return Resultado(qp, descricao, "Mann-Whitney U", len(dados), np.nan, np.nan,
                         "r = Z/√N", np.nan, "—", aviso="é preciso ter os dois grupos")
    a = dados.loc[dados.g == niveis[0], "y"].to_numpy(float)
    b = dados.loc[dados.g == niveis[1], "y"].to_numpy(float)
    n1, n2 = len(a), len(b)
    n = n1 + n2
    u = stats.mannwhitneyu(a, b, alternative="two-sided")
    _, empates = np.unique(np.concatenate([a, b]), return_counts=True)
    var_u = n1 * n2 / 12 * ((n + 1) - (empates ** 3 - empates).sum() / (n * (n - 1)))
    z = (u.statistic - n1 * n2 / 2) / np.sqrt(var_u) if var_u > 0 else 0.0
    r = z / np.sqrt(n)
    cliff = 2 * u.statistic / (n1 * n2) - 1
    aviso = "grupo com menos de 5 respostas: resultado frágil" if min(n1, n2) < 5 else ""
    return Resultado(qp, descricao, "Mann-Whitney U", n, float(u.statistic), float(u.pvalue),
                     "r = Z/√N", float(r), magnitude_r(r), aviso=aviso,
                     extra={"grupos": {niveis[0]: (n1, float(np.median(a))), niveis[1]: (n2, float(np.median(b)))},
                            "cliff": float(cliff), "cliff_mag": magnitude_cliff(cliff)})


def _holm_lista(ps: list[float]) -> list[float]:
    m = len(ps)
    ordem = np.argsort(ps)
    ajust, anterior = [np.nan] * m, 0.0
    for k, i in enumerate(ordem):
        anterior = min(1.0, max(anterior, (m - k) * ps[i]))
        ajust[i] = anterior
    return ajust


def dunn(dados: pd.DataFrame) -> pd.DataFrame:
    """Pós-teste de Dunn (pares de grupos), com correção de Holm entre os pares."""
    n = len(dados)
    postos = pd.Series(stats.rankdata(dados["y"]), index=dados.index)
    _, empates = np.unique(dados["y"], return_counts=True)
    corr = (empates ** 3 - empates).sum() / (12 * (n - 1))
    medias = postos.groupby(dados["g"], observed=True).mean()
    tamanhos = dados.groupby("g", observed=True).size()
    niveis = list(medias.index)
    linhas = []
    for i in range(len(niveis)):
        for j in range(i + 1, len(niveis)):
            gi, gj = niveis[i], niveis[j]
            ep = np.sqrt((n * (n + 1) / 12 - corr) * (1 / tamanhos[gi] + 1 / tamanhos[gj]))
            z = (medias[gi] - medias[gj]) / ep
            linhas.append({"Par": f"{gi} × {gj}", "z": float(z), "p": float(2 * stats.norm.sf(abs(z)))})
    t = pd.DataFrame(linhas)
    if len(t):
        t["p (Holm)"] = _holm_lista(t["p"].tolist())
    return t


def kruskal(y: pd.Series, grupo: pd.Series, qp: str, descricao: str,
            ordem: list[str] | None = None) -> Resultado:
    """Kruskal-Wallis + Dunn (Holm). Efeito: ε² = H / (n − 1)."""
    dados = pd.DataFrame({"y": y, "g": grupo}).dropna()
    niveis = [n for n in (ordem or sorted(dados["g"].unique())) if n in set(dados["g"])]
    dados["g"] = pd.Categorical(dados["g"], niveis, ordered=True)
    grupos = [g["y"].values for _, g in dados.groupby("g", observed=True) if len(g) > 0]
    if len(grupos) < 2:
        return Resultado(qp, descricao, "Kruskal-Wallis H", len(dados), np.nan, np.nan,
                         "ε²", np.nan, "—", aviso="é preciso ter dois ou mais grupos")
    h = stats.kruskal(*grupos)
    n = len(dados)
    eps2 = h.statistic / (n - 1)
    tamanhos = dados.groupby("g", observed=True).size()
    medianas = dados.groupby("g", observed=True)["y"].median()
    aviso = "há grupos com menos de 5 respostas" if (tamanhos < 5).any() else ""
    return Resultado(qp, descricao, "Kruskal-Wallis H + Dunn", n, float(h.statistic), float(h.pvalue),
                     "ε²", float(eps2), magnitude_eps2(eps2), aviso=aviso,
                     extra={"grupos": {str(g): (int(tamanhos[g]), float(medianas[g])) for g in tamanhos.index},
                            "dunn": dunn(dados)})


def spearman(x: pd.Series, y: pd.Series, qp: str, descricao: str) -> Resultado:
    dados = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(dados) < 3:
        return Resultado(qp, descricao, "Correlação de Spearman", len(dados), np.nan, np.nan,
                         "ρ", np.nan, "—", aviso="amostra insuficiente")
    rho, p = stats.spearmanr(dados["x"], dados["y"])
    return Resultado(qp, descricao, "Correlação de Spearman", len(dados), float(rho), float(p),
                     "ρ", float(rho), magnitude_r(rho),
                     aviso="n < 10: resultado frágil" if len(dados) < 10 else "")


def _p_permutacao(a: np.ndarray, b: np.ndarray, chi2_obs: float, reps: int = 10000) -> float:
    """p-valor de Monte Carlo para tabelas maiores que 2×2 (aproxima o exato de Fisher-Freeman-Halton)."""
    rng = np.random.default_rng(42)
    ca, ia = np.unique(a, return_inverse=True)
    cb, ib = np.unique(b, return_inverse=True)
    maiores = 0
    for _ in range(reps):
        tab = np.zeros((len(ca), len(cb)))
        np.add.at(tab, (ia, rng.permutation(ib)), 1)
        tab = tab[tab.sum(axis=1) > 0][:, tab.sum(axis=0) > 0]
        maiores += stats.chi2_contingency(tab, correction=False)[0] >= chi2_obs - 1e-9
    return (maiores + 1) / (reps + 1)


def qui_quadrado(a: pd.Series, b: pd.Series, qp: str, descricao: str) -> Resultado:
    """χ² de independência; Fisher quando alguma frequência esperada < 5. Efeito: φ (2×2) ou V de Cramér."""
    dados = pd.DataFrame({"a": a, "b": b}).dropna()
    tab = pd.crosstab(dados["a"], dados["b"])
    n = int(tab.values.sum())
    efeito_nome = "φ" if tab.shape == (2, 2) else "V de Cramér"
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return Resultado(qp, descricao, "Qui-quadrado", n, np.nan, np.nan, efeito_nome, np.nan, "—",
                         aviso="é preciso ao menos 2 categorias em cada variável")
    chi2, p, gl, esperado = stats.chi2_contingency(tab, correction=False)
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    teste = f"Qui-quadrado (gl = {gl})"
    if (esperado < 5).any():
        if tab.shape == (2, 2):
            p = stats.fisher_exact(tab.values)[1]
            teste = "Exato de Fisher"
        else:
            p = _p_permutacao(dados["a"].to_numpy(str), dados["b"].to_numpy(str), chi2)
            teste = "Fisher (Monte Carlo, 10.000 permutações)"
    return Resultado(qp, descricao, teste, n, float(chi2), float(p), efeito_nome, float(v), magnitude_r(v),
                     extra={"tabela": tab})


def holm(resultados: list[Resultado]) -> None:
    """Correção de Holm-Bonferroni sobre uma família de testes (preenche p_holm)."""
    validos = [r for r in resultados if not np.isnan(r.p)]
    for r, aj in zip(validos, _holm_lista([r.p for r in validos])):
        r.p_holm = aj


# ---------------------------------------------------------------- confiabilidade

def cronbach(itens: pd.DataFrame, padronizado: bool = False) -> dict:
    """Alfa de Cronbach (casos completos), alfa se o item for excluído e correlação item-total.
    padronizado=True converte os itens em escore z antes (alfa padronizado, itens de escalas diferentes)."""
    x = itens.dropna()
    k, n = x.shape[1], len(x)
    if k < 2 or n < 3:
        return {"alfa": np.nan, "n": n, "k": k, "ic": (np.nan, np.nan), "itens": pd.DataFrame()}
    if padronizado:
        dp = x.std(ddof=1).replace(0, np.nan)
        x = ((x - x.mean()) / dp).fillna(0)

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


def kappa_cohen(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    """Kappa de Cohen entre dois codificadores (categoria principal de cada resposta)."""
    d = pd.DataFrame({"a": a, "b": b}).dropna()
    n = len(d)
    if n < 2:
        return np.nan, n
    po = (d["a"] == d["b"]).mean()
    cats = set(d["a"]) | set(d["b"])
    pe = sum((d["a"] == c).mean() * (d["b"] == c).mean() for c in cats)
    return (float((po - pe) / (1 - pe)) if pe < 1 else 1.0), n
