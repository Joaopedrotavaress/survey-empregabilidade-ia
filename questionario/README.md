# Questionário: Empregabilidade de devs após a IA generativa

Cópia completa do formulário aplicado no Google Forms, com todas as perguntas, opções de resposta, obrigatoriedade, validações e ramificações (lógica de "ir para a seção").

- Link público do formulário: <https://docs.google.com/forms/d/e/1FAIpQLScepfmDMJDaGNiyeF8wp5CNkzn3BTLCHR5j3icv5k383jeVUg/viewform>
- Estrutura: 9 seções (páginas) e 26 perguntas, 3 delas em grade (12 afirmações no total).
- Extraído diretamente da definição publicada do formulário em 26/11/2026.

Legenda: **(obrigatória)** indica pergunta obrigatória; as demais podem ser puladas. **→** indica para onde o formulário leva o respondente depois daquela resposta. "Enviar formulário" encerra a participação na hora, sem passar pelas outras seções. "Item invertido" é pontuado ao contrário (6 − valor) no dashboard (ver `dashboard/config.py`).

## Fluxo das ramificações

```mermaid
flowchart TD
    S1["1. Termo de consentimento"] -->|Aceito| S2["2. Triagem: 18 anos ou mais?"]
    S1 -->|Não aceito| FIM(["Enviar formulário"])
    S2 -->|Sim| S3["3. Triagem: matriculado(a) na turma?"]
    S2 -->|Não| FIM
    S3 -->|Não| S4["4. Situação atual"]
    S3 -->|Sim| FIM
    S4 -->|CLT, PJ ou freelancer| S6["6. Perfil"]
    S4 -->|Desempregado(a), primeiro emprego ou saiu da área| S5["5. Busca por vaga"]
    S4 -->|Não atua nem busca atuar como dev| FIM
    S5 --> S6
    S6 --> S7["7. Empregabilidade e IA"]
    S7 -->|Trabalhava ou buscava vaga antes de dez/2022: Sim| S8["8. Comparação com antes de 2023"]
    S7 -->|Não| S9["9. Mudanças nas vagas"]
    S8 --> S9
    S9 --> FIM2(["Enviar formulário"])
```

Resumo dos caminhos:

| Grupo | Seções que vê |
|---|---|
| Dentro do mercado (CLT, PJ, freelancer), já atuava antes de dez/2022 | 1, 2, 3, 4, 6, 7, 8, 9 |
| Dentro do mercado, começou depois de dez/2022 | 1, 2, 3, 4, 6, 7, 9 |
| Fora do mercado (desempregado, primeiro emprego, saiu da área), já atuava antes | 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| Fora do mercado, começou depois | 1, 2, 3, 4, 5, 6, 7, 9 |
| Não aceita o termo, menor de 18, matriculado na turma ou não atua/busca atuar como dev | Formulário encerrado na seção em que respondeu |

---

## Seção 1 — Termo de consentimento

> Esta pesquisa faz parte da disciplina Medição e Experimentação em Engenharia de Software, do curso de Pontifícia Universidade Católica de Minas Gerais (PUC Minas) – Engenharia de Software. O objetivo é entender como a empregabilidade percebida de desenvolvedores de software variou após a popularização da IA generativa, comparando quem está dentro e fora do mercado de trabalho.
>
> - A participação é voluntária e sem remuneração. Você pode desistir a qualquer momento antes de enviar.
> - O tempo estimado é de cerca de 10 minutos.
> - O risco é mínimo. As perguntas não essenciais podem ser puladas.
> - A pesquisa é anônima: não coletamos nome, e-mail, telefone, CPF, empresa nem IP. Os dados são usados apenas de forma agregada e para fins acadêmicos.
> - Como as respostas não são identificáveis, uma resposta enviada não pode ser retirada depois.
>
> Dúvidas: arthurbt2005@gmail.com

**1. Você aceita participar desta pesquisa?** (obrigatória) — múltipla escolha
- Li o termo e aceito participar → Seção 2
- Não aceito participar → Enviar formulário

## Seção 2 — Triagem

