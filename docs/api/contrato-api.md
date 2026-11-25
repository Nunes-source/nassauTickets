# Contrato da API REST — v1

Base: `/api/v1` · JSON UTF-8 · Swagger em `/docs` e OpenAPI em `/openapi.json` (gerados pelo FastAPI) · Datas em ISO 8601 com fuso (`2026-11-27T09:15:02-03:00`).
Autenticação: cabeçalho `Authorization: Bearer <token>`.

## 1. Formato de erro (único)
```json
{ "codigo": "TRANSICAO_INVALIDA", "mensagem": "A senha não pode ir de AGUARDANDO para ATENDIDA.", "detalhes": {}, "request_id": "b1f4..." }
```
| HTTP | `codigo` | Quando |
|---|---|---|
| 401 | `NAO_AUTENTICADO` | token ausente, inválido ou expirado |
| 401 | `CREDENCIAIS_INVALIDAS` | login errado ou usuário inativo |
| 403 | `SEM_PERMISSAO` | perfil insuficiente |
| 404 | `NAO_ENCONTRADO` | recurso inexistente |
| 404 | `FILA_VAZIA` | chamar próximo sem senha aguardando |
| 409 | `FORA_DO_EXPEDIENTE` | emissão ou chamada fora de 07h–17h |
| 409 | `TRANSICAO_INVALIDA` | estado da senha não permite a ação |
| 409 | `GUICHE_OCUPADO` | guichê com outro atendente |
| 409 | `ATENDENTE_SEM_GUICHE` | chamar sem ter ocupado um guichê |
| 409 | `GUICHE_COM_SENHA_ATIVA` | guichê ainda tem senha em CHAMADA, CHAMADA_NOVAMENTE ou EM_ATENDIMENTO |
| 409 | `GUICHE_INATIVO` | ocupar um guichê desativado |
| 409 | `ATENDENTE_JA_TEM_GUICHE` | atendente tenta ocupar um segundo guichê (`detalhes.guiche` diz qual) |
| 409 | `GESTOR_JA_EXISTE` / `EMAIL_JA_CADASTRADO` / `GUICHE_JA_CADASTRADO` | cadastros |
| 409 | `AUTOALTERACAO_PROIBIDA` | o gestor tenta inativar a si mesmo ou mudar o próprio perfil |
| 409 | `SEQUENCIA_ESGOTADA` | passou de 999 senhas do tipo no dia |
| 422 | `VALIDACAO` | corpo ou parâmetro inválido (lista os campos em `detalhes`) |
| 500 | `ERRO_INTERNO` | falha inesperada (sem detalhes técnicos) |
| 503 | `BANCO_INDISPONIVEL` | banco fora; cabeçalho `Retry-After: 5` |

## 2. Públicos (sem login)
| Método e rota | Uso | Resposta |
|---|---|---|
| `POST /senhas` | Totem emite senha. Corpo `{"tipo":"SP"}` (SP, SG, SE) | `201` `{"id":123,"numero":"261127-SP001","tipo":"SP","sequencial":1,"estado":"AGUARDANDO","emitida_em":"..."}` |
| `GET /painel` | Painel: 5 últimas chamadas, mais recente primeiro | `200` ver abaixo |
| `GET /health` | Saúde (`SELECT 1`, sem retry) | `200` `{"status":"ok","banco":"ok"}` ou `503` `{"status":"degradado","banco":"falha"}` com `Retry-After: 5` |

`GET /painel`:
```json
{ "ultimas": [
    { "numero":"261127-SP001","tipo":"SP","sequencial":1,"guiche":3,
      "chamada":2,"ultima_chamada":true,"chamada_em":"2026-11-27T09:15:02-03:00",
      "texto_chamada":"Última chamada. Senha prioritária zero zero um, guichê três" } ],
  "atualizado_em":"2026-11-27T09:15:04-03:00" }
```
Nunca inclui a próxima senha (RN-09). O front consulta a cada 2–3 s. `texto_chamada` é o mesmo texto de `chamar-proximo`, para o áudio e para leitores de tela.

## 3. Autenticação
| Método e rota | Perfil | Uso |
|---|---|---|
| `POST /auth/login` | público | Corpo `{"email","senha"}` → `{"access_token","token_type":"bearer","expira_em","perfil","nome"}` |
| `GET /auth/me` | logado | `{"id","nome","email","perfil","guiche":{"id","numero"}|null}` |

