"""Configuração do estudo, seguindo o protocolo pré-registrado (protocolo/).

As colunas são localizadas por um trecho do texto da pergunta (sem acento, minúsculo),
então o dashboard continua funcionando se a ordem das colunas mudar na planilha.
Os IDs entre parênteses (T3, EPA1, S1...) são os do protocolo.
"""

# chave interna -> trecho do texto da pergunta no formulário
COLUNAS = {
    "ts": "carimbo de data",
    "consentimento": "aceita participar",          # T1
    "maior18": "18 anos ou mais",                  # T2
    "turma": "matriculado",                        # T4
    "situacao": "situacao atual em relacao",       # T3 -> M1
    "meses_busca": "quantos meses voce esta buscando",   # B1
    "candidaturas": "quantas vagas de dev voce se candidatou",  # B2
    "entrevistas": "quantas entrevistas",          # B3
    "exp_anos": "anos de experiencia profissional",  # P1 -> M2
    "senioridade": "senioridade atual",            # P2 -> M3
    "area": "principal area de atuacao",           # P3
    "porte": "porte da empresa",                   # P4
    "regiao": "regiao do brasil",                  # P5
    "faixa_etaria": "faixa etaria",                # P6
    "formacao": "maior formacao",                  # P7
    "layoff": "layoff",                            # B4
    "canal": "ficou sabendo desta pesquisa",       # S3
    "emp1": "conseguiria um emprego como dev em pouco tempo",  # EPA1
    "emp2": "existem muitas vagas no mercado",     # EPA2
    "atencao": "para confirmar que voce esta lendo",  # AT1
    "emp3": "habilidades tecnicas sao valorizadas",  # EPA3
    "emp4": "teria dificuldade para conseguir uma vaga",  # EPA4 (R)
    "ia1": "um dos principais fatores das mudancas",  # AIA1
    "ia2": "contratam menos devs porque usam ia",  # AIA2
    "ia3": "mais a fatores economicos",            # AIA3 (R)
    "uso_ia": "com que frequencia voce usa assistentes",  # API1
    "prof_ia": "proficiencia no uso de ia",        # API2
    "prod_ia": "entregar tarefas mais rapido",     # API3
    "antes2022": "antes de dezembro de 2022",      # F1
    "cmp1": "mais dificil conseguir entrevistas",  # VPE1
    "cmp2": "diminuiu o numero de vagas",          # VPE2
    "cmp3": "mais longos ou mais exigentes",       # VPE3
    "cmp4": "oportunidades de trabalho aumentaram",  # VPE4 (R)
    "emp_vs_antes": "a sua empregabilidade hoje esta",  # G1
    "mudancas": "quais destas mudancas voce observou",  # S1
    "aberta": "principal mudanca que a ia trouxe",  # S2
}

# Textos retirados antes da análise (anonimização, protocolo seção 6). A resposta continua na amostra;
# só os campos listados ficam em branco. Chave = carimbo de data/hora da resposta.
TEXTOS_RETIRADOS = {
    "2026-11-25 16:44:06": ["canal", "aberta"],
    "2026-11-25 16:44:54": ["canal", "aberta"],
}

RESPOSTA_ATENCAO = "Discordo parcialmente"

LIKERT = {
    "Discordo totalmente": 1,
    "Discordo parcialmente": 2,
    "Nem concordo nem discordo": 3,
    "Concordo parcialmente": 4,
    "Concordo totalmente": 5,
}
LIKERT_ROTULOS = list(LIKERT)  # ordem 1..5
NAO_SEI = "Não sei avaliar"     # vira ausente (NaN)

COMPARACAO = {"Muito pior": 1, "Pior": 2, "Igual": 3, "Melhor": 4, "Muito melhor": 5}
G1_AGRUPADO = {"Muito pior": "Pior", "Pior": "Pior", "Igual": "Igual", "Melhor": "Melhor", "Muito melhor": "Melhor"}

# API1 e API2 vão para a escala 1–5 para entrar no escore API junto com API3
USO_IA = {
    "Nunca": 1,
    "Raramente (menos de uma vez por semana)": 2,
    "Algumas vezes por semana": 3,
    "Diariamente": 4,
    "Várias vezes ao dia": 5,
}
PROF_IA = {"Nenhuma": 1, "Básica": 2, "Intermediária": 3, "Avançada": 4, "Especialista": 5}

SENIORIDADE_ORDEM = [
    "Ainda não trabalhei como dev", "Estágio ou trainee", "Júnior", "Pleno", "Sênior", "Especialista, tech lead ou acima",
]
# M3: senioridade em três grupos
SENIORIDADE_GRUPO = {
    "Ainda não trabalhei como dev": "Até júnior", "Estágio ou trainee": "Até júnior", "Júnior": "Até júnior",
    "Pleno": "Pleno", "Sênior": "Sênior ou acima", "Especialista, tech lead ou acima": "Sênior ou acima",
}
M3_ORDEM = ["Até júnior", "Pleno", "Sênior ou acima"]
PORTE_ORDEM = [
    "Até 49 pessoas", "50 a 249 pessoas", "250 a 999 pessoas", "1.000 pessoas ou mais",
    "Não se aplica (nunca trabalhei como dev)",
]
FAIXAS_EXP = [(-1, 1, "0 a 1 ano"), (1, 4, "2 a 4 anos"), (4, 9, "5 a 9 anos"), (9, 99, "10 anos ou mais")]

