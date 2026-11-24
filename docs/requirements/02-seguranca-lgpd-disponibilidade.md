# Segurança, LGPD, disponibilidade e indicadores

## 1. Segurança (OWASP)
| Tema | Decisão |
|---|---|
| Senhas | argon2id (`argon2-cffi`); nunca logar nem devolver o hash |
| Autenticação | Login por e-mail e senha → JWT HS256 (`PyJWT`), expiração `JWT_EXPIRA_MIN` (padrão 480 min = turno) |
| Autorização | `exigir_perfil("ATENDENTE","GESTOR")` e `exigir_perfil("GESTOR")` por rota. GESTOR herda ATENDENTE |
| Injeção | SQL sempre parametrizado (`%s`); validação de entrada com Pydantic (tipos, tamanhos, enums) |
| Segredos | `.env` fora do Git; `.env.example` só com nomes. Segredos do JWT e do banco nunca no código |
| CORS | Restrito a `CORS_ORIGENS` |
| Força bruta | Mensagem única "credenciais inválidas"; bloqueio temporário após 5 falhas seguidas por e-mail (se der tempo) |
| Erros | Nunca expor stack trace; erro interno responde 500 genérico com `request_id` |
| Dependências | Versões fixas em `requirements.txt` |

Rotas públicas (sem login): `POST /senhas`, `GET /painel`, `GET /health`. Todo o resto exige token.

## 2. LGPD
- **Minimização:** a senha do cliente é anônima: nenhum nome, CPF ou contato. O sistema não identifica o cliente.
- **Dados pessoais tratados:** apenas nome e e-mail de atendentes e do gestor, para autenticar e auditar o trabalho.
- **Finalidade:** controle de atendimento e auditoria operacional; não se usa para outro fim.
- **Registro de acesso:** `log_acesso` guarda usuário, ação, recurso, IP, resultado e data; não guarda senha nem token.
- **Retenção:** definir prazo para `log_acesso` e relatórios (sugestão: 6 meses para logs). Confirmar com o professor.
- **Direitos do titular:** o gestor corrige e inativa usuários; inativar mantém o histórico de auditoria sem expor dados desnecessários.
- **Segurança:** hash de senha, perfis, HTTPS recomendado em produção (fora do escopo da demonstração local).

## 3. Disponibilidade e recuperação de desastres
| Cenário | Comportamento do back end | O que o front exibe |
|---|---|---|
| Banco fora do ar | 503 `BANCO_INDISPONIVEL` com `Retry-After: 5`; 3 tentativas de conexão com espera 0,2 s / 0,5 s / 1 s | **Painel:** mantém a última lista com aviso "Reconectando…" e tenta de novo a cada 5 s. **Totem:** desabilita a emissão e mostra "Sistema indisponível, procure a recepção". **Atendente:** faixa de aviso e ações bloqueadas até voltar |
| Back end fora do ar | Sem resposta (timeout no front) | Mesmo comportamento do banco indisponível |
| Falha no meio de uma operação da fila | Rollback da transação; nada fica pela metade; resposta 503/500 padronizada | Atendente pode repetir a ação (as operações validam o estado antes de agir) |
| Health check | `GET /api/v1/health` → `{status, banco}`; 200 se o banco responde (`SELECT 1`), 503 caso contrário | — |
| Backup | `mysqldump` diário (`database/scripts/backup.sh`), retenção 7 dias, teste de restauração no README | — |
| Metas | RPO: 24 h (menor se houver binlog); RTO: 30 min | — |

## 4. Indicadores de desempenho (RF-16)
| Indicador | Definição |
|---|---|
| Tempo médio de espera | média de (1ª chamada − emissão), por tipo |
| Tempo médio de atendimento | média de (fim − início), por tipo, comparado ao TM simulado |
| Taxa de não comparecimento | NAO_COMPARECEU com motivo ABANDONO ÷ senhas emitidas |
| Atendimentos por guichê | quantidade de ATENDIDA por guichê |
| Atendimentos por atendente | quantidade de ATENDIDA por usuário |
| Vazão por hora | atendimentos concluídos por hora de expediente |

## 5. Observabilidade
Logs em JSON (nível, mensagem, `request_id`, rota, status, duração). O `request_id` volta no cabeçalho `X-Request-ID` e nos erros.
