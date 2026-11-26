# Survey pré-registrado: empregabilidade de devs após a IA generativa

Trabalho final da disciplina **Medição e Experimentação em Engenharia de Software**, Engenharia de Software, PUC Minas.

O estudo mede se a empregabilidade percebida de desenvolvedores mudou após a popularização da IA generativa (2023 em diante) e se essa mudança difere entre quem está dentro e fora do mercado de trabalho.

## Integrantes

- Arthur Henrique Teixeira e Silva Bacelete
- Davi Augusto Dias Soares
- João Pedro Tavares e Amorim
- Pedro Henrique Morais Marques
- Victor Lucas Tornelli

## Pré-registro

O protocolo (Parte 1) fica em `protocolo/`. **A data do commit que adiciona o protocolo final é o registro do estudo** e precisa ser anterior à primeira resposta coletada. Mudanças posteriores ao protocolo são tratadas como desvios e declaradas na página de metodologia do dashboard.

## Estrutura

| Pasta | Conteúdo |
| --- | --- |
| `protocolo/` | Protocolo do survey (PDF e Word) |
| `questionario/` | Formulário completo, com todas as opções de resposta e ramificações |
| `dados/` | Exportação bruta do Google Forms (CSV com data e hora, sem identificadores) |
| `dashboard/` | Código do dashboard (Streamlit), que lê o CSV bruto e aplica a limpeza |
| `evidencias/` | Capturas datadas da divulgação e planilha de controle (sem dados de respondentes) |

## Dados e privacidade

O formulário não coleta nome, e-mail, telefone, CPF, empresa nem IP. Antes de entrar em `dados/`, a única alteração no CSV é trocar nomes citados nas respostas abertas por `[PESSOA]` ou `[EMPRESA]`. O repositório é privado.

## Dashboard

Streamlit + Plotly + SciPy. Lê a planilha de respostas e refaz a limpeza e as estatísticas a cada acesso
(cache de 60 s; o botão "Atualizar agora" força a releitura).

```bash
py -m venv .venv
.venv\Scripts\pip install -r dashboard/requirements.txt
.venv\Scripts\streamlit run dashboard/app.py
```

**Fonte dos dados** (nesta ordem):

1. `SHEET_URL` em `.streamlit/secrets.toml` (veja `.streamlit/secrets.toml.example`) ou variável de ambiente:
   link da planilha de respostas do Google Forms, compartilhada como "Qualquer pessoa com o link: leitor".
   Assim o dashboard mostra as respostas novas sem ninguém exportar nada.
2. Se não houver link, o arquivo `.csv` ou `.xlsx` mais recente em `dados/`.

| Arquivo | Conteúdo |
| --- | --- |
| `dashboard/config.py` | Mapeamento das perguntas, escalas, itens invertidos e construtos |
| `dashboard/dados.py` | Leitura e critérios de descarte (cada descarte com motivo) |
| `dashboard/estatistica.py` | Wilcoxon, Mann-Whitney, Kruskal-Wallis, Spearman, χ², Holm, margem de erro, alfa de Cronbach |
| `dashboard/graficos.py` | Barras divergentes, funil, mapa de calor, gráfico de efeitos |
| `dashboard/metodologia.md` | Texto da página de metodologia e desvios (editar à mão) |
