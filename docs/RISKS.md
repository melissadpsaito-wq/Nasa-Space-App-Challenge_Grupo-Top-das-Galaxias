# Riscos

| ID | Risco | Prob. | Impacto | Sinal de alerta | Plano B | Dono |
|---|---|---|---|---|---|---|
| R01 | ~~Dados 2026 não chegam~~ | — | — | — | Encerrado por D33 (série termina em dez/2025) | Dados |
| R02 | S-NPP 2012–2024 não baixado | Baixa | Crítico | Sáb 08:00 sem arquivo | Usar NOAA-20 como referência, ponte Aqua→N20 em 2018–2021 | Dados |
| R03 | Calibração ruim (métrica não melhora vs bruto) | Média | Alto | Validação sáb 22:00 | Fator global × mês; declarar limitação | Ciência |
| R04 | AI1 atrasa o núcleo | Média | Médio | Já fora do núcleo (D24) | Só entra se validado até o CP5 (dom 10:00) | Ciência (Samuel) |
| R05 | Deriva de órbita Terra/Aqua distorce pontes | **Confirmada (Aqua 2024–25); limitada** | Baixo para a série do app · Médio para o gráfico dos 4 satélites | **Medido 14/11 18:07 (Brasil, grade 0,02°, M1):** sem degrau em 2020 (S-NPP/Aqua 3,96 em 2012–19 → 3,98 em 2020–21; o salto 5,94 → 7,15 do Pantanal era do bruto, efeito de pixels por fogo em anos de muito fogo). Aqua harmonizado passa o S-NPP em **+15% (2024) e +23% (2025)**: deriva real, coerente com passagem mais tarde, perto do pico diário do fogo. Terra→Aqua diverge depois de 2011 (+15–60%) | Ajuste Aqua→S-NPP em 2012–2019 já fica antes da deriva (D30); série do app usa S-NPP desde fev/2012; Terra só em nov/2000–jun/2002 (baixa confiança, perto da janela 2003–2010). Divergências mostradas e explicadas no gráfico (D34) | Ciência (Melissa) |
| R06 | JSON do app > 5 MB | Baixa | Médio | Tamanho do export | H3 res 3 ou tiles | Dados |
| R07 | Integração Dados × Front trava | Média | Alto | Contrato não congelado às 15:00 (CP1) | Front com dados falsos no formato do contrato | Dados + Front |
| R08 | Demo > 30 s, sem legenda em inglês ou link privado | Baixa | Crítico (desclassifica) | Checklist | Revisão por 2 pessoas + janela anônima | Murilo + Luana |
| R09 | Chave da API vazada no repositório | Baixa | Médio | Revisão de PR | `.env` no `.gitignore`; chave só em GitHub Secrets | Todos — **ocorreu em 13/11 (commit `541c557`): gerar chave nova; ver GOVERNANCE §9** |
| R10 | Cansaço | Alta | Médio | Erros bobos à noite | Dormir ≥ 5 h em turnos (`PLANO-48H.md` §2: 01:30–07:30) | Todos |
| R11 | Murilo sobrecarregado (Dados + Capitão) | Média | Alto | Checkpoint atrasado ou export parado | Vídeo puxado pela Luana; texto do método escrito pela Ciência | Murilo |
| R12 | Melissa e Samuel editam o mesmo código | Média | Médio | Conflito de merge | Interface `Bridge` fixa; cada um em seu módulo e branch | Ciência |
| R13 | Arquivos entre Dados e Ciência fora do contrato | Média | Alto | Ciência não consegue ler o que recebe | Fixar os 3 arquivos do `DATA_DICTIONARY.md` §5 no CP1 (15:00) | Dados + Ciência |
| R14 | Tempo comprimido: construção começa sáb 19:45 (D23) | Alta | Alto | CP2 ou CP3 atrasado > 1 h | Cortes de D24; série nacional vira só áreas prontas (Pantanal + SP); AI1 fora | Murilo |
| R15 | Escopo "agro/previsão" do PDF da equipe volta durante a noite | Média | Alto | Tarefa de previsão ou índice aparece no grupo | D21 e D24: só entra por nova Dxx substituindo item do núcleo | Murilo |
| R16 | Score do app diferente da referência da Ciência | Média | Médio | Casos de `tests/score_cases.json` falham | Luana + Samuel conferem no CP5; o app mostra percentil simples | Luana + Samuel |
| R17 | Juiz pergunta "e o mês atual?" (série termina em 2025) | Média | Médio | Pergunta de mentor no pitch | Responder: score funciona para qualquer mês; NOAA-20 harmonizado prova que a série continua; 2026/NRT é o próximo passo | Murilo |
