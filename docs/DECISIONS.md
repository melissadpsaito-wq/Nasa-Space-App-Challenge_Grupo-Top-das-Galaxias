# Registro de decisões

Regra: Claude propõe; o Capitão decide. Toda decisão que muda escopo, método, dados ou prazo entra aqui.
Status: proposta · decidida · revertida. Nova decisão: próximo ID, uma linha, nunca apagar linhas antigas (reverter com nova decisão).

| ID | Data | Decisão | Motivo | Dono | Status |
|---|---|---|---|---|---|
| D01 | 13/11 | Desafio: Harmonization of MODIS and VIIRS Hot Spots | Dados prontos, desafio viável em 48 h | Equipe | decidida |
| D02 | 13/11 | Equipe de 3; fora do escopo: comparar duas áreas | Capacidade | Murilo | decidida (Terra e NOAA-20 revistos por D10/D11) |
| D03 | 13/11 | Unidade da série: focos VIIRS-equivalentes (escala S-NPP) | S-NPP tem a maior sobreposição com MODIS | Murilo | proposta |
| D04 | 13/11 | Grade H3 res 4, agregação mensal para o app | Detalhe × tamanho no navegador | Dados | proposta |
| D05 | 13/11 | App estático, sem backend | Nada cai na demo | Front | proposta |
| D06 | 13/11 | Piloto Pantanal 2020 | Caso brasileiro forte | Murilo | proposta |
| D07 | 13/11 | Envio interno dom 20:00; congelamento dom 13:00 | 4 h de folga | Murilo | decidida |
| D08 | 13/11 | Manter tese de "25 anos" | Força da narrativa | Murilo | decidida (ver D10) |
| D09 | 13/11 | Brasil + vizinhos; prioridade Bolívia e Paraguai | Pantanal cruza fronteira | Dados | decidida |
| D10 | 13/11 | Terra nov/2000–jun/2002 via ponte Terra→Aqua, marcado "baixa confiança"; senão "~24 anos" | Sustentar D08 com validade | Murilo | proposta |
| D11 | 13/11 | S-NPP parou em 02/11/2026; continuidade com NOAA-20 convertido para escala S-NPP (sobreposição 2018–2025) | NRT só existe via NOAA-20/21 | Murilo | proposta |
| D12 | 13/11 | C1 = bateria de testes de homogeneidade (Pettitt, KS no FRP, pegada espacial, sazonalidade) nas trocas de satélite | Prova objetiva; cobre mudança de método de coleta | Murilo | decidida |
| D13 | 13/11 | C2 = harmonização física em 3 etapas: grade comum ~2 km por passagem → limiar FRP por bioma × estação × dia/noite → resíduo por célula × mês com termo aditivo | Razão estabiliza em ~3,45 a partir de ~2 km | Murilo | decidida |
| D14 | 13/11 | Subdivisão por pegada (375 m) não adotada no núcleo; possível M4 experimental | Inverte o viés (S-NPP/Aqua = 0,55) | Murilo | decidida |
| D15 | 13/11 | Escopo final (núcleo / se der tempo / bônus) conforme `GOVERNANCE.md` §4 | Discussão do grupo com notas por ideia | Equipe | decidida |
| D16 | 13/11 | Equipe de 4: Melissa e Samuel assumem o método (Ciência); Murilo assume Dados e mantém o papel de Capitão; Luana no Front. Atualiza `GOVERNANCE.md` §1 e o checklist (4 membros) | Divisão do Guia de Execução 48h | Murilo | proposta |
| D38 | 14/11 | **Tiles do app fora do Git até o export final.** Export 2.4 em tiles por célula-pai H3 res 2 (`app/public/data/harm_<pai>.json`, R06 acionado). Os tiles (`harm_82*.json`) entram no `.gitignore` e vão para a Luana pelo Drive (zip) a cada export provisório (CP3, CP4); só o export final de domingo (antes do CP7) é commitado, uma vez, retirando a linha do `.gitignore`. Código (`pipeline/export.py`, testes) segue no Git normalmente | Export res 5 = 128 tiles, máx 1,35 MB, **total 101 MB**; commitar cada reexport somaria ~100 MB ao histórico por vez (~300 MB até domingo). Alternativa descartada: commitar a cada export | Murilo | decidida (14/11 22:47) |
