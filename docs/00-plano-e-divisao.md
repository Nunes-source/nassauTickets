# Plano de trabalho e divisão da equipe

**Projeto:** nassauTickets — back end · **Disciplina:** Back End Frameworks (Prof. Eduardo Hernandes), 2026.2
**Devs do back end:** Dev A e Dev B (sugestão: Heitor = A, Nunes = B; podem trocar)
**Apresentação prevista:** 27/11/2026 → **repositório no Teams até 26/11/2026** (use a tag `v1.0-entrega`). Atraso = −10 pontos por dia.

## 0. Antes de tudo: situação da inscrição
O edital fixa a inscrição até 06/11 e diz que equipe não inscrita no prazo não apresenta. Como o grupo teve problema para se inscrever, **avisem o professor hoje** pelo chat do Teams (canal principal) e guardem o print do erro. Sugestão de mensagem:

> Professor, a equipe nassauTickets (6 integrantes) teve problemas técnicos para concluir a inscrição em grupo-hub.vercel.app dentro do prazo. Podemos concluir a inscrição para apresentar em 27/11? Seguem prints do erro.

## 1. Perguntas a confirmar com o professor (Teams)
1. Podemos usar PyMySQL com SQL direto (sem ORM) e scripts `.sql` como migrations?
2. O TM simulado e os 5% de não atendimento podem ficar num **simulador** (`tools/simulador.py`) que usa a API, em vez de dentro da API?
3. Pode existir um único usuário GESTOR que também atende (herda perfil de atendente)?
4. Senhas ainda em AGUARDANDO no fim do expediente podem ir para NAO_COMPARECEU com `motivo_descarte = FIM_EXPEDIENTE`?

Enquanto não houver resposta, seguimos as propostas dos ADRs.

## 2. Divisão do trabalho (metade a metade)

### Dev A — Núcleo da fila (regras de negócio: 20 + 10 + 10 pts)
Emissão e numeração · escolha do próximo (alternância) · concorrência · máquina de estados e histórico · chamar próximo / chamar novamente / iniciar / encerrar / não compareceu · painel · descarte no fim do expediente · simulador · testes da fila.

### Dev B — Base, segurança, relatórios e operação (15 + 10 + 10 + 10 + 10 pts)
Estrutura do projeto e core · schema base · seed · autenticação, perfis, log de acesso (LGPD) · cadastros · relatórios, auditoria e indicadores · health check e recuperação de falhas · Docker Compose · README · CI.

### Dono de cada arquivo
| Área | Dev A | Dev B |
|---|---|---|
| `app/core/*`, `main.py` | — | ✅ |
| `routers/` | `senhas.py`, `atendimento.py` | `auth.py`, `cadastros.py`, `relatorios.py`, `saude.py` |
| `services/` | `emissao.py`, `fila.py`, `estados.py`, `atendimento.py` | `auth.py`, `cadastros.py`, `relatorios.py`, `indicadores.py` |
| `repositories/` | `senhas.py`, `chamadas.py`, `atendimentos.py`, `fila_estado.py` | `usuarios.py`, `guiches.py`, `log_acesso.py`, `relatorios.py` |
| `database/schema/` | `02_fila.sql` | `01_base.sql` |
| `database/` outros | — | `seed.py`, `scripts/backup.sh` |
| `tools/` | `simulador.py` | — |
| `tests/` | `test_fila.py`, `test_estados.py`, `test_concorrencia.py`, `test_fluxo.py` | `test_auth.py`, `test_relatorios.py`, `test_saude.py` |
| Raiz | — | `docker-compose.yml`, `Dockerfile`, `.env.example`, `requirements.txt`, CI |
| `docs/` | `adr/002,003,004`, `models/uml/` (estados, sequência) | `adr/001`, `mer/`, `api/`, `requirements/02` |
| README | seção Fila/Concorrência | resto (consolidação) |

Arquivos compartilhados (`docs/requirements/01`, `docs/api/contrato-api.md`): editar em PR pequeno e avisar o outro.