# M1: situação -> estrato. Respostas fora daqui saem da população.
DENTRO_MERCADO = {"Empregado(a) com carteira assinada (CLT)", "Contrato PJ", "Freelancer ou autônomo(a)"}
FORA_MERCADO = {"Desempregado(a), buscando vaga de dev", "Buscando o primeiro emprego como dev",
                "Saí da área de desenvolvimento"}
FORA_POPULACAO_PREFIXO = "Não atuo"
M1_ORDEM = ["Dentro do mercado", "Fora do mercado"]

# Metas do protocolo (seção 2)
META_TOTAL, META_DENTRO, META_FORA = 50, 30, 20
INICIO_PREVISTO, FIM_PREVISTO = "2026-11-17", "2026-12-07 23:59"

# Escores (M4, M5, M7, M8): média dos itens após inverter os (R). "minimo" = itens exigidos.
CONSTRUTOS = {
    "EPA": {
        "nome": "Empregabilidade atual (EPA)", "metrica": "M4",
        "itens": ["emp1", "emp2", "emp3", "emp4"], "inv": ["emp4"], "minimo": 4,
        "leitura": "maior = mais empregável hoje", "padronizado": False,
    },
    "VPE": {
        "nome": "Variação percebida da empregabilidade (VPE)", "metrica": "M5",
        "itens": ["cmp1", "cmp2", "cmp3", "cmp4"], "inv": ["cmp4"], "minimo": 3,
        "leitura": "maior = percebe mais piora desde 2023 (só F1 = Sim)", "padronizado": False,
    },
    "AIA": {
        "nome": "Atribuição das mudanças à IA (AIA)", "metrica": "M7",
        "itens": ["ia1", "ia2", "ia3"], "inv": ["ia3"], "minimo": 3,
        "leitura": "maior = atribui mais à IA do que à economia", "padronizado": False,
    },
    "API": {
        "nome": "Adoção e proficiência em IA (API)", "metrica": "M8",
        "itens": ["uso_ia", "prof_ia", "prod_ia"], "inv": [], "minimo": 3,
        "leitura": "maior = usa mais e domina mais a IA", "padronizado": True,
    },
}
META_ALFA = 0.70

# Rótulos curtos dos itens (para os gráficos)
ROTULOS_ITENS = {
    "emp1": "EPA1 · Conseguiria emprego em pouco tempo",
    "emp2": "EPA2 · Há muitas vagas compatíveis com meu perfil",
    "emp3": "EPA3 · Minhas habilidades são valorizadas",
    "emp4": "EPA4 (R) · Teria dificuldade para vaga igual ou melhor",
    "ia1": "AIA1 · IA é um dos principais fatores das mudanças",
    "ia2": "AIA2 · Empresas contratam menos devs por causa da IA",
    "ia3": "AIA3 (R) · Mudanças se devem mais à economia que à IA",
    "uso_ia": "API1 · Frequência de uso de IA",
    "prof_ia": "API2 · Proficiência em IA",
    "prod_ia": "API3 · Uso IA para entregar mais rápido sem perder qualidade",
    "cmp1": "VPE1 · Ficou mais difícil conseguir entrevistas",
    "cmp2": "VPE2 · Diminuiu o número de vagas para meu perfil",
    "cmp3": "VPE3 · Processos seletivos mais longos ou exigentes",
    "cmp4": "VPE4 (R) · Minhas oportunidades aumentaram",
}

# Itens em escala de concordância (barras divergentes)
BLOCOS_LIKERT = {
    "EPA · Empregabilidade atual": ["emp1", "emp2", "emp3", "emp4"],
    "AIA · Atribuição das mudanças à IA": ["ia1", "ia2", "ia3"],
    "API3 · Uso de IA": ["prod_ia"],
    "VPE · Comparando com antes de 2023 (só F1 = Sim)": ["cmp1", "cmp2", "cmp3", "cmp4"],
}
ITENS_LIKERT = [i for b in BLOCOS_LIKERT.values() for i in b]

# S1: opções de mudança observada (M10)
OPCOES_S1 = [
    "Menos vagas para júnior e estágio",
    "Mais anos de experiência exigidos para o mesmo nível",
    "Exigência de conhecimento em IA nas vagas",
    "Processos seletivos com mais etapas ou mais longos",
    "Testes técnicos mais difíceis",
    "Salários ofertados menores",
    "Não observei mudanças",
]

MIN_SEGMENTO = 5   # o dashboard só mostra segmentos com 5 ou mais respostas (protocolo, seção 6)
JANELA_DUPLICATA_MIN = 60  # D5: respostas idênticas enviadas com até 60 min de diferença
ALFA = 0.05