**2. Você tem 18 anos ou mais?** (obrigatória) — múltipla escolha
- Sim → Seção 3
- Não → Enviar formulário

## Seção 3 — Triagem

**3. Você está matriculado(a) na turma de Medição e Experimentação em Engenharia de Software deste semestre?** (obrigatória) — múltipla escolha
- Não → Seção 4
- Sim → Enviar formulário

## Seção 4 — Situação atual

*Se você tem mais de um vínculo, marque o vínculo principal.*

**4. Qual é a sua situação atual em relação ao desenvolvimento de software?** (obrigatória) — múltipla escolha
- Empregado(a) com carteira assinada (CLT) → Seção 6
- Contrato PJ → Seção 6
- Freelancer ou autônomo(a) → Seção 6
- Desempregado(a), buscando vaga de dev → Seção 5
- Buscando o primeiro emprego como dev → Seção 5
- Saí da área de desenvolvimento → Seção 5
- Não atuo nem busco atuar como dev → Enviar formulário

## Seção 5 — Busca por vaga

Vista apenas por quem está fora do mercado. Depois desta seção, segue para a Seção 6.

**5. Há quantos meses você está buscando vaga como dev?** (obrigatória) — resposta curta
*Conte desde que começou a buscar, mesmo que ainda estivesse empregado(a). Use 0 se for menos de 1 mês.*
Validação: número inteiro ("Digite um número inteiro, por exemplo: 3").

**6. Nos últimos 3 meses, para quantas vagas de dev você se candidatou?** (obrigatória) — resposta curta
*Inclua candidaturas simplificadas (por exemplo, no LinkedIn). Um número aproximado basta.*
Validação: número inteiro.

**7. Nos últimos 3 meses, para quantas entrevistas de vaga de dev você foi chamado(a)?** (obrigatória) — resposta curta
*Um número aproximado basta.*
Validação: número inteiro.

## Seção 6 — Perfil

**8. Quantos anos de experiência profissional como dev você tem?** (obrigatória) — resposta curta
*Conte estágios; arredonde para anos completos. Use 0 se ainda não trabalhou como dev.*
Validação: número inteiro.

**9. Qual é a sua senioridade atual (ou a do seu último cargo)?** (obrigatória) — múltipla escolha
- Ainda não trabalhei como dev
- Estágio ou trainee
- Júnior
- Pleno
- Sênior
- Especialista, tech lead ou acima

**10. Qual é a sua principal área de atuação (atual ou pretendida)?** — múltipla escolha
- Front-end
- Back-end
- Full stack
- Mobile
- Dados, IA ou machine learning
- DevOps, cloud ou SRE
- QA ou testes
- Outra

**11. Qual é o porte da empresa em que você trabalha (ou trabalhou por último)?** — múltipla escolha
- Não se aplica (nunca trabalhei como dev)
- Até 49 pessoas
- 50 a 249 pessoas
- 250 a 999 pessoas
- 1.000 pessoas ou mais

**12. Em que região do Brasil você mora?** — múltipla escolha
- Norte
- Nordeste
- Centro-Oeste
- Sudeste
- Sul

**13. Qual é a sua faixa etária?** — múltipla escolha
- 18 a 24 anos
- 25 a 29 anos
- 30 a 34 anos
- 35 a 44 anos
- 45 anos ou mais

**14. Qual é a sua maior formação concluída ou em andamento?** — múltipla escolha
- Ensino médio
- Curso técnico
- Bootcamp ou curso livre
- Graduação em andamento
- Graduação concluída
- Especialização ou MBA
- Mestrado ou doutorado

**15. Você foi desligado(a) em um layoff (demissão em massa) desde janeiro de 2023?** — múltipla escolha
- Sim
- Não

**16. Onde você ficou sabendo desta pesquisa?** — múltipla escolha
- LinkedIn
- Discord
- Telegram
- WhatsApp
- Reddit
- Indicação de amigo(a) ou colega
- Outro (campo de texto livre)

## Seção 7 — Empregabilidade e IA

*Indique o quanto você concorda com cada afirmação. Exemplo: se você acha que seria fácil conseguir uma vaga igual ou melhor, discorde da última afirmação.*

