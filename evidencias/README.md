# Evidências da coleta

Registros digitais da aplicação do survey, conforme exigido na entrega:

| Evidência exigida | Onde está |
|---|---|
| Capturas datadas dos canais de divulgação | As três imagens `.jpg` desta pasta, as cinco capturas `divulgacao_whatsapp_*.png` (seção abaixo) e a planilha [`controle_divulgacao.csv`](controle_divulgacao.csv) |
| Exportação bruta do formulário, com data e hora de cada resposta | [`../dados/`](../dados/) (CSV exportado do Google Forms, coluna "Carimbo de data/hora") |
| Acesso ao painel do formulário | Mostrado ao vivo durante a apresentação (aba "Respostas" do Google Forms) |

## Divulgação

| ID | Data e hora da publicação | Canal | Captura |
|---|---|---|---|
| D1 | 17:00, antes de 26/11/2026 (o separador de data não aparece na captura) | WhatsApp, grupo de colegas (Grupo A) | [whatsapp_grupo_A_captura_2026-11-26_1147.jpg](whatsapp_grupo_A_captura_2026-11-26_1147.jpg) |
| D2 | 25/11/2026, 16:2x | WhatsApp, grupo de colegas (Grupo B) | [whatsapp_grupo_B_captura_2026-11-26_1147.jpg](whatsapp_grupo_B_captura_2026-11-26_1147.jpg) |
| D3 | 25/11/2026, 16:02 | Google Chat, grupo de trabalho (Grupo C) | [google_chat_grupo_C_captura_2026-11-26.jpg](google_chat_grupo_C_captura_2026-11-26.jpg) |

As capturas foram feitas em 26/11/2026. Nelas, "Ontem" corresponde a 25/11/2026. O horário da captura aparece na barra de status das capturas do celular (11:47).

### Capturas adicionais do WhatsApp (26/11/2026)

Convites enviados em conversas e no grupo de devs, a maioria por volta das 08:36, e lembretes individuais.
As capturas mostram só "Hoje" e o horário; a data de cada resposta está em
[`../dados/respostas_brutas.csv`](../dados/respostas_brutas.csv).

| Arquivo | O que mostra |
|---|---|
| `divulgacao_whatsapp_1.png` a `3.png` | Convite com o link do formulário enviado em conversas, 08:36 |
| `divulgacao_whatsapp_4.png` | Convite no grupo de devs e resposta "Respondido" |
| `divulgacao_whatsapp_5.png` | Lembrete individual a um contato |

## Proteção de dados

Nenhuma evidência expõe dados pessoais de respondentes ou de terceiros. Nas capturas, ficaram cobertos por tarjas:

- nome, foto e lista de membros de cada grupo;
- mensagens, nomes e fotos de outras pessoas.

Ficaram visíveis somente a mensagem de divulgação enviada pela equipe, a data e a hora.

Os arquivos originais, sem as tarjas, não estão no repositório.

**Exceção:** as capturas `divulgacao_whatsapp_*.png` foram adicionadas sem tarjas. A `4` mostra nomes de membros do
grupo e uma mensagem de outra pessoa; a `5` mostra o nome e o telefone de um contato. Cubra esses dados antes de
compartilhar o repositório fora do grupo.
