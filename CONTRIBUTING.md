# Como contribuir

## Branches
- `main`: sempre funcionando; é o que o deploy publica.
- `dados/<tema>`, `front/<tema>`, `ciencia/<tema>`: uma branch por tarefa.
- A partir de dom 13:00 (congelamento): só branches `fix/<tema>`.

## Commits
Formato: `<área>: <o que mudou>` — ex.: `dados: agrega focos em H3 res 4`, `front: calendário com cividis`.
Código gerado ou sugerido por IA: acrescentar a linha `AI-assisted: Claude` no corpo do commit e registrar em `docs/AI_USAGE.md`.

## Pull requests
- Todo merge em `main` passa por PR com 1 revisão de outro membro.
- Revisão rápida (≤ 10 min): roda? quebra o contrato de dados? tem segredo no código?
- Usar o template `.github/PULL_REQUEST_TEMPLATE.md`.

## Definição de pronto
1. Roda na máquina de outra pessoa (ou no deploy).
2. Não quebra o contrato de `docs/DATA_DICTIONARY.md`.
3. Testes mínimos passam (`make test` quando existir).
4. Uso de IA registrado, se houve.
5. Tarefa marcada em `docs/ROADMAP.md` / issue fechada.

## Proibido no repositório
- `.env`, `MAP_KEY` ou qualquer chave.
- Dados brutos (`data/raw/`, ZIPs): ficam no Drive da equipe.
- Arquivos > 50 MB.
