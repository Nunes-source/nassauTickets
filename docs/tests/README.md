# Testes do nassauTickets — Fase 1

Documentação, scripts e evidências de verificação do protótipo enviado em `nassauTickets-main.zip`.
Os arquivos anteriores do projeto foram preservados. Esta pasta adicional concentra a contribuição dos testadores sem modificar o frontend, o backend, os requisitos ou o README da raiz.

## Testadores responsáveis pelas contribuições

| Nome | Matrícula | Parte preparada |
|---|---|---|
| Gabriel Luann | 01654299 | Plano de testes, testes unitários e relatório unitário |
| Cauã Andrade | 01821096 | Integração, verificação da compilação, pendências e roteiro manual |

Os resultados anexados vêm de execução automatizada assistida em uma cópia do ZIP, em 04/10/2026 no fuso de Brasília (05/10/2026 em UTC). Eles não representam execução pessoal já realizada por cada integrante. Cada testador deve revisar sua contribuição e executar os scripts em sua cópia antes de enviar seu commit.

## Conteúdo

| Arquivo | Finalidade |
|---|---|
| `plano-de-testes.md` | Escopo, critérios, rastreabilidade e limites da verificação |
| `relatorio-gabriel.md` | 16 testes unitários executados |
| `relatorio-caua.md` | 15 testes de integração em DOM simulado e compilação |
| `pendencias.md` | Limitações confirmadas e funcionalidades fora do escopo atual |
| `roteiro-manual.md` | Verificações ainda não executadas em navegador real |
| `scripts/` | Testes executáveis, sem mudar o código da aplicação |
| `evidencias/` | Resultados JSON, compilação e hashes dos arquivos originais |

O professor pede que a documentação fique em `docs/`. Por isso os testes ficam em `docs/tests/`, como extensão da estrutura obrigatória, preservando todas as pastas exigidas.

## Executar os testes

Pré-requisito: Node.js 22 LTS ou compatível. A execução anexada usou Node.js 24.19.0; a mesma execução em Node.js 22 ainda deve ser conferida pela equipe.

Na raiz do repositório, o teste unitário funciona sem dependências adicionais:

```bash
node docs/tests/scripts/unitarios-gabriel.mjs
```

Para integração, instale primeiro as dependências originais do frontend e depois as dependências isoladas dos testes:

```bash
cd frontend
npm ci
cd ../docs/tests
npm ci
npm run test:unit
npm run test:integration
```

O script de integração monta o React em `jsdom`; não precisa iniciar o servidor Vite. O `esbuild` compila os componentes somente para a execução em memória. As dependências dos testes estão no `package.json` desta pasta e não alteram o `package.json` do frontend.

Para conferir a compilação da aplicação:

```bash
cd frontend
npm run build
```

Cada suite imprime JSON e retorna código 1 se uma de suas verificações falhar. As observações em `pendencias` são registradas separadamente: um teste do comportamento simplificado passar não significa que a regra completa do professor tenha sido atendida.

Para produzir novas evidências sem sobrescrever a execução anexada:

```bash
cd docs/tests
mkdir resultados-locais
node scripts/unitarios-gabriel.mjs > resultados-locais/unitarios.json
node scripts/integracao-caua.mjs > resultados-locais/integracao.json
```

`node_modules/` e `resultados-locais/` não devem ser enviados ao Git. Não envie `frontend/dist/`.

## Versionamento

Cada integrante trabalha em uma branch criada a partir de `dev` e abre seu pull request com destino a `dev`. Depois de revisar e integrar as contribuições, o Scrum Master faz o merge de `dev` para `main`, preservando o histórico. O ZIP não contém histórico Git; branches, permissões, participação e merges precisam ser verificados no repositório real.
