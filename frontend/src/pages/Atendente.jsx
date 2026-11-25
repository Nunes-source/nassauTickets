import { useCallback, useEffect, useState } from 'react';
import LoginAtendente from '../components/LoginAtendente.jsx';
import EscolhaGuiche from '../components/EscolhaGuiche.jsx';
import TerminalAtendente from '../components/TerminalAtendente.jsx';
import { obterMe } from '../api/api.js';
import { sessao, textoDoErro } from '../api/cliente.js';

// Fluxo do atendente: login → escolha do guichê → terminal.
export default function Atendente({ intervaloMs }) {
  const [usuario, setUsuario] = useState(sessao.ler()); // { token, nome, perfil } ou null
  const [guiche, setGuiche] = useState(undefined); // undefined = carregando · null = sem guichê · { id, numero }
  const [aviso, setAviso] = useState(null);
  const [erroCarga, setErroCarga] = useState(null);
  const [tentativa, setTentativa] = useState(0);

  const sair = useCallback((mensagem = null) => {
    sessao.limpar();
    setUsuario(null);
    setGuiche(undefined);
    setErroCarga(null);
    setAviso(mensagem);
  }, []);
  const expirar = useCallback(() => sair('Sessão expirada. Entre de novo.'), [sair]);

  // Com o token, descobre se este atendente já ocupa um guichê (por exemplo, depois de recarregar a página).
  useEffect(() => {
    if (!usuario) return undefined;
    let vivo = true;
    setErroCarga(null);
    obterMe()
      .then((me) => vivo && setGuiche(me.guiche ?? null))
      .catch((e) => {
        if (!vivo) return;
        if (e.status === 401) expirar();
        else setErroCarga(textoDoErro(e));
      });
    return () => { vivo = false; };
  }, [usuario, tentativa, expirar]);

  if (!usuario) {
    return (
      <LoginAtendente
        aviso={aviso}
        aoEntrar={(dados) => {
          sessao.salvar(dados);
          setAviso(null);
          setUsuario(dados);
        }}
      />
    );
  }

  if (erroCarga) {
    return (
      <section>
        <h1>Terminal do atendente</h1>
        <p role="alert" className="aviso aviso-erro">{erroCarga}</p>
        <button className="botao-secundario" onClick={() => setTentativa(tentativa + 1)}>Tentar de novo</button>
      </section>
    );
  }

  if (guiche === undefined) {
    return (
      <section>
        <h1>Terminal do atendente</h1>
        <p className="subtitulo">Carregando…</p>
      </section>
    );
  }

  if (guiche === null) {
    return <EscolhaGuiche usuario={usuario} aoOcupar={setGuiche} aoSair={() => sair()} aoExpirar={expirar} />;
  }

  return (
    <TerminalAtendente
      guiche={guiche}
      usuario={usuario}
      intervaloMs={intervaloMs}
      aoLiberar={() => setGuiche(null)}
      aoSair={() => sair()}
      aoExpirar={expirar}
    />
  );
}
