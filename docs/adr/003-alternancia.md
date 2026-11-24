# ADR-003 — Regra de alternância e escolha do próximo tipo
**Status:** aceito (confirmar com o professor, se possível) · **Responsável:** Dev A

**Problema:** o diagrama do requisito diz `[SP] → [SE|SG] → [SP] → [SE|SG]`, e o texto diz que o atendimento segue "SP, depois SE, depois SG", com prioridade SP > SE > SG e "senha diferente da anterior" a cada atendimento. Filas vazias ficam por conta do sistema, mantendo as regras.

**Decisão (função pura `escolher_tipo(ultimo_tipo, disponiveis)`):**
1. Se nenhum tipo tem senha aguardando → `None` (`FILA_VAZIA`).
2. Candidatos = tipos disponíveis **menos** `ultimo_tipo` (para nunca repetir o tipo anterior).
3. Se não sobrar candidato, usa o próprio `ultimo_tipo` (só ele tem fila).
4. Entre os candidatos, vale a prioridade SP > SE > SG.

**Exemplos (todas as filas cheias):** SP → SE → SP → SE → ... Sem SE: SP → SG → SP → SG. Sem SP: SE → SG → SE → SG. Só SG: SG → SG.

**Consequência assumida:** com SP e SE sempre disponíveis, a SG só é chamada quando a SP ou a SE esvaziam (ela é a de menor prioridade). Registrar isso na apresentação como comportamento esperado.

**Testes obrigatórios (`test_fila.py`):** tabela com `(ultimo_tipo, disponiveis) → esperado` cobrindo todos os 4×8 casos relevantes, mais um dia simulado completo.
