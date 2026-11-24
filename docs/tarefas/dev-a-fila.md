# Dev A — Núcleo da fila

Peça ao Claude Code **uma tarefa por vez**, no formato: *"Leia CLAUDE.md e docs/..., e implemente a tarefa A-03. Não edite arquivos do Dev B."* Cada tarefa termina com testes passando, contrato da API atualizado e commit pequeno em `feat/fila-<descricao>`.

| ID | Fase | Tarefa | Docs de referência | Pronto quando |
|---|---|---|---|---|
| A-01 | 0 | `database/schema/02_fila.sql` | `mer/modelo-dados.md` §4 | aplica sobre o `01_base.sql` sem erro no MySQL 8 |
| A-02 | 0 | `services/estados.py`: tabela de transições e `validar_transicao(de, para)` | `models/uml/diagramas.md` §3 | testes cobrem todas as transições válidas e inválidas |
| A-03 | 0 | `services/fila.py`: `escolher_tipo(ultimo, disponiveis)` | ADR-003 | testes em tabela cobrem todos os casos |
| A-04 | 0 | `services/emissao.py`: `formatar_numero(data, tipo, seq)` e validações | RN-02 | `261127-SP001`; seq > 999 → `SEQUENCIA_ESGOTADA` |
| A-05 | 1 | `repositories/` de senhas, chamadas, atendimentos e fila_estado (SQL parametrizado) | `mer/modelo-dados.md` §5 | nenhum SQL fora de `repositories/` |
| A-06 | 1 | `POST /senhas` (emissão): contador atômico, EMITIDA→AGUARDANDO + histórico, expediente | RF-01 a RF-03 | 201 com número correto; `FORA_DO_EXPEDIENTE` fora do horário |
| A-07 | 1 | `POST /atendimentos/chamar-proximo` com lock | ADR-002, RN-12 | chamada 1 gravada; `FILA_VAZIA`, `ATENDENTE_SEM_GUICHE`, `GUICHE_COM_SENHA_ATIVA` |
| A-08 | 1 | `chamar-novamente`, `iniciar-atendimento` (sorteia `duracao_simulada_seg`), `encerrar-atendimento`, `nao-compareceu` | RF-05 a RF-08, RN-07 | transições inválidas → `409 TRANSICAO_INVALIDA`; histórico gravado |
| A-09 | 1 | `GET /painel` e `GET /fila/resumo` | RF-09, RN-09 | 5 últimas; nunca a próxima |
| A-10 | 1 | Descarte no fim do expediente | ADR-004 | senhas AGUARDANDO viram NAO_COMPARECEU/`FIM_EXPEDIENTE` após 17h |
| A-11 | 2 | `tests/test_concorrencia.py` | ADR-002 | N threads × M senhas, zero duplicidade, alternância mantida |
| A-12 | 2 | `tools/simulador.py` (`--velocidade`, `--senhas`) | ADR-004 | roda um dia inteiro via API e gera dados para relatórios |
| A-13 | 2 | `tests/test_fluxo.py`: emissão → chamada → atendimento → encerramento, e fluxo de não comparecimento | UC-01 a UC-09 | passa do zero com banco limpo |
| A-14 | 3 | Roteiro de demonstração (fila, alternância, concorrência) e seção do README | edital §7 | ensaiado em até 6 min |

**Ponto de atenção:** `usuario_atual()` e a conexão vêm do `core/` do Dev B (ver contrato interno em `00-plano-e-divisao.md`). Até ficarem prontos, use stubs locais e não os commite.