Escala das grades desta seção (uma resposta por linha, todas as linhas obrigatórias):
Discordo totalmente · Discordo parcialmente · Nem concordo nem discordo · Concordo parcialmente · Concordo totalmente

**17. Sobre a sua empregabilidade hoje:** (obrigatória) — grade de múltipla escolha
1. Se eu precisasse, conseguiria um emprego como dev em pouco tempo.
2. Existem muitas vagas no mercado compatíveis com o meu perfil.
3. Atenção: para confirmar que você está lendo, marque "Discordo parcialmente" nesta linha. *(item de atenção)*
4. Minhas habilidades técnicas são valorizadas pelas empresas que contratam devs.
5. Eu teria dificuldade para conseguir uma vaga igual ou melhor que a atual (ou a última). *(item invertido)*

**18. Sobre o papel da IA no mercado de devs:** (obrigatória) — grade de múltipla escolha
1. A IA generativa é um dos principais fatores das mudanças no mercado de devs.
2. As empresas contratam menos devs porque usam IA para aumentar a produtividade.
3. As mudanças no mercado de devs se devem mais a fatores econômicos do que à IA. *(item invertido)*

**19. Com que frequência você usa assistentes de IA para programar?** (obrigatória) — múltipla escolha
- Nunca
- Raramente (menos de uma vez por semana)
- Algumas vezes por semana
- Diariamente
- Várias vezes ao dia

**20. Como você avalia a sua proficiência no uso de IA para desenvolver?** (obrigatória) — múltipla escolha
- Nenhuma
- Básica
- Intermediária
- Avançada
- Especialista

**21. Consigo usar IA para entregar tarefas mais rápido sem perder qualidade.** (obrigatória) — múltipla escolha
- Discordo totalmente
- Discordo parcialmente
- Nem concordo nem discordo
- Concordo parcialmente
- Concordo totalmente

**22. Você já trabalhava ou buscava vaga de dev antes de dezembro de 2022 (lançamento do ChatGPT)?** (obrigatória) — múltipla escolha
*A busca por estágio conta.*
- Sim → Seção 8
- Não → Seção 9

## Seção 8 — Comparação com antes de 2023

Vista apenas por quem respondeu "Sim" na pergunta 22. Depois desta seção, segue para a Seção 9.

*Compare a situação de hoje com a de antes de 2023, quando a IA generativa se popularizou. Se não conseguir comparar, marque "Não sei avaliar".*

**23. Comparando com antes de 2023:** (obrigatória) — grade de múltipla escolha, uma resposta por linha
Escala: Discordo totalmente · Discordo parcialmente · Nem concordo nem discordo · Concordo parcialmente · Concordo totalmente · Não sei avaliar
1. Ficou mais difícil conseguir entrevistas para o meu perfil.
2. Diminuiu o número de vagas abertas para o meu perfil.
3. Os processos seletivos ficaram mais longos ou mais exigentes.
4. Minhas oportunidades de trabalho aumentaram. *(item invertido)*

**24. Comparada a antes de 2023, a sua empregabilidade hoje está:** (obrigatória) — múltipla escolha
- Muito pior
- Pior
- Igual
- Melhor
- Muito melhor

## Seção 9 — Mudanças nas vagas

Depois desta seção, o formulário é enviado.

**25. Quais destas mudanças você observou em vagas e processos seletivos desde 2023?** (obrigatória) — caixas de seleção
*Marque todas as que se aplicam.*
- Menos vagas para júnior e estágio
- Mais anos de experiência exigidos para o mesmo nível
- Exigência de conhecimento em IA nas vagas
- Processos seletivos com mais etapas ou mais longos
- Testes técnicos mais difíceis
- Salários ofertados menores
- Não observei mudanças

**26. Na sua opinião, qual foi a principal mudança que a IA trouxe para a sua empregabilidade?** — parágrafo
*Opcional. Não cite nomes de pessoas ou empresas.*

---

## Mensagem de confirmação

> Obrigado por participar! Se puder, compartilhe esta pesquisa com outras pessoas que atuam ou buscam atuar como devs. Isso nos ajuda a alcançar mais perfis.
