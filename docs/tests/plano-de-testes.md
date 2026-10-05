# Plano de testes — Fase 1

**Projeto:** nassauTickets  
**Contribuição de:** Gabriel Luann, matrícula 01654299  
**Participante da etapa de integração:** Cauã Andrade, matrícula 01821096  
**Base:** orientações da atividade, especificação do laboratório, README e requisitos do ZIP recebido.

## Objetivo e escopo

Verificar a implementação existente da Fase 1: emissão SP/SE/SG, numeração, fila em memória, chamada por guichê, integração entre telas e painel das cinco últimas chamadas. Registrar divergências da especificação completa sem alterar a aplicação.

O README identifica esta entrega como protótipo de frontend. Backend, banco, autenticação, atendimento completo, áudio, concorrência entre clientes e relatórios ficam para a segunda fase. A atividade exige organização, documentação, participação, versionamento e algum código na primeira fase; não exige que o sistema completo já esteja funcional nessa etapa.

## Estratégia

| Camada | Técnica | Evidência |
|---|---|---|
| Funções de senha | Execução das funções reais com `node:assert/strict` | `unitarios-gabriel.json` |
| Componentes e estado do React | Montagem do App real em jsdom, cliques e navegação simulados | `integracao-caua.json` |
| Compilação | `npm ci` e `npm run build` na cópia de análise | `build-frontend.txt` |
| Integridade do escopo | Comparação byte a byte dos arquivos originais | `integridade-projeto.json` |
| Navegador real | Roteiro manual, ainda não executado | `roteiro-manual.md` |
| Organização do repositório | Inspeção dos arquivos disponíveis no ZIP | `relatorio-caua.md` |

## Rastreabilidade

| Requisito/regra | Casos | Alcance e restrição |
|---|---|---|
| RF01 / RN01 — emissão dos três tipos | U01–U03, U16, I01–I03 | Emissão em memória e integração com a fila |
| RF02 / RN09 — número da senha | U01–U07, U15, I02, D02, D04 | Formato e sequência verificados; persistência e reinício diário têm pendências |
| RF03 / RN02 / RN03 — próxima senha | U08–U13, I04–I08, D01 | Regra simplificada verificada; alternância completa não implementada |
| RF08 / RN08 — painel de chamadas | I04–I10 | Cinco últimas, guichê e ausência de antecipação |
| RN01 — qualquer guichê atende qualquer tipo | I12 | Nove combinações de tipo e guichê em uma única instância do App |
| Navegação e rótulo do guichê | I11, I13–I15 | DOM e estado; sem certificar acessibilidade completa |
| RN04 / RF13 — expediente | D05 | Ausência de bloqueio confirmada; função planejada |
| RF04–RF07 / RF10 — atendimento e estados | D03 | Controles ainda ausentes; não confundir chamada com atendimento concluído |
| RNF10 — acessibilidade | M05–M07 | Pendente de navegador real; rótulos isolados não certificam WCAG |
| RNF07 / RNF08 — desempenho e concorrência | M09 e testes futuros | Sem medição de carga nem clientes simultâneos nesta execução |

## Critérios de resultado

- **Aprovado:** a verificação executada encontrou o comportamento esperado para o escopo explicitado.
- **Reprovado:** uma verificação executada encontrou comportamento diferente do esperado.
- **Pendência confirmada:** observação reproduzida de divergência em relação ao sistema completo.
- **Não implementado nesta fase:** funcionalidade explicitamente planejada para a Fase 2.
- **Não executado:** não existe evidência de execução suficiente; não contar como aprovado.

A aprovação dos testes de caracterização do protótipo não equivale à aprovação de todos os requisitos do professor.

## Critérios para encaminhar a contribuição

Scripts sem falhas inesperadas, evidências anexadas, pendências descritas, alteração limitada a `docs/tests/` e commits separados pelos integrantes. A decisão de aceitar e integrar cabe ao Scrum Master.

## Limites

Sem navegador real disponível nesta execução, não foram verificados layout, teclado, leitores de tela ou áudio. Não houve validação de segurança, LGPD, restauração de banco, disponibilidade, concorrência distribuída ou relatórios. O ZIP também não permite comprovar branches, colaboração ou merges no GitHub. Não foram atribuídos resultados fictícios aos integrantes.