## 4. Atendente (ATENDENTE ou GESTOR)
| Método e rota | Uso | Observações |
|---|---|---|
| `GET /guiches?livres=true` | Lista guichês | `[{"id":1,"numero":1,"ativo":true,"livre":true,"ocupante":null}]` (`ocupante` = `{"id","nome"}` quando ocupado). `livres=true` traz só os ativos e sem atendente |
| `POST /guiches/{id}/ocupar` | Atendente assume o guichê | `200` com o guichê · `409 GUICHE_OCUPADO` / `GUICHE_INATIVO` / `ATENDENTE_JA_TEM_GUICHE` · repetir no próprio guichê é inofensivo |
| `POST /guiches/{id}/liberar` | Libera o guichê | só o ocupante (ou o gestor) · `409 GUICHE_COM_SENHA_ATIVA` se houver senha ativa |
| `GET /fila/resumo` | Quantidade aguardando por tipo | `{"SP":2,"SE":0,"SG":5}` |
| `POST /atendimentos/chamar-proximo` | RF-04. Estratégia do ADR-002/003 | `200` (abaixo) · `404 FILA_VAZIA` |
| `GET /atendimentos/atual` | Senha ativa (CHAMADA, CHAMADA_NOVAMENTE ou EM_ATENDIMENTO) do guichê do atendente, no formato de `chamar-proximo`, ou `null`. O front usa para retomar o atendimento ao recarregar a página | `200` |
| `POST /senhas/{id}/chamar-novamente` | RF-05. Só de CHAMADA | `200` com `ultima_chamada:true` |
| `POST /senhas/{id}/iniciar-atendimento` | RF-06. De CHAMADA ou CHAMADA_NOVAMENTE | `200` `{"senha":{...},"duracao_simulada_seg":412}` |
| `POST /senhas/{id}/encerrar-atendimento` | RF-07. De EM_ATENDIMENTO | `200` senha ATENDIDA |
| `POST /senhas/{id}/nao-compareceu` | RF-08. Só de CHAMADA_NOVAMENTE | `200` senha NAO_COMPARECEU |

Resposta de chamar (próximo ou novamente):
```json
{ "senha": {"id":123,"numero":"261127-SP001","tipo":"SP","sequencial":1,"estado":"CHAMADA"},
  "guiche": {"id":1,"numero":3},
  "chamada": {"numero":1,"ultima_chamada":false,"chamada_em":"2026-11-27T09:15:02-03:00"},
  "texto_chamada": "Senha prioritária zero zero um, guichê três" }
```
Na segunda chamada: `"ultima_chamada": true` e `"texto_chamada": "Última chamada. Senha prioritária zero zero um, guichê três"`. O front usa `texto_chamada` no áudio e para leitores de tela (RNF-07).
Tipos por extenso: SP "prioritária", SG "geral", SE "exames".

### Regras da fila (como a API se comporta)
- **Emissão** (`POST /senhas`): contador atômico por tipo e dia; EMITIDA → AGUARDANDO e histórico na mesma transação. `409 FORA_DO_EXPEDIENTE` fora de 07h–17h; `409 SEQUENCIA_ESGOTADA` depois da senha 999 do tipo (o contador não avança).
- **Chamar próximo** exige, nesta ordem: expediente (`FORA_DO_EXPEDIENTE`), guichê ocupado (`ATENDENTE_SEM_GUICHE`), guichê sem senha ativa (`GUICHE_COM_SENHA_ATIVA`, RN-12) e senha aguardando (`404 FILA_VAZIA`). As chamadas simultâneas entram em fila num lock (ADR-002) e a alternância segue o ADR-003.
- **Dono da senha:** `chamar-novamente`, `iniciar-atendimento`, `encerrar-atendimento` e `nao-compareceu` só valem para quem chamou a senha (ou o GESTOR, como supervisor); outro atendente recebe `403 SEM_PERMISSAO`. Estado inválido tem prioridade e dá `409 TRANSICAO_INVALIDA` (`detalhes: {"de","para"}`).
- **Depois das 17h** (RN-10): a primeira requisição (de qualquer rota da fila ou do painel) descarta as senhas AGUARDANDO do dia (NAO_COMPARECEU, `FIM_EXPEDIENTE`, origem SISTEMA). Emitir e chamar próximo ficam bloqueados, mas o que já estava em curso termina: `chamar-novamente`, `iniciar-atendimento`, `encerrar-atendimento` e `nao-compareceu` continuam valendo.
- **Respostas:** `iniciar-atendimento` → `{"senha":{id,numero,tipo,sequencial,estado},"duracao_simulada_seg":412}`; `encerrar-atendimento` e `nao-compareceu` → `{id,numero,tipo,sequencial,estado}`; `GET /fila/resumo` → `{"SP":2,"SE":0,"SG":5}`.
- **`texto_chamada`:** tipo por extenso, sequencial dígito a dígito e guichê por extenso (`Senha exames zero quatro zero, guichê doze`); na 2ª chamada começa com `Última chamada.`
- **Demonstração fora do horário:** `EXPEDIENTE_FORCAR_ABERTO=true` na API ignora o expediente (nunca em produção).

