# Diagramas (Mermaid — o GitHub renderiza direto)

## 1. Arquitetura
```mermaid
flowchart LR
    T[Totem / Painel / Terminal do atendente<br/>React 19] -->|REST JSON /api/v1| R[routers]
    subgraph Back end FastAPI
      R --> S[services<br/>regras de negócio]
      S --> P[repositories<br/>SQL parametrizado]
      R -.-> C[core: config, db, security, errors, tempo]
      S -.-> C
    end
    P --> DB[(MySQL 8.0)]
    SIM[tools/simulador.py] -->|REST| R
```

## 2. Casos de uso
```mermaid
flowchart LR
    AC([Cliente AC]) --- UC01(UC-01 Emitir senha)
    AC --- UC02(UC-02 Consultar painel)
    AA([Atendente AA]) --- UC03(UC-03 Login)
    AA --- UC04(UC-04 Ocupar guichê)
    AA --- UC05(UC-05 Chamar próximo)
    AA --- UC06(UC-06 Chamar novamente)
    AA --- UC07(UC-07 Iniciar atendimento)
    AA --- UC08(UC-08 Encerrar atendimento)
    AA --- UC09(UC-09 Registrar não comparecimento)
    GE([Gestor]) --- UC10(UC-10 Gerenciar usuários e guichês)
    GE --- UC11(UC-11 Relatórios e auditoria)
    GE --- UC12(UC-12 Indicadores)
    AS([Sistema AS]) --- UC14(UC-14 Descartar senhas às 17h)
    AS --- UC13(UC-13 Health check)
```
O GESTOR também executa os casos de uso do atendente.

## 3. Máquina de estados da senha
```mermaid
stateDiagram-v2
    [*] --> EMITIDA: totem emite
    EMITIDA --> AGUARDANDO: sistema (mesma transação)
    AGUARDANDO --> CHAMADA: chamar próximo
    AGUARDANDO --> NAO_COMPARECEU: fim do expediente
    CHAMADA --> CHAMADA_NOVAMENTE: chamar novamente
    CHAMADA --> EM_ATENDIMENTO: iniciar atendimento
    CHAMADA_NOVAMENTE --> EM_ATENDIMENTO: iniciar atendimento
    CHAMADA_NOVAMENTE --> NAO_COMPARECEU: 2ª chamada sem comparecimento
    EM_ATENDIMENTO --> ATENDIDA: encerrar atendimento
    ATENDIDA --> [*]
    NAO_COMPARECEU --> [*]
```
**Tabela de transições (fonte única para o código e os testes):**
| De | Para | Ação | Quem |
|---|---|---|---|
| (nova) | EMITIDA | emitir | TOTEM |
| EMITIDA | AGUARDANDO | concluir emissão | SISTEMA |
| AGUARDANDO | CHAMADA | chamar próximo | ATENDENTE |
| AGUARDANDO | NAO_COMPARECEU (`FIM_EXPEDIENTE`) | descarte às 17h | SISTEMA |
| CHAMADA | CHAMADA_NOVAMENTE | chamar novamente | ATENDENTE |
| CHAMADA | EM_ATENDIMENTO | iniciar | ATENDENTE |
| CHAMADA_NOVAMENTE | EM_ATENDIMENTO | iniciar | ATENDENTE |
| CHAMADA_NOVAMENTE | NAO_COMPARECEU (`ABANDONO`) | não compareceu | ATENDENTE |
| EM_ATENDIMENTO | ATENDIDA | encerrar | ATENDENTE |

Qualquer par fora da tabela → `409 TRANSICAO_INVALIDA`. Toda transição grava uma linha em `senha_historico`.

## 4. Sequência: chamar próximo (concorrência)
```mermaid
sequenceDiagram
    participant A1 as Atendente 1
    participant A2 as Atendente 2
    participant API as API (service fila)
    participant DB as MySQL
    A1->>API: POST /atendimentos/chamar-proximo
    A2->>API: POST /atendimentos/chamar-proximo
    API->>DB: BEGIN; SELECT ultimo_tipo FROM fila_estado FOR UPDATE (A1 obtém o lock)
    Note over API,DB: A2 espera o lock (transação serializada)
    API->>DB: escolher_tipo + SELECT senha aguardando FOR UPDATE
    API->>DB: UPDATE senhas→CHAMADA; INSERT chamadas; INSERT senha_historico; UPDATE fila_estado.ultimo_tipo
    DB-->>API: COMMIT (libera o lock)
    API-->>A1: 200 senha X, guichê 1
    API->>DB: (A2 obtém o lock) escolhe a próxima senha, já sem a X
    DB-->>API: COMMIT
    API-->>A2: 200 senha Y, guichê 2
```

## 5. Sequência: fluxo completo de uma senha
```mermaid
sequenceDiagram
    participant AC as Cliente (totem)
    participant AA as Atendente
    participant API
    participant PN as Painel
    AC->>API: POST /senhas {tipo}
    API-->>AC: 201 261127-SG001 (AGUARDANDO)
    AA->>API: POST /atendimentos/chamar-proximo
    API-->>AA: 200 senha CHAMADA, texto_chamada
    PN->>API: GET /painel (polling)
    API-->>PN: 5 últimas chamadas
    alt cliente comparece
        AA->>API: POST /senhas/{id}/iniciar-atendimento
        AA->>API: POST /senhas/{id}/encerrar-atendimento
        API-->>AA: ATENDIDA
    else não comparece
        AA->>API: POST /senhas/{id}/chamar-novamente (ultima_chamada=true)
        AA->>API: POST /senhas/{id}/nao-compareceu
        API-->>AA: NAO_COMPARECEU
    end
```
