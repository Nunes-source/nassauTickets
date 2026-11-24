# ADR-004 — Simulação do TM, 5% de não atendimento e descartes
**Status:** aceito (confirmar com o professor) · **Responsável:** Dev A

**Problema:** o edital pede TM simulado por tipo e ~5% de senhas não atendidas, mas quem inicia e encerra o atendimento é o atendente via API.

**Decisão**
- **TM:** ao iniciar o atendimento, a API sorteia `duracao_simulada_seg` conforme RN-07 e grava em `atendimentos`. O encerramento continua manual; o relatório de TM compara o simulado com o real.
- **5% não comparecem:** o `tools/simulador.py` (cliente da API) simula atendentes e clientes: em ~5% das senhas ele chama duas vezes e registra `nao-compareceu`; nas demais, inicia, espera a duração simulada (acelerada por `--velocidade`) e encerra. Também serve para gerar volume para os relatórios na demonstração.
- **Não comparecimento (real):** só existe após a 2ª chamada e por ação do atendente (`/nao-compareceu`), motivo `ABANDONO`.
- **Fim do expediente (RN-10):** na primeira requisição depois das 17h (e por uma tarefa agendada simples, se der tempo), as senhas AGUARDANDO do dia viram NAO_COMPARECEU com motivo `FIM_EXPEDIENTE`. Atendimentos já em curso podem ser encerrados normalmente.
- **Demonstração fora do horário:** `EXPEDIENTE_FORCAR_ABERTO=true` no `.env` (nunca em produção).

**Alternativa descartada:** simular dentro da API com temporizadores; mais frágil e difícil de testar.
