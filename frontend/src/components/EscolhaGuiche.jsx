import { useCallback, useEffect, useState } from 'react';
import { listarGuichesLivres, ocuparGuiche } from '../api/api.js';
import { textoDoErro } from '../api/cliente.js';

// O atendente escolhe um guichê livre. Um atendente ocupa no máximo um guichê (RN-11).
export default function EscolhaGuiche({ usuario, aoOcupar, aoSair, aoExpirar }) {
  const [guiches, setGuiches] = useState(null);
  const [erro, setErro] = useState(null);
  const [ocupando, setOcupando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setGuiches(await listarGuichesLivres());
      setErro(null);
    } catch (e) {
      if (e.status === 401) return aoExpirar();
      setErro(textoDoErro(e));
    }
    return undefined;
  }, [aoExpirar]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  async function ocupar(guiche) {
    setOcupando(true);
    setErro(null);
    try {
      await ocuparGuiche(guiche.id);
      aoOcupar({ id: guiche.id, numero: guiche.numero });
    } catch (e) {
      if (e.status === 401) return aoExpirar();
      setErro(textoDoErro(e));
      await carregar(); // a lista pode ter mudado (outro atendente pegou o guichê)
      setOcupando(false);
    }
    return undefined;
  }

  return (
    <section>
      <h1>Terminal do atendente</h1>
      <div className="cartao atendente-topo">
        <p>Olá, <strong>{usuario.nome}</strong>. Escolha o seu guichê.</p>
        <div className="atendente-topo-acoes">
          <button className="botao-secundario" onClick={() => aoSair()}>Sair</button>
        </div>
      </div>

      {erro && <p role="alert" className="aviso aviso-erro">{erro}</p>}

      {guiches === null && !erro && <p className="subtitulo">Carregando guichês…</p>}
      {guiches !== null && guiches.length === 0 && (
        <div className="cartao painel-vazio">
          <p>Nenhum guichê livre agora.</p>
          <button className="botao-secundario" onClick={carregar}>Atualizar lista</button>
        </div>
      )}
      {guiches !== null && guiches.length > 0 && (
        <ul className="guiches-lista">
          {guiches.map((g) => (
            <li key={g.id}>
              <button className="botao-primario" disabled={ocupando} onClick={() => ocupar(g)}>
                Guichê {g.numero}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
