# Roteiro manual — verificações ainda não executadas

Este roteiro complementa os resultados automatizados. **Todos os casos abaixo estão NÃO EXECUTADOS em navegador real nesta entrega.** Não usar esta lista como evidência de aprovação.

Iniciar com `cd frontend`, `npm ci` e `npm run dev`; abrir a URL mostrada pelo Vite. Usar dados fictícios e uma sessão limpa para cada caso. Registrar uma nova evidência apenas após executar a verificação.

| ID | Ação | Resultado esperado ou limite a confirmar | Situação |
|---|---|---|---|
| M01 | Emitir SP, SG e SE pelo Totem | Cartão legível com número, tipo e horário; fila aumenta | Não executado |
| M02 | Navegar para Atendente, escolher guichê e chamar | Senha sai da fila e aparece no Painel com o guichê escolhido | Não executado |
| M03 | Chamar sete senhas e abrir Painel | Exatamente cinco últimas, em ordem da mais recente | Não executado |
| M04 | Abrir fila vazia e tentar chamar | Botão desabilitado e mensagem clara | Não executado |
| M05 | Usar somente Tab, Shift+Tab e Enter; usar teclado no seletor | Foco visível e todas as ações acessíveis, sem armadilha de foco | Não executado |
| M06 | Usar leitor de tela no menu, totem e seletor | Rótulos compreensíveis; região de atualização anunciada corretamente | Não executado |
| M07 | Medir contraste das cores e ampliar para 200% | Texto e controles legíveis; sem perda de ações | Não executado |
| M08 | Conferir em 390px, 768px e 1366px | Sem cortes ou rolagem horizontal indevida; painel legível | Não executado |
| M09 | Abrir em navegadores diferentes e observar console | Fluxos básicos sem erros; registrar navegador e versão reais | Não executado |
| M10 | Emitir e chamar, depois recarregar a página | Confirmar perda de dados já prevista no protótipo e registrar a limitação | Não executado |
| M11 | Abrir Totem e Painel em abas distintas | Confirmar ausência de sincronização entre páginas no protótipo | Não executado |
| M12 | Executar suites e build com Node.js 22 LTS | Confirmar compatibilidade com a versão recomendada pelo projeto | Não executado |

Áudio, login, banco, relatórios, concorrência entre clientes e recuperação de falhas precisam de roteiro adicional quando estiverem implementados. jsdom não mede layout real nem comprova conformidade integral de acessibilidade.
