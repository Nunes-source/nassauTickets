# Backend (FastAPI + MySQL)

API REST do nassauTickets. Documentação completa no [README da raiz](../README.md); contrato dos endpoints em [`docs/api/contrato-api.md`](../docs/api/contrato-api.md); decisões em [`docs/adr/`](../docs/adr).

```
app/
├── main.py          cria a aplicação (CORS, logs, handlers, routers sob /api/v1)
├── core/            config, db (retry + transação), security (argon2, JWT, perfis), errors, logging, tempo, periodos
├── routers/         só HTTP: valida entrada, chama o service, devolve a resposta
├── services/        regras de negócio
├── repositories/    todo o SQL (sempre parametrizado, sem ORM)
└── schemas/         modelos Pydantic (também geram o Swagger)
database/            schema/*.sql (migrations), migrar.py, seed.py, scripts/ (backup e restauração)
tests/               pytest
tools/               simulador (Dev A)
```

Os routers `senhas.py` e `atendimento.py` (Dev A) entram sozinhos na API quando o arquivo existir: basta exportarem `router`.
