import { useCallback, useEffect, useState } from 'react';
import SenhaTag from './SenhaTag.jsx';
import usePolling from '../hooks/usePolling.js';
import {
  atendimentoAtual, chamarNovamente, chamarProximo, encerrarAtendimento,
  iniciarAtendimento, liberarGuiche, registrarNaoComparecimento, resumoFila,
} from '../api/api.js';
import { textoDoErro } from '../api/cliente.js';

const ROTULO_ESTADO = {
  CHAMADA: 'Chamada · aguardando o cliente',
  CHAMADA_NOVAMENTE: 'Última chamada feita · aguardando o cliente',
  EM_ATENDIMENTO: 'Em atendimento',
};

export default function TerminalAtendente({ guiche, usuario, aoLiberar, aoSair, aoExpirar, intervaloMs = 3000 }) {
  const [ativa, setAtiva] = useState(undefined); // undefined = carregando · null = nenhuma senha ativa
  const [mensagem, setMensagem] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const { dados: resumo, erro: erroResumo, atualizar: atualizarResumo } = usePolling(resumoFila, intervaloMs);

  const tratarErro = useCallback((e) => {
    if (e.status === 401) {
      aoExpirar();
      return;
    }
    setMensagem({ tipo: 'erro', texto: textoDoErro(e) });
  }, [aoExpirar]);

  // Ao abrir (ou recarregar a página), retoma a senha que este guichê já estava atendendo.
  useEffect(() => {
    let vivo = true;
    atendimentoAtual()
      .then((a) => vivo && setAtiva(a))
      .catch((e) => {
        if (!vivo) return;
        setAtiva(null);
        tratarErro(e);
      });
    return () => { vivo = false; };
  }, [tratarErro]);

  useEffect(() => {
    if (erroResumo?.status === 401) aoExpirar();
  }, [erroResumo, aoExpirar]);

  async function executar(chamada, aposSucesso) {
    setOcupado(true);
    setMensagem(null);
    try {
      const resultado = await chamada();
      aposSucesso(resultado);
      atualizarResumo();
    } catch (e) {
      tratarErro(e);
      if (e.status === 409) { // o estado mudou (por exemplo, em outra aba): sincroniza de novo
        try { setAtiva(await atendimentoAtual()); } catch { /* mantém o que já está na tela */ }
      }
    } finally {
      setOcupado(false);
    }
  }

  const chamar = () => executar(chamarProximo, (r) => setAtiva(r));
  const chamarDeNovo = () => executar(() => chamarNovamente(ativa.senha.id), (r) => setAtiva(r));
  const iniciar = () => executar(() => iniciarAtendimento(ativa.senha.id), (r) => setAtiva({ ...ativa, senha: r.senha }));
  const encerrar = () => executar(() => encerrarAtendimento(ativa.senha.id), () => {
    setMensagem({ tipo: 'ok', texto: `Atendimento da senha ${ativa.senha.numero} encerrado.` });
    setAtiva(null);
  });
  const naoCompareceu = () => executar(() => registrarNaoComparecimento(ativa.senha.id), () => {
    setMensagem({ tipo: 'ok', texto: `Senha ${ativa.senha.numero} registrada como não comparecimento.` });
    setAtiva(null);
  });
  const liberar = () => executar(() => liberarGuiche(guiche.id), () => aoLiberar());

  async function sair() {
    setOcupado(true);
    if (!ativa) {
      try { await liberarGuiche(guiche.id); } catch { /* sai mesmo assim */ }
    }
    aoSair();
  }

  const total = resumo ? Object.values(resumo).reduce((soma, n) => soma + n, 0) : null;
  const estado = ativa?.senha.estado;

  return (
    <section>
      <h1>Terminal do atendente</h1>

      <div className="cartao atendente-topo">
        <p><strong>{usuario.nome}</strong> · Guichê <strong>{guiche.numero}</strong></p>
        <div className="atendente-topo-acoes">
          <button className="botao-secundario" disabled={ocupado || Boolean(ativa)} onClick={liberar}>Liberar guichê</button>
          <button className="botao-secundario" disabled={ocupado} onClick={sair}>Sair</button>
        </div>
      </div>

      {mensagem && (
        <p role={mensagem.tipo === 'erro' ? 'alert' : 'status'} className={`aviso aviso-${mensagem.tipo}`}>{mensagem.texto}</p>
      )}

      {ativa === undefined && <p className="subtitulo">Carregando…</p>}

      {ativa === null && (
        <div className="cartao ativa-card">
          <p className="ativa-rotulo">Nenhuma senha em atendimento neste guichê.</p>
          <div className="ativa-acoes">
            <button className="botao-primario" disabled={ocupado} onClick={chamar}>Chamar próxima</button>
          </div>
        </div>
      )}

      {ativa && (
        <div className={`cartao ativa-card borda-${ativa.senha.tipo}`} aria-live="polite">
          <p className="ativa-rotulo">{ROTULO_ESTADO[estado] ?? estado}</p>
          <p className="senha-numero">{ativa.senha.numero} <SenhaTag tipo={ativa.senha.tipo} /></p>
          <p className="senha-detalhe">{ativa.texto_chamada}</p>
          <div className="ativa-acoes">
            {estado === 'CHAMADA' && (
              <button className="botao-secundario" disabled={ocupado} onClick={chamarDeNovo}>Chamar novamente</button>
            )}
            {(estado === 'CHAMADA' || estado === 'CHAMADA_NOVAMENTE') && (
              <button className="botao-primario" disabled={ocupado} onClick={iniciar}>Iniciar atendimento</button>
            )}
            {estado === 'CHAMADA_NOVAMENTE' && (
              <button className="botao-perigo" disabled={ocupado} onClick={naoCompareceu}>Cliente não compareceu</button>
            )}
            {estado === 'EM_ATENDIMENTO' && (
              <button className="botao-primario" disabled={ocupado} onClick={encerrar}>Encerrar atendimento</button>
            )}
          </div>
        </div>
      )}

      <h2 className="titulo-secao">Fila de espera ({total ?? '…'})</h2>
      {erroResumo && erroResumo.status !== 401 && (
        <p role="status" className="aviso aviso-info">Sem conexão com o servidor. Os números podem estar desatualizados.</p>
      )}
      <p className="resumo-fila">
        {['SP', 'SE', 'SG'].map((tipo) => (
          <span key={tipo} className="resumo-item"><SenhaTag tipo={tipo} /> {resumo ? resumo[tipo] ?? 0 : '…'}</span>
        ))}
      </p>
    </section>
  );
}
