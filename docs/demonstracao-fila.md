# Roteiro de demonstração: fila, alternância e concorrência (A-14)

**Meta: 6 minutos.** Ensaie com cronômetro. Tenha o Swagger (`http://localhost:8000/docs`) e um terminal abertos.

## Preparação (antes da apresentação)
```bash
docker compose --env-file backend/.env up -d --build      # banco + API (aplica migrations e seed)
# fora das 07h–17h: EXPEDIENTE_FORCAR_ABERTO=true em backend/.env e `docker compose ... up -d` de novo
```
No Swagger, faça login (`POST /auth/login`) como `atendente1@nassau.local` / `Atendente@123`, copie o token e use **Authorize**. Tenha um segundo token (`atendente2@nassau.local`) à mão. Deixe `GET /painel` aberto em outra aba.

## Roteiro
| Tempo | O que fazer | O que dizer |
|---|---|---|
| 0:00 | Mostrar `docs/models/uml/diagramas.md` §1 | "router → service → repository; todo o SQL fica nos repositórios, parametrizado." |
| 0:30 | `POST /senhas` seis vezes: SG, SE, SP, SG, SE, SP | "Número `YYMMDD-PPSQ`, sequência por tipo reiniciada todo dia. O contador é atômico no banco." Mostrar `GET /fila/resumo`. |
| 1:15 | `POST /guiches/{id}/ocupar` e `POST /atendimentos/chamar-proximo` (iniciar e encerrar entre as chamadas) | "Saiu SP001, SE001, SP002, SE002, SG001, SG002: nunca repete o tipo anterior se houver outro com fila; entre os candidatos, SP > SE > SG." |
| 2:15 | Explicar a consequência | "Com SP e SE sempre disponíveis, a SG só é chamada quando elas esvaziam. É a prioridade funcionando (ADR-003)." |
| 2:30 | Chamar uma senha e tentar `iniciar-atendimento` de uma que ainda aguarda | "Transição inválida dá `409 TRANSICAO_INVALIDA`. A tabela de transições é uma só, usada pelo código e pelos testes." |
| 3:00 | `chamar-novamente` | "`ultima_chamada: true` e o `texto_chamada` que o front usa no áudio e em leitores de tela." Depois `nao-compareceu` → NAO_COMPARECEU / ABANDONO. |
| 3:30 | `GET /painel` | "5 últimas chamadas, mais recente primeiro; nunca a próxima (RN-09)." |
| 3:50 | **Concorrência ao vivo:** `cd backend && python -m tools.simulador --senhas 60 --velocidade 600` | "Três atendentes chamando ao mesmo tempo, 5% não comparecem, tudo pela API." Mostrar o painel mudando. |
| 4:50 | `pytest tests/test_concorrencia.py -v` | "Seis guichês em threads: zero senha repetida e a alternância se mantém, conferida chamada a chamada." |
| 5:20 | Mostrar `chamar_proximo` em `services/atendimento.py` | "A transação trava a linha do dia em `fila_estado` com `FOR UPDATE`: as chamadas viram uma fila de espera, sem ler um 'último tipo' velho." |
| 5:50 | Fechar | "Depois das 17h, a primeira requisição descarta o que sobrou (`FIM_EXPEDIENTE`); está no teste `test_descarte_as_17h_so_pega_quem_aguarda`." |

## Se algo der errado
- **`FORA_DO_EXPEDIENTE`:** falta `EXPEDIENTE_FORCAR_ABERTO=true` na API.
- **Simulador sem guichê livre:** libere os guichês (`POST /guiches/{id}/liberar`) ou reinicie com `docker compose down -v`.
- **Plano B:** rode `pytest tests/test_fluxo.py -v`, que percorre emissão, alternância, estados, painel e descarte.

## Perguntas prováveis na arguição
- **Por que `FOR UPDATE` na linha de `fila_estado` e não só `SKIP LOCKED`?** `SKIP LOCKED` evitaria a senha duplicada, mas dois atendentes leriam o mesmo "último tipo" e poderiam quebrar a alternância. Com o lock na linha do dia as decisões ficam serializadas (ADR-002).
- **O lock não deixa tudo lento?** A seção crítica dura milissegundos e o laboratório tem poucos guichês.
- **E se duas pessoas emitem senha ao mesmo tempo?** O contador usa `INSERT ... ON DUPLICATE KEY UPDATE ultimo_seq = LAST_INSERT_ID(ultimo_seq + 1)`: o banco trava a linha do contador e cada emissão recebe um número diferente. Os `UNIQUE` são a segunda barreira.
- **Por que `READ COMMITTED`?** No padrão (REPEATABLE READ) uma leitura comum poderia usar uma foto antiga do banco e não ver a senha que a chamada anterior acabou de levar. Em `READ COMMITTED`, cada comando vê o que já foi confirmado.
- **Onde está a regra das transições?** `services/estados.py`, tabela `TRANSICOES`; os testes verificam as 9 válidas e as outras 47 combinações como inválidas.
- **Quem pode mexer numa senha chamada?** Só quem a chamou (ou o gestor, como supervisor).
- **Por que o simulador é um cliente da API?** Simular dentro da API com temporizadores seria mais frágil e difícil de testar (ADR-004).
