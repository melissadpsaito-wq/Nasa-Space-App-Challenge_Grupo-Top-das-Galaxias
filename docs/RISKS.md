# Riscos

| ID | Risco | Prob. | Impacto | Sinal de alerta | Plano B | Dono |
|---|---|---|---|---|---|---|
| R01 | Dados 2026 (S-NPP jan–out, NOAA-20) não chegam | Média | Alto | Sáb 10:00 sem arquivo | Série até dez/2025 + NRT da API para "este mês" | Dados |
| R02 | S-NPP 2012–2024 não baixado | Baixa | Crítico | Sáb 08:00 sem arquivo | Usar NOAA-20 como referência, ponte Aqua→N20 em 2018–2021 | Dados |
| R03 | Calibração ruim (métrica não melhora vs bruto) | Média | Alto | Validação sáb 22:00 | Fator por bioma × mês; declarar limitação | Ciência |
| R04 | AI1 atrasa o núcleo | Média | Médio | Dom 10:00 sem resultado | Sai do núcleo (D15) | Ciência (Samuel) |
| R05 | Deriva de órbita Terra/Aqua distorce pontes | Média | Médio | Resíduo cresce com o ano | Janelas de ajuste anteriores à deriva | Ciência (Melissa) |
| R06 | JSON do app > 5 MB | Baixa | Médio | Tamanho do export | H3 res 3 ou tiles | Dados |
| R07 | Integração Dados × Front trava | Média | Alto | Contrato não fixado às 10:00 | Front com dados falsos no formato do contrato | Dados + Front |
| R08 | Demo > 30 s, sem legenda em inglês ou link privado | Baixa | Crítico (desclassifica) | Checklist | Revisão por 2 pessoas + janela anônima | Murilo + Luana |
| R09 | Chave da API vazada no repositório | Baixa | Médio | Revisão de PR | `.env` no `.gitignore`; chave só em GitHub Secrets | Todos |
| R10 | Cansaço | Alta | Médio | Erros bobos à noite | Dormir ≥ 5 h na noite de sábado, em turnos | Todos |
| R11 | Murilo sobrecarregado (Dados + Capitão) | Média | Alto | Checkpoint atrasado ou export parado | Vídeo puxado pela Luana; texto do método escrito pela Ciência | Murilo |
| R12 | Melissa e Samuel editam o mesmo código | Média | Médio | Conflito de merge | Interface `Bridge` fixa; cada um em seu módulo e branch | Ciência |
| R13 | Arquivos entre Dados e Ciência fora do contrato | Média | Alto | Ciência não consegue ler o que recebe | Fixar os 3 arquivos do `DATA_DICTIONARY.md` §5 às 10:00 | Dados + Ciência |