## 5. Gestor (somente GESTOR)
| Método e rota | Uso |
|---|---|
| `POST /usuarios` · `GET /usuarios` · `PATCH /usuarios/{id}` | Cadastro (inclui inativar). Corpo do POST: `nome`, `email`, `senha` (mín. 8), `perfil`. O PATCH aceita só os campos a mudar (`nome`, `email`, `senha`, `perfil`, `ativo`); inativar libera o guichê do usuário. Resposta: `{"id","nome","email","perfil","ativo"}` (nunca o hash) |
| `POST /guiches` · `PATCH /guiches/{id}` | Cadastro (`{"numero":4}`) e ativação (`{"ativo":false}`; não desativa guichê ocupado) |
| `GET /relatorios/{periodo}/{tipo}` | Relatórios (abaixo) |
| `GET /indicadores?de=YYYY-MM-DD&ate=YYYY-MM-DD` | Indicadores (RF-16) |

### Relatórios: `GET /relatorios/{periodo}/{tipo}`
- `periodo`: `diario` (`?data=2026-11-27`) ou `mensal` (`?ano=2026&mes=11`).
- `tipo`: `resumo`, `senhas`, `tm` ou `auditoria`. Para `senhas` e `auditoria`: `?pagina=1&tamanho=50`.

**`resumo`** (RF-15 a, b):
```json
{ "periodo":"2026-11-27","emitidas_total":120,"atendidas_total":98,"nao_compareceu_total":22,
  "por_tipo":{"SP":{"emitidas":20,"atendidas":18},"SE":{"emitidas":40,"atendidas":38},"SG":{"emitidas":60,"atendidas":42}} }
```
**`senhas`** (RF-15 c): `{"periodo","pagina","tamanho","total","itens":[...]}`; cada item é `{numero,tipo,emitida_em,atendimento_inicio,atendimento_fim,guiche}`; campos de atendimento e guichê `null` se não atendida. Ordenado por emissão.
**`tm`** (RF-15 d): `{"periodo","por_tipo":{"SP":{quantidade, tm_simulado_medio_seg, tm_real_medio_seg}, ...}}` (médias em segundos inteiros, `null` sem dados; o TM varia por sorteio, então muda a cada dia).
**`auditoria`** (RF-15 e): mesmo envelope paginado de `senhas`; cada item é `{atendente,guiche,senha,primeira_chamada_em,segunda_chamada_em|null,inicio_atendimento_em|null,fim_atendimento_em|null}`; uma linha por senha chamada, inclui as NAO_COMPARECEU (sem início e fim). Atendente e guichê são os da 1ª chamada. Senhas descartadas sem nunca terem sido chamadas (ex.: FIM_EXPEDIENTE) não aparecem aqui.
Período inválido (mês 13, intervalo invertido, mais de 366 dias) → `422 VALIDACAO`.

### `indicadores`
```json
{ "de":"2026-11-27","ate":"2026-11-27",
  "tempo_medio_espera_seg":{"SP":120,"SE":300,"SG":900},
  "tempo_medio_atendimento_seg":{"SP":890,"SE":75,"SG":310},
  "taxa_nao_comparecimento":0.05,
  "atendimentos_por_guiche":[{"guiche":1,"quantidade":40}],
  "atendimentos_por_atendente":[{"atendente":"Atendente 1","quantidade":40}],
  "vazao_por_hora":9.8 }
```
Médias em segundos inteiros (`null` sem dados). `taxa_nao_comparecimento` conta só `ABANDONO` (não `FIM_EXPEDIENTE`) ÷ emitidas. `vazao_por_hora` = atendimentos concluídos ÷ (horas de expediente × dias do intervalo). Sem `de`/`ate` o padrão é hoje; máximo de 366 dias.

## 6. Cabeçalhos
Toda resposta traz `X-Request-ID` (o mesmo `request_id` dos erros). Respostas 503 trazem `Retry-After: 5`. Rotas autenticadas: `Authorization: Bearer <token>`.

## 7. Versionamento e boas práticas
Prefixo `/api/v1`; mudanças incompatíveis viram `/api/v2`. Rotas em português, substantivos no plural, ações como sub-recurso (`/senhas/{id}/iniciar-atendimento`). Toda rota autenticada grava em `log_acesso`.
