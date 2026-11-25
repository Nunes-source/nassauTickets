# Requisitos, regras de negócio e casos de uso

Fontes: documento "Sistema para controle de atendimento" (v06, Prof. João Ferreira) e Edital do Projeto Final de Back End Frameworks. Onde as fontes são ambíguas, vale o ADR indicado.

## 1. Agentes
| Sigla | Agente | Papel |
|---|---|---|
| AS | Sistema | Emite senhas, decide a próxima, grava dados, atualiza o painel |
| AA | Atendente | Faz login, ocupa um guichê, chama, inicia e encerra atendimentos |
| AC | Cliente | Anônimo; só interage com o totem (emite senha) e vê o painel |
| GESTOR | Atendente com perfil adicional | Cadastros, relatórios, auditoria e indicadores |

## 2. Requisitos funcionais
| ID | Requisito | Prioridade |
|---|---|---|
| RF-01 | Emitir senha SP, SG ou SE sem login, com número `YYMMDD-PPSQ` | Alta |
| RF-02 | Sequência `SQ` por tipo, 3 dígitos, reiniciada todo dia | Alta |
| RF-03 | Bloquear emissão e chamada fora do expediente (07h–17h) | Alta |
| RF-04 | Chamar próximo respeitando prioridade e alternância (RN-03) | Alta |
| RF-05 | Chamar novamente a senha em CHAMADA, devolvendo `ultima_chamada = true` | Alta |
| RF-06 | Iniciar atendimento da senha chamada | Alta |
| RF-07 | Encerrar atendimento (permitido após 17h se já em curso) | Alta |
| RF-08 | Registrar não comparecimento após a 2ª chamada | Alta |
| RF-09 | Painel com as 5 últimas senhas chamadas, nunca a próxima | Alta |
| RF-10 | Máquina de estados com 7 estados, transições validadas e histórico | Alta |
| RF-11 | Atendente ocupar e liberar um guichê | Alta |
| RF-12 | Login com perfis ATENDENTE e GESTOR | Alta |
| RF-13 | Gestor cadastra usuários e guichês | Média |
| RF-14 | Descartar, no fim do expediente, as senhas que sobraram (RN-10) | Alta |
| RF-15 | Relatórios diário e mensal: (a) emitidas e atendidas em geral, (b) por tipo, (c) detalhado por senha, (d) TM, (e) auditoria | Alta |
| RF-16 | Indicadores de desempenho (ver `02-seguranca-lgpd-disponibilidade.md`) | Média |
| RF-17 | Fornecer dados para o áudio: tipo, sequencial, guichê, última chamada, e `texto_chamada` | Média |
| RF-18 | Health check do back end e do banco | Média |
| RF-19 | Simulador do TM e dos 5% de não comparecimento (ADR-004) | Média |

## 3. Requisitos não funcionais
| ID | Categoria | Requisito |
|---|---|---|
| RNF-01 | Segurança | Senha com hash argon2id; JWT com expiração; acesso por perfil; entrada validada; SQL parametrizado; segredos em `.env` |
| RNF-02 | LGPD | Cliente anônimo (nenhum dado pessoal); dados pessoais só de usuários, mínimos; registro de acesso (`log_acesso`) |
| RNF-03 | Concorrência | Duas chamadas simultâneas nunca recebem a mesma senha (ADR-002) |
| RNF-04 | Desempenho | 95% das requisições em até 500 ms com 6 guichês ativos em ambiente local |
| RNF-05 | Disponibilidade | Falha de banco responde 503 padronizado; `/health`; retry de conexão; backup descrito (`03-...`) |
| RNF-06 | Auditoria | Toda transição de estado e toda chamada ficam registradas com quem, quando e onde |
| RNF-07 | Acessibilidade | A API entrega texto equivalente (`texto_chamada`) e mensagens de erro claras e estáveis para o front tratar leitores de tela e áudio |
| RNF-08 | Manutenibilidade | Camadas router/service/repository; testes automatizados; erros padronizados |
| RNF-09 | Portabilidade | Sobe do zero com Docker Compose e README |
| RNF-10 | Observabilidade | Logs estruturados em JSON com `request_id` |

