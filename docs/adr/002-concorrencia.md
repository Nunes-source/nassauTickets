# ADR-002 — Estratégia de concorrência ao chamar a próxima senha
**Status:** aceito · **Responsável:** Dev A

**Problema:** dois ou mais atendentes chamam a próxima senha quase ao mesmo tempo; a mesma senha não pode ir para dois guichês, e a alternância SP → SE|SG depende do **último tipo chamado**, que é um estado global.

**Decisão:** lock pessimista na linha do dia em `fila_estado`, dentro de uma transação:
1. `BEGIN`
2. `INSERT IGNORE INTO fila_estado (data) VALUES (hoje)` e `SELECT ultimo_tipo ... FOR UPDATE` (aqui as chamadas simultâneas **entram em fila**)
3. `escolher_tipo(ultimo_tipo, tipos_disponiveis)` (ADR-003)
4. `SELECT ... FROM senhas WHERE estado='AGUARDANDO' AND tipo=? ORDER BY sequencia LIMIT 1 FOR UPDATE`
5. `UPDATE senhas` → CHAMADA, `INSERT chamadas`, `INSERT senha_historico`, `UPDATE fila_estado.ultimo_tipo`
6. `COMMIT` (libera o lock; a próxima chamada já enxerga o resultado)

**Por que não só `SKIP LOCKED`:** ele evitaria a duplicidade, mas dois atendentes leriam o mesmo `ultimo_tipo` e poderiam quebrar a alternância. Com o lock na linha de `fila_estado`, as decisões ficam serializadas e corretas. A seção crítica dura milissegundos, e o volume do laboratório (poucos guichês) torna isso suficiente.

**Complementos:** a numeração usa `INSERT ... ON DUPLICATE KEY UPDATE ultimo_seq = LAST_INSERT_ID(ultimo_seq+1)`; as constraints `UNIQUE` em `senhas` e `chamadas` são a segunda barreira contra duplicidade.

**Demonstração (arguição):** `tests/test_concorrencia.py` dispara N threads chamando em guichês diferentes com M senhas aguardando e confere que não há senha repetida e que a alternância se mantém. A mesma cena roda ao vivo com o simulador.
