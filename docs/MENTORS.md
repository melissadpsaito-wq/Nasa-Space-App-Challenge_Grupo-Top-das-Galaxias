# Mentores e mudanças de rota

## 1. Como mudar o projeto durante o evento
| Passo | O que fazer | Tempo |
|---|---|---|
| 1 | Quem propõe escreve em 1 linha: **o que muda, por quê, quanto custa (h), o que sai para caber** | 2 min |
| 2 | Capitão decide (ouvindo a equipe, máx. 10 min) | 10 min |
| 3 | Registrar como nova linha em `DECISIONS.md` (Dxx); nunca apagar a antiga | 1 min |
| 4 | Atualizar `ROADMAP.md` e avisar no grupo | 2 min |
Regras: depois do CP3 (sáb 23:30), só entra no núcleo algo que substitua outro item; depois do CP7 (dom 15:00), nenhuma mudança de escopo.

## 2. Quando falar com mentores
Onde: presencialmente no evento de SP ou no **Space Apps Connect** (Local Leads, Navigators, especialistas).
| Quando | Objetivo | Quem vai |
|---|---|---|
| Sáb ~17:00 | Validar o método antes de codar fundo (M2, M3, M5) | Melissa + Samuel |
| Sáb ~22:00 | Mostrar primeiros resultados (razões, validação), se houver mentor | Samuel + Murilo |
| Dom ~11:00 | Testar o pitch, a persona (D20) e a página do projeto | Murilo + Luana |
Abertura de 30 s: "Harmonizamos focos MODIS e VIIRS. Medimos que o S-NPP vê 5,4× mais que o Aqua; ~1/3 é resolução, o resto é sensibilidade. Corrigimos em 3 etapas e validamos fora da amostra. Temos 3 perguntas rápidas."
Regra: perguntas fechadas (sim/não ou A/B), no máximo 3 por conversa.

## 3. Banco de perguntas (com a nossa resposta atual)
### Método
| # | Pergunta | Nossa resposta atual | Decisão ligada |
|---|---|---|---|
| M1 | Série na escala S-NPP (VIIRS-equivalente) ou escala MODIS: qual faz mais sentido para usuários? | S-NPP (maior sobreposição; VIIRS continua) | D03, D11 |
| M2 | Agregar os dois sensores em grade comum de ~2 km por passagem é um jeito válido de remover o efeito de resolução? | Sim: razão estabiliza em 3,45 a partir de ~2 km | D13 |
| M3 | Usar limiar de FRP entre sensores diferentes é aceitável como indicador de sensibilidade? | Sim, calibrado por estação × dia/noite (D33) | D13 |
| M4 | Quais anos evitar por deriva de órbita do Terra e do Aqua? | Terra antes de ~2020, Aqua antes de ~2022 [a confirmar] | Janelas das pontes |
| M5 | Como tratar células onde só o VIIRS detecta (MODIS = 0)? | Termo aditivo por célula × mês | D13 |
| M6 | Validação dividida por ano + erro em log é suficiente? | Sim, mais R², viés e consistência entre os 4 sensores (D33) | C1/AI1 |
| M7 | Falta algum teste de homogeneidade além de Pettitt, KS, pegada e sazonalidade? | — | D12 |
### Dados
| # | Pergunta | Nossa resposta atual |
|---|---|---|
| D1 | O que significa `version` 6.2 (2000) × 61.03 (2024–25) no MODIS do FIRMS? | 61.03 = coleção 6.1, versão 03 [a confirmar] |
| D2 | ~~Melhor via para 2026~~ | Fora por D33 |
| D3 | Qual satélite de referência o INPE usa em cada período? | [a confirmar] |
### Produto e julgamento
| # | Pergunta | Nossa resposta atual |
|---|---|---|
| P1 | Os juízes valorizam mais rigor científico ou produto pronto? | Os dois; núcleo cobre ambos |
| P2 | A história "o S-NPP apagou em 2/11" é um bom gancho? | Sim |
| P3 | Vídeo de 30 s ou 7 slides? | Vídeo |
| P4 | Quantos projetos SP indica ao global e quando é o pitch local? | [perguntar ao Local Lead] |

## 4. Registro das conversas (preencher na hora)
| Hora | Mentor (nome/área) | Pergunta | Resposta | Ação | Dxx |
|---|---|---|---|---|---|
| | | | | | |
Ao final: resumir em 1 frase na submissão ("Method reviewed by Space Apps São Paulo mentors") — item V2.

### Perguntas novas (v2)
| # | Pergunta | Nossa resposta atual | Decisão |
|---|---|---|---|
| P5 | Um coordenador de brigada/Defesa Civil usaria "o fogo está fora do normal, e quando é o pico?" para planejar a temporada? | Sim | D20 |
| P6 | Comparar com o histórico (sem previsão) é suficiente para "antecipar períodos críticos"? | Sim, como climatologia | D21 |