## 4. Regras de negócio
| ID | Regra |
|---|---|
| RN-01 | Tipos: SP (prioritária), SE (retirada de exames), SG (geral). Prioridade SP > SE > SG |
| RN-02 | Número `YYMMDD-PPSQ`. Exemplo: `261127-SP001` (12 caracteres) |
| RN-03 | Próxima senha: ver ADR-003 (nunca repete o tipo anterior se houver outro disponível; entre os candidatos vale SP > SE > SG) |
| RN-04 | Qualquer guichê atende qualquer tipo |
| RN-05 | Expediente 07:00–17:00 (America/Recife). Fora dele não há emissão nem chamada |
| RN-06 | 1ª chamada (CHAMADA) e 2ª chamada (CHAMADA_NOVAMENTE). Sem comparecimento após a 2ª, a senha vai para NAO_COMPARECEU e o sistema segue |
| RN-07 | TM simulado: SP 15 min ±5 (uniforme 10–20); SG 5 min ±3 (uniforme 2–8); SE 1 min em 95% e 5 min em 5% |
| RN-08 | Cerca de 5% das senhas emitidas não são atendidas (descarte sem atendimento) |
| RN-09 | O painel mostra só as 5 últimas senhas chamadas, nunca a próxima |
| RN-10 | Às 17h, atendimentos em curso podem ser concluídos; senhas que sobraram são descartadas (NAO_COMPARECEU, motivo FIM_EXPEDIENTE) |
| RN-11 | Um atendente ocupa no máximo um guichê; um guichê tem no máximo um atendente |
| RN-12 | Um guichê só chama a próxima se não tiver senha ativa (CHAMADA, CHAMADA_NOVAMENTE ou EM_ATENDIMENTO) |
| RN-13 | Existe um único usuário GESTOR ativo; ele também pode atender (herda ATENDENTE) |
| RN-14 | Transições de estado só pelas regras de `docs/models/uml/diagramas.md`; qualquer outra é rejeitada com 409 |
| RN-15 | Chamar novamente só vale para senha em CHAMADA e só uma vez |

## 5. Casos de uso
| ID | Caso de uso | Ator | Fluxo principal | Exceções |
|---|---|---|---|---|
| UC-01 | Emitir senha | AC | Escolhe o tipo no totem → sistema gera número e grava EMITIDA→AGUARDANDO → devolve a senha | Fora do expediente; banco indisponível |
| UC-02 | Consultar painel | AC | Painel consulta periodicamente → recebe as 5 últimas chamadas | Banco indisponível |
| UC-03 | Fazer login | AA/GESTOR | Envia e-mail e senha → recebe token | Credenciais inválidas; usuário inativo |
| UC-04 | Ocupar guichê | AA | Escolhe um guichê livre → sistema vincula | Guichê ocupado ou inativo |
| UC-05 | Chamar próximo | AA | Sistema escolhe a próxima senha (ADR-003) com lock → registra chamada 1 | Fila vazia; fora do expediente; guichê com senha ativa |
| UC-06 | Chamar novamente | AA | Senha em CHAMADA → registra chamada 2 e `ultima_chamada = true` | Estado inválido |
| UC-07 | Iniciar atendimento | AA | Cliente chegou → EM_ATENDIMENTO, grava início | Estado inválido |
| UC-08 | Encerrar atendimento | AA | EM_ATENDIMENTO → ATENDIDA, grava fim | Estado inválido |
| UC-09 | Registrar não comparecimento | AA | Após a 2ª chamada → NAO_COMPARECEU | Estado inválido |
| UC-10 | Gerenciar usuários e guichês | GESTOR | CRUD com validações | Segundo gestor; e-mail repetido |
| UC-11 | Consultar relatórios | GESTOR | Escolhe período e tipo → recebe dados | Período inválido |
| UC-12 | Consultar indicadores | GESTOR | Informa intervalo → recebe indicadores | Intervalo inválido |
| UC-13 | Verificar saúde do sistema | Todos | `GET /health` | Banco fora → 503 |
| UC-14 | Descartar senhas no fim do expediente | AS | Rotina do sistema às 17h (ou na primeira requisição depois) | — |
