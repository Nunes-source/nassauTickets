# Relatório de testes unitários

**Projeto:** nassauTickets — Fase 1  
**Responsável pela contribuição:** Gabriel Luann — 01654299  
**Origem examinada:** nassauTickets-main.zip  
**Execução:** automatizada assistida, 04/10/2026 (Brasília)  
**Ambiente:** Node.js 24.19.0, `America/Sao_Paulo`  
**Método:** importação das funções reais do frontend e asserções com `node:assert/strict`.

## Resultado

**16 verificações executadas: 16 aprovadas e 0 reprovadas.**

| ID | Verificação executada | Resultado |
|---|---|---|
| U01 | Numeração SP com data e três dígitos | APROVADO |
| U02 | Numeração SG com sequência própria recebida pela função | APROVADO |
| U03 | Numeração SE com sequência própria recebida pela função | APROVADO |
| U04 | Sequência 9 com preenchimento de zeros | APROVADO |
| U05 | Sequência 99 com preenchimento de zeros | APROVADO |
| U06 | Sequência 999 preserva três dígitos | APROVADO |
| U07 | Tipo e instante da emissão registrados | APROVADO |
| U08 | Fila vazia retorna null | APROVADO |
| U09 | SP é escolhida antes de SE e SG na regra simplificada | APROVADO |
| U10 | SE é escolhida antes de SG quando não há SP | APROVADO |
| U11 | SG é escolhida quando as outras filas estão vazias | APROVADO |
| U12 | Dentro do mesmo tipo vale a chegada na lista | APROVADO |
| U13 | Escolha não altera a fila original | APROVADO |
| U14 | Hora exibida em horas e minutos no fuso definido | APROVADO |
| U15 | Data recebida altera o prefixo da senha | APROVADO |
| U16 | Totem oferece apenas os três tipos previstos | APROVADO |

## Evidência e reprodução

O resultado completo está em `evidencias/unitarios-gabriel.json`. Na raiz do projeto:

```bash
node docs/tests/scripts/unitarios-gabriel.mjs
```

A suite não precisa de dependências externas e não muda os arquivos originais. O resultado corresponde à versão do ZIP recebido; executar de novo se o código em `dev` for diferente.

## Interpretação

A função `criarSenha` recebe a sequência como argumento. Os testes de numeração verificam sua formatação, e não afirmam que ela gerencia sozinha o contador diário. O incremento independente no App foi verificado pela suite de integração.

Os casos U09 e U10 aprovam a prioridade simplificada existente. A alternância completa exigida pelo professor permanece pendente e aparece no relatório de integração como D01. A formatação de data correta não comprova o reinício automático da sequência na virada do dia.

## Encaminhamento

Contribuição preparada para revisão na branch de Gabriel e pull request para `dev`. O código da aplicação foi preservado. A inclusão no GitHub, autoria do commit e merge ainda dependem da execução do fluxo pelos integrantes e pelo Scrum Master.
