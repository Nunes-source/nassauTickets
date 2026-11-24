# CLAUDE.md — nassauTickets (back end)

Leia este arquivo antes de qualquer tarefa. A documentação completa está em `docs/`; em caso de dúvida, ela manda.

## Projeto
Back end do Sistema de Controle de Atendimento de um Laboratório de Análises Clínicas (UNINASSAU, Back End Frameworks 2026.2). Fontes das regras: `docs/requirements/` (baseado no documento de requisitos v06 e no Edital do Projeto Final).

## Stack (decisão em `docs/adr/001-stack.md`)
Python 3.14 · FastAPI · MySQL 8.0 · PyMySQL com **SQL direto (sem ORM)** · argon2-cffi · PyJWT · pytest · Docker Compose.

## Estrutura
```
backend/
├── app/
│   ├── main.py
│   ├── core/          config, db, security, errors, logging, tempo
│   ├── routers/       só HTTP: valida entrada, chama service, devolve resposta
│   ├── services/      regras de negócio (fila, estados, relatórios...)
│   ├── repositories/  todas as queries SQL (sempre parametrizadas)
│   └── schemas/       modelos Pydantic de entrada e saída
├── database/          schema/01_base.sql, schema/02_fila.sql, seed.py, scripts/
├── tests/
├── tools/simulador.py
├── requirements.txt
└── .env.example
docker-compose.yml     (raiz)
```

## Regras de código
- Camadas: router → service → repository. **Nenhuma regra de negócio em router. Nenhum SQL fora de repository.**
- Nomes de domínio em português sem acento (`senha`, `guiche`, `atendimento`, `chamar_proximo`). Termos de framework em inglês. Valores técnicos sem acento: `NAO_COMPARECEU`.
- SQL sempre parametrizado (`%s`). Nunca concatenar texto em query.
- Transação explícita nas operações da fila (ver `docs/adr/002-concorrencia.md`).
- Erros de negócio: `raise ErroNegocio(codigo, mensagem, status)`; formato único em `docs/api/contrato-api.md`.
- Horários sempre via `core/tempo.py` (`agora()`, `hoje()`), fuso America/Recife. Nunca `datetime.now()` solto.
- Segredos só em `.env` (nunca versionado). Manter `.env.example` atualizado.
- Todo endpoint novo entra no contrato da API e tem teste.

## Git
- Trabalhar sempre em `feat/<area>-<descricao>` criada a partir da `dev`; PR para `dev`, revisado pela outra pessoa. `main` só recebe merge da `dev`.
- Commits pequenos com prefixo `feat:`, `fix:`, `docs:`, `chore:`, `test:`.
- **Nunca** force push, reescrever histórico público nem commitar token, senha real ou `.env`.
- Cada integrante commita com a própria identidade (`git config user.name/email`).
- README só pode listar como pronto (✅) o que está implementado e testado.

## Dono de cada área (evitar conflito de merge)
Veja `docs/00-plano-e-divisao.md`. Não edite arquivos da área da outra pessoa sem combinar.

## Comandos
```
cp backend/.env.example backend/.env          # uma vez; troque as senhas
docker compose --env-file backend/.env up -d db
cd backend && pip install -r requirements.txt
python -m database.seed                        # aplica database/schema/*.sql e cria o seed
uvicorn app.main:app --reload                  # Swagger em http://localhost:8000/docs
pytest                                         # sem MySQL, os testes de banco são pulados
```
Tudo junto (banco + API): `docker compose --env-file backend/.env up -d --build`.

## Antes de dar uma tarefa por concluída
1. Testes passando. 2. Contrato da API atualizado. 3. Nada de segredo no diff. 4. Quem fez consegue explicar cada linha (o edital desconta código que a equipe não explica na arguição).
