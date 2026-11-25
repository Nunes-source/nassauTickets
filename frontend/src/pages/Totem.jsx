import { useState } from 'react';
import SenhaTag from '../components/SenhaTag.jsx';
import { emitirSenha } from '../api/api.js';
import { textoDoErro } from '../api/cliente.js';
import { TIPOS, ORDEM_TOTEM } from '../data/tipos.js';
import { formatarHora } from '../utils/formatar.js';

export default function Totem() {
  const [ultimaEmitida, setUltimaEmitida] = useState(null);
  const [enviando, setEnviando] = useState(null);
  const [erro, setErro] = useState(null);

  async function emitir(sigla) {
    setEnviando(sigla);
    setErro(null);
    try {
      setUltimaEmitida(await emitirSenha(sigla));
    } catch (e) {
      setUltimaEmitida(null);
      setErro(textoDoErro(e));
    } finally {
      setEnviando(null);
    }
  }

  return (
    <section>
      <h1>Retire sua senha</h1>
      <p className="subtitulo">Escolha o tipo de atendimento.</p>

      <div className="totem-opcoes">
        {ORDEM_TOTEM.map((sigla) => (
          <button key={sigla} className={`opcao opcao-${sigla}`} disabled={enviando !== null} onClick={() => emitir(sigla)}>
            <span className="opcao-sigla">{sigla}</span>
            <span className="opcao-nome">{TIPOS[sigla].nome}</span>
            <span className="opcao-descricao">{TIPOS[sigla].descricao}</span>
          </button>
        ))}
      </div>

      {erro && <p role="alert" className="aviso aviso-erro">{erro}</p>}

      {ultimaEmitida && (
        <div className={`cartao senha-emitida borda-${ultimaEmitida.tipo}`} aria-live="polite">
          <div className="senha-emitida-topo">
            <span>Sua senha</span>
            <SenhaTag tipo={ultimaEmitida.tipo} />
          </div>
          <p className="senha-numero">{ultimaEmitida.numero}</p>
          <p className="senha-detalhe">
            Emitida às {formatarHora(ultimaEmitida.emitida_em)} · Aguarde ser chamado no painel
          </p>
        </div>
      )}
    </section>
  );
}