### O que um entrega ao outro (contrato interno)
O Dev B entrega até **14/11** (Fase 0) estes pontos de integração, que o Dev A usa:
- `core/db.py`: dependência `get_conexao()` (PyMySQL, `DictCursor`, `autocommit=False`, utf8mb4) e `transacao(conn)` (context manager com commit/rollback).
- `core/errors.py`: `ErroNegocio(codigo, mensagem, status=409, detalhes=None)` e handlers globais no formato padrão.
- `core/security.py`: `usuario_atual()` e `exigir_perfil(*perfis)` retornando `UsuarioAtual(id, nome, perfil)`.
- `core/tempo.py`: `agora()`, `hoje()`, `dentro_do_expediente()` (respeita `EXPEDIENTE_*` do `.env`).
- `database/schema/01_base.sql` aplicado e `seed.py` criando atendente, gestor e 3 guichês.

O Dev A entrega ao Dev B (Fase 1): `database/schema/02_fila.sql` e as operações da fila já gravando `chamadas`, `atendimentos` e `senha_historico` conforme `docs/mer/modelo-dados.md`, que são a base dos relatórios.

## 3. Cronograma (hoje 12/11 → entrega 26/11)
| Fase | Datas | Dev A | Dev B |
|---|---|---|---|
| 0 Fundação | 12–14/11 | `02_fila.sql`; funções puras (`escolher_tipo`, formatar número, tabela de transições) + testes unitários | estrutura, core, `01_base.sql`, seed, login/JWT, Docker Compose |
| 1 Núcleo | 15–19/11 | emissão, chamar próximo com lock, chamar novamente, iniciar, encerrar, não compareceu, painel, fim do expediente | cadastros, log de acesso, relatórios (resumo e detalhado) |
| 2 Fechamento | 20–23/11 | teste de concorrência, simulador, teste de fluxo completo | TM, auditoria, indicadores, health e retry, backup, Swagger revisado |
| 3 Entrega | 24–26/11 | roteiro da demonstração (fila e concorrência) | README, máquina limpa, tag `v1.0-entrega`, envio no Teams |

Meta: **código congelado em 24/11**; 25/11 só testes em máquina limpa e ensaio (15 min + 5 de arguição); 26/11 envio de manhã.

## 4. Como usar o Claude Code (e o que o edital exige)
- Abram o Claude Code na **raiz do repositório**; ele lê o `CLAUDE.md` sozinho. Peça **uma tarefa por vez** (as listas em `docs/tarefas/`), leia o diff antes de aceitar e rode `pytest`.
- Commits saem com a **sua** identidade: configure `git config user.name` e `user.email` na sua máquina. O edital exige histórico de commits de todos.
- **Nunca** cole token do GitHub no chat nem em arquivo. Use o login normal do Git na sua máquina.
- O edital permite IA generativa se o grupo **entende e explica todo o código** e **declara o uso no README**. Código que não for explicado na arguição é desconsiderado. Cada um deve conseguir explicar a parte do outro em alto nível.
- Convenções: branches `feat/<area>-<descricao>` a partir da `dev`; PR revisado pelo outro; `main` só no fechamento.

## 5. Estrutura de pastas × edital
O edital sugere `/src`, `/database`, `/tests`. No repositório ficam em `backend/app` (= `/src`), `backend/database` e `backend/tests`; o README explica esse mapeamento.

## 6. Mapa da documentação
- `requirements/01-requisitos.md` — RF, RNF, regras de negócio e casos de uso
- `requirements/02-seguranca-lgpd-disponibilidade.md` — segurança, LGPD, falhas, indicadores
- `mer/modelo-dados.md` — modelo e SQL
- `models/uml/diagramas.md` — arquitetura, casos de uso, estados, sequência
- `api/contrato-api.md` — endpoints e erros
- `adr/` — decisões (stack, concorrência, alternância, simulação e descartes)
- `tarefas/` — tarefas por dev
