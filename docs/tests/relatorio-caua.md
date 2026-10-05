# Relatório de testes de integração e organização

**Projeto:** nassauTickets — Fase 1  
**Responsável pela contribuição:** Cauã Andrade — 01821096  
**Origem examinada:** nassauTickets-main.zip  
**Execução:** automatizada assistida, 04/10/2026 (Brasília)  
**Ambiente:** Node.js 24.19.0, React instalado pelo lockfile original, jsdom 26.1.0, esbuild 0.27.4.  
**Método:** montagem do App real em DOM simulado, interação com componentes e consulta ao DOM resultante.

## Resultado da integração

**15 verificações executadas: 15 aprovadas e 0 reprovadas.**

| ID | Verificação executada | Resultado |
|---|---|---|
| I01 | Totem inicia vazio com SP, SG e SE | APROVADO |
| I02 | Emissão sequencial e contadores independentes por tipo | APROVADO |
| I03 | Senha emitida aparece na fila ao navegar | APROVADO |
| I04 | Chamada remove a senha da fila e registra guichê 2 no painel | APROVADO |
| I05 | Regra simplificada escolhe SP na fila mista | APROVADO |
| I06 | Sem SP, SE é escolhida antes de SG | APROVADO |
| I07 | Somente SG: ordem de chegada é mantida | APROVADO |
| I08 | Botão de chamada desabilitado em fila vazia | APROVADO |
| I09 | Painel não antecipa senha emitida ainda não chamada | APROVADO |
| I10 | Painel limita sete chamadas às cinco mais recentes | APROVADO |
| I11 | Navegação entre telas conserva a fila em memória | APROVADO |
| I12 | Cada guichê disponível chama cada tipo de senha | APROVADO |
| I13 | Atendente mostra a última chamada do guichê selecionado | APROVADO |
| I14 | Hash inválido abre Totem | APROVADO |
| I15 | Menu marca a tela atual e rótulo do guichê está presente | APROVADO |

I12 cobre as nove combinações possíveis entre três guichês e três tipos de senha. Cada combinação é executada isoladamente. Isso não simula nove clientes ou atendentes concorrentes.

## Compilação

`npm ci` instalou as dependências do frontend e `npm run build` terminou com código 0. Foram transformados 36 módulos. A saída da compilação está em `evidencias/build-frontend.txt`.

## Organização verificada por inspeção do ZIP

| Item | Resultado observado |
|---|---|
| `backend/` e `frontend/` | Presentes |
| `docs/branding/`, `docs/mer/`, `docs/mockups/` | Presentes e com arquivos |
| `docs/models/uml/` e `docs/requirements/` | Presentes e com arquivos |
| `.gitignore` na raiz | Presente, incluindo exclusão de `node_modules/` |
| `LICENSE` | Presente com licença MIT |
| `README.md` | Presente, descreve escopo, tecnologias, execução e branches |
| Seção `## Membros` | Presente com nomes, matrículas e papéis; Gabriel e Cauã como testadores |
| Frontend em React | Presente, com componentes, estado, props, eventos e efeitos |
| Diretórios vazios | Os diretórios exigidos possuem arquivos; `.gitkeep` não é necessário neles |
| Branches `dev`/`main` e merges | Não verificáveis no ZIP; conferir no GitHub |
| Repositório público e acesso dos integrantes | Não verificáveis no ZIP; conferir no GitHub |
| Escolha e justificativa técnica do backend | Ainda pendente; README identifica a decisão para a Fase 2 |

Esta é uma inspeção de arquivos; não é um teste automatizado de histórico Git.

## Pendências encontradas

D01: alternância completa de prioridades ausente. D02: perda do estado na reinicialização do App. D04: sequência não reinicia ao mudar o dia. D03 e D05 confirmam funções planejadas ainda ausentes: ciclo completo de atendimento e controle do expediente. Detalhes e reprodução estão em `pendencias.md` e em `evidencias/integracao-caua.json`.

A observação D02 foi produzida por desmontagem e remontagem do App; não é uma execução de F5 em navegador real. A execução em DOM simulado não comprova aparência, navegação por teclado, áudio, acessibilidade completa, desempenho sob carga ou concorrência entre terminais.

## Reprodução e encaminhamento

Na pasta `frontend`, executar `npm ci`. Na pasta `docs/tests`, executar `npm ci` e `npm run test:integration`.

Os resultados aprovam os fluxos descritos do protótipo, com as limitações acima. Não constituem aprovação do sistema completo. A contribuição está preparada para a branch de Cauã e pull request com destino a `dev`; a revisão e o merge final cabem ao Scrum Master.
