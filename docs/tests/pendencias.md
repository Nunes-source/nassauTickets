# Pendências e limitações observadas

**Base:** Fase 1 do ZIP recebido, sem alteração do código.  
**Evidência:** `evidencias/integracao-caua.json`.  
**Contribuição:** Cauã Andrade — 01821096.

## D01 — Alternância entre prioridades

**Requisitos:** RF03, RN02 e RN03.  
**Situação:** pendência confirmada, já reconhecida como parcial no README.  
**Impacto:** emissão contínua de SP pode adiar indefinidamente SE e SG.

Reprodução: emitir SP001, SP002, SE001 e SG001; chamar quatro vezes. A ordem observada é `SP → SP → SE → SG`. Conforme RN02/RN03 do documento do grupo, a ordem esperada é `SP → SE → SP → SG`. Essa expectativa usa a regra documentada pelo grupo para resolver a redação da especificação. Encaminhar ao desenvolvedor para implementação da alternância.

## D02 — Estado perdido na reinicialização

**Requisitos:** RF02, RN09 e RNF05.  
**Situação:** limitação confirmada e prevista no README.  
**Impacto:** perda da fila e possibilidade de repetir números no mesmo dia.

Reprodução executada: emitir SP001, desmontar o App e montá-lo novamente, emitir SP. Observado: SP001 novamente, sem preservar a fila anterior. Esse experimento simula reinicialização do componente; o teste de recarregar a página no navegador permanece no roteiro manual. Persistência deve ser validada após integração com backend/banco.

## D03 — Ciclo de atendimento e rechamada ausentes

**Requisitos:** RF04 a RF07, RF10, RN05, RN06 e RN12.  
**Situação:** não implementado nesta fase, conforme README.  
**Impacto:** não é possível comprovar atendimento iniciado/concluído nem abandono após duas chamadas.

Inspeção do terminal montado: a única ação de atendimento disponível é `Chamar próxima`. Não existem os controles de iniciar, finalizar, rechamar ou não comparecimento. Registrar como implementação futura; uma senha chamada não deve ser contada como atendida em relatório.

## D04 — Contador não reinicia automaticamente na virada do dia

**Requisitos:** RF02 e RN09.  
**Situação:** pendência confirmada.  
**Impacto:** o prefixo passa a representar o novo dia, mas o contador continua do dia anterior.

Reprodução executada com relógio controlado: às 23h59 de 04/10/2026, emitir SG; sem reinicializar o App, avançar para 00h01 de 05/10/2026 e emitir SG. Observado: `261004-SG001 → 261005-SG002`. Esperado para o reinício diário: `261005-SG001`.

O cenário é isolado para conferir a numeração; o horário também evidencia o controle de expediente ausente em D05.

## D05 — Controle do expediente ausente

**Requisitos:** RN04, RF13 e fluxo alternativo UC01.  
**Situação:** não implementado nesta fase, conforme README.  
**Impacto:** emissão permitida fora do horário de funcionamento; descarte e encerramento ainda não verificáveis.

Na execução D04 foram aceitas emissões às 23h59 e 00h01. O sistema completo deve tratar o expediente entre 7h e 17h, concluir atendimentos em curso e descartar a fila restante ao encerrar.

## Funcionalidades não validadas

Login e perfis; backend e MySQL; relatórios e auditoria; áudio; concorrência distribuída; disponibilidade, recuperação e backup; tempos médios do sistema completo; segurança e acessibilidade completa. Elas não recebem resultado aprovado nesta entrega. A observação histórica de cerca de 5% de não comparecimento não foi simulada nem validada como descarte aleatório de clientes reais.

## Tratamento

Todas as pendências estão abertas para triagem pelo Scrum Master e pelo desenvolvedor. A divisão da Fase 1 permite registrar funções planejadas sem afirmar que estejam implementadas. Nenhuma correção no código foi realizada pelos testadores nesta contribuição.
