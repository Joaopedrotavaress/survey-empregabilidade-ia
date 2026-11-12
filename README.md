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
