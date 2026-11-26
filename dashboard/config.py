"""Configuração do estudo: mapeamento das colunas do Google Forms, escalas e construtos.

As colunas são localizadas por um trecho do texto da pergunta (sem acento, minúsculo),
então o dashboard continua funcionando se a ordem das colunas mudar na planilha.
"""

# chave interna -> trecho do texto da pergunta no formulário
COLUNAS = {
    "ts": "carimbo de data",
    "consentimento": "aceita participar",
    "maior18": "18 anos ou mais",
    "turma": "matriculado",
    "situacao": "situacao atual em relacao",
    "meses_busca": "quantos meses voce esta buscando",
    "candidaturas": "quantas vagas de dev voce se candidatou",
    "entrevistas": "quantas entrevistas",
    "exp_anos": "anos de experiencia profissional",
    "senioridade": "senioridade atual",
    "area": "principal area de atuacao",
    "porte": "porte da empresa",
    "regiao": "regiao do brasil",
    "faixa_etaria": "faixa etaria",
    "formacao": "maior formacao",
    "layoff": "layoff",
    "canal": "ficou sabendo desta pesquisa",
    "emp1": "conseguiria um emprego como dev em pouco tempo",
    "emp2": "existem muitas vagas no mercado",
    "atencao": "para confirmar que voce esta lendo",
    "emp3": "habilidades tecnicas sao valorizadas",
    "emp4": "teria dificuldade para conseguir uma vaga",
    "ia1": "um dos principais fatores das mudancas",
    "ia2": "contratam menos devs porque usam ia",
    "ia3": "mais a fatores economicos",
    "uso_ia": "com que frequencia voce usa assistentes",
    "prof_ia": "proficiencia no uso de ia",
    "prod_ia": "entregar tarefas mais rapido",
    "antes2022": "antes de dezembro de 2022",
    "cmp1": "mais dificil conseguir entrevistas",
    "cmp2": "diminuiu o numero de vagas",
    "cmp3": "mais longos ou mais exigentes",
    "cmp4": "oportunidades de trabalho aumentaram",
    "emp_vs_antes": "a sua empregabilidade hoje esta",
    "mudancas": "quais destas mudancas voce observou",
    "aberta": "principal mudanca que a ia trouxe",
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

USO_IA = {
    "Nunca": 0,
    "Raramente (menos de uma vez por semana)": 1,
    "Algumas vezes por semana": 2,
    "Diariamente": 3,
    "Várias vezes ao dia": 4,
}
PROF_IA = {"Nenhuma": 0, "Básica": 1, "Intermediária": 2, "Avançada": 3, "Especialista": 4}

SENIORIDADE_ORDEM = [
    "Estágio ou trainee", "Júnior", "Pleno", "Sênior", "Especialista, tech lead ou acima",
]
PORTE_ORDEM = [
    "Até 49 pessoas", "50 a 249 pessoas", "250 a 999 pessoas", "1.000 pessoas ou mais",
    "Não se aplica (nunca trabalhei como dev)",
]
FAIXAS_EXP = [(-1, 1, "0 a 1 ano"), (1, 4, "2 a 4 anos"), (4, 9, "5 a 9 anos"), (9, 99, "10 anos ou mais")]

# Situação -> grupo de mercado (QP3). Respostas fora daqui saem da população.
DENTRO_MERCADO = {"Empregado(a) com carteira assinada (CLT)", "Contrato PJ", "Freelancer ou autônomo(a)"}
FORA_MERCADO = {"Desempregado(a), buscando vaga de dev", "Buscando o primeiro emprego como dev"}
FORA_POPULACAO_PREFIXO = "Não atuo"

# Construtos medidos por mais de um item. "inv" = item invertido (6 - valor).
CONSTRUTOS = {
    "Empregabilidade percebida hoje": {
        "itens": ["emp1", "emp2", "emp3", "emp4"],
        "inv": ["emp4"],
        "leitura": "maior = mais empregável",
    },
    "Atribuição das mudanças à IA": {
        "itens": ["ia1", "ia2", "ia3"],
        "inv": ["ia3"],
        "leitura": "maior = atribui mais à IA do que à economia",
    },
    "Piora do mercado desde 2023": {
        "itens": ["cmp1", "cmp2", "cmp3", "cmp4"],
        "inv": ["cmp4"],
        "leitura": "maior = percebe mercado pior que antes de 2023",
    },
}

# Rótulos curtos dos itens Likert (para os gráficos)
ROTULOS_ITENS = {
    "emp1": "Conseguiria emprego em pouco tempo",
    "emp2": "Há muitas vagas compatíveis com meu perfil",
    "emp3": "Minhas habilidades são valorizadas",
    "emp4": "Teria dificuldade para vaga igual ou melhor (inv.)",
    "ia1": "IA é um dos principais fatores das mudanças",
    "ia2": "Empresas contratam menos devs por causa da IA",
    "ia3": "Mudanças se devem mais à economia que à IA (inv.)",
    "prod_ia": "Uso IA para entregar mais rápido sem perder qualidade",
    "cmp1": "Ficou mais difícil conseguir entrevistas",
    "cmp2": "Diminuiu o número de vagas para meu perfil",
    "cmp3": "Processos seletivos mais longos ou exigentes",
    "cmp4": "Minhas oportunidades aumentaram (inv.)",
}

BLOCOS_LIKERT = {
    "Empregabilidade hoje": ["emp1", "emp2", "emp3", "emp4"],
    "Papel da IA no mercado": ["ia1", "ia2", "ia3"],
    "Uso de IA": ["prod_ia"],
    "Comparando com antes de 2023 (só quem já atuava)": ["cmp1", "cmp2", "cmp3", "cmp4"],
}

ALFA = 0.05
