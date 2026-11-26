### Desenho do estudo

Survey transversal, autoaplicado pelo Google Forms, sem coleta de nome, e-mail ou IP, seguindo o protocolo
pré-registrado (pasta `protocolo/`). População-alvo: pessoas com 18 anos ou mais que atuam ou buscam atuar como
devs no Brasil, em dois estratos: dentro do mercado (CLT, PJ, freelancer) e fora (desempregadas, em busca do
1º emprego ou que saíram da área). Amostragem não probabilística, por conveniência e bola de neve. O estudo mede
percepção, não causalidade.

### Desvios em relação ao protocolo

| # | O que foi planejado | O que aconteceu | Por quê | Impacto |
| --- | --- | --- | --- | --- |
| 1 | Commit do protocolo no repositório antes da primeira resposta, como prova de data | O protocolo foi entregue na Parte 1 da disciplina; o arquivo foi adicionado ao repositório depois do início da coleta | O registro foi feito pela entrega da Parte 1, e não pelo commit | A anterioridade do protocolo é comprovada pela data de entrega da Parte 1 |
| 2 | Coleta de 17/11 a 07/12/2026 | A primeira resposta chegou em 25/11 (ver tabela acima) | A divulgação começou depois do previsto | Janela de coleta mais curta, com menos tempo para lembretes e para reforçar canais |
| 3 | Divulgação em LinkedIn, Discord, Telegram, WhatsApp e Reddit, com grupos de vagas e bootcamps para garantir o estrato "fora" | Quase todas as respostas vieram de WhatsApp e indicação de conhecidos; nenhuma de Discord, Telegram ou Reddit | O convite circulou sobretudo nas redes pessoais dos integrantes | Amostra concentrada nas redes do grupo (autosseleção); a comparação por canal (S3) fica limitada |
| 4 | Pelo menos 20 respostas "fora" e 30 "dentro" | O estrato "fora" ficou abaixo da meta (ver tabela acima) | Os canais de vagas e bootcamps, que trariam esse estrato, quase não foram usados | Menor poder nos testes dentro × fora (o protocolo já previa detectar só efeitos grandes) e margem de erro maior para esse estrato |
| 5 | Análise em Python com pandas, SciPy e pingouin | Análise em pandas e SciPy, com Dunn, Wilson, Newcombe, δ de Cliff e alfa implementados no código do dashboard | Menos dependências para rodar o dashboard | Nenhum: os testes e tamanhos de efeito são os do plano |
| 6 | D5: duplicatas com "horários próximos"; Fisher quando o esperado é menor que 5 | D5 operacionalizado como respostas idênticas com até 60 min de diferença; em tabelas maiores que 2×2, Fisher por Monte Carlo (10.000 permutações) | O protocolo não fixava a janela nem o método para tabelas maiores | Critérios explícitos e reprodutíveis |
| 7 | Alfa de Cronbach ≥ 0,70; abaixo disso, o item de pior correlação item-total pode sair | AIA ficou abaixo da meta (ver página Confiabilidade); os índices usam os 3 itens | Decisão do grupo de manter o construto como planejado | Ler AIA com cautela; a página Confiabilidade mostra o alfa sem o item |

Análises fora do plano (página Explorar cruzamentos) são exploratórias e não entram nas famílias de Holm.

### Limitações e ameaças à validade

- **Autosseleção e não resposta.** Não sabemos quantas pessoas receberam o convite, então não dá para calcular a
  taxa de resposta. Quem se sente mais afetado pelo mercado pode ter respondido mais.
- **Amostra de conveniência.** As margens de erro supõem amostragem aleatória; aqui elas cobrem só o erro
  aleatório, e as conclusões valem para os respondentes.
- **Divulgação por conhecidos.** Parte das respostas veio de pessoas próximas aos integrantes, o que pode
  inclinar as respostas; textos com nomes de pessoas foram retirados antes da análise, sem excluir a resposta.
- **Desejabilidade social.** Empregabilidade e proficiência em IA podem ser superestimadas. Mitigação:
  anonimato explícito e itens reversos.
- **Viés de memória.** VPE e G1 comparam com antes de 2023 e dependem da lembrança; por isso só quem respondeu
  F1 = Sim vê essas perguntas, e há a opção "Não sei avaliar".
- **Subgrupos pequenos.** O estrato "fora" e as senioridades pleno e sênior têm poucas respostas; os testes
  desses recortes são frágeis e aparecem sinalizados.
- **Confusão de causas.** Juros e cortes pós-2022 também afetam o mercado; AIA3 capta a explicação econômica,
  mas o survey não permite concluir que a IA causou as mudanças.
