import { useEffect, useRef, useState } from 'react';
import SenhaTag from '../components/SenhaTag.jsx';
import usePolling from '../hooks/usePolling.js';
import { obterPainel } from '../api/api.js';
import { formatarHora } from '../utils/formatar.js';

const TOTAL_NO_PAINEL = 5; // senha atual + histórico = 5 últimas chamadas
const temVoz = () => typeof window !== 'undefined' && 'speechSynthesis' in window;

// O painel consulta a API a cada poucos segundos. Nunca mostra a próxima senha.
export default function Painel({ intervaloMs = 3000 }) {
  const { dados, erro } = usePolling(obterPainel, intervaloMs);
  const [somAtivo, setSomAtivo] = useState(false);
  const jaAnunciada = useRef(undefined); // undefined = ainda não carregou a primeira vez

  const chamadas = dados?.ultimas ?? [];
  const atual = chamadas[0];
  const anteriores = chamadas.slice(1, TOTAL_NO_PAINEL);
  const chaveAtual = atual ? `${atual.numero}#${atual.chamada}` : null;

  // Áudio: anuncia só chamadas novas (a primeira carga não fala nada) e só com o som ativado.
  useEffect(() => {
    if (dados === null) return;
    if (jaAnunciada.current === undefined) {
      jaAnunciada.current = chaveAtual;
      return;
    }
    if (chaveAtual && chaveAtual !== jaAnunciada.current) {
      jaAnunciada.current = chaveAtual;
      if (somAtivo && temVoz()) {
        window.speechSynthesis.cancel();
        const fala = new SpeechSynthesisUtterance(atual.texto_chamada);
        fala.lang = 'pt-BR';
        window.speechSynthesis.speak(fala);
      }
    }
  }, [dados, chaveAtual, atual, somAtivo]);

  return (
    <section>
      <h1>Painel de chamadas</h1>

      {erro && (
        <p role="status" className="aviso aviso-info">
          Reconectando ao servidor… {chamadas.length > 0 ? 'As chamadas abaixo podem estar desatualizadas.' : ''}
        </p>
      )}

      {temVoz() && (
        <button className="botao-secundario som-botao" aria-pressed={somAtivo} onClick={() => setSomAtivo(!somAtivo)}>
          {somAtivo ? 'Desativar som das chamadas' : 'Ativar som das chamadas'}
        </button>
      )}

      {dados === null && !erro && <p className="subtitulo">Carregando…</p>}

      {dados !== null && atual && (
        <div key={chaveAtual} className={`cartao painel-atual borda-${atual.tipo}`} aria-live="polite">
          <p className="painel-rotulo">{atual.ultima_chamada ? 'Última chamada' : 'Chamando agora'}</p>
          <p className="painel-senha">{atual.numero}</p>
          <p className="painel-guiche">
            Guichê <strong>{atual.guiche}</strong> <SenhaTag tipo={atual.tipo} />
          </p>
        </div>
      )}

      {dados !== null && !atual && (
        <div className="cartao painel-vazio">
          <p>Nenhuma senha chamada ainda.</p>
          <p className="senha-detalhe">As chamadas aparecem aqui assim que o atendente chamar a próxima senha.</p>
        </div>
      )}

      {anteriores.length > 0 && (
        <>
          <h2 className="titulo-secao">Últimas chamadas</h2>
          <ol className="historico">
            {anteriores.map((c) => (
              <li key={c.numero + c.chamada_em} className="historico-item">
                <SenhaTag tipo={c.tipo} />
                <span className="historico-senha">{c.numero}</span>
                <span className="historico-guiche">Guichê {c.guiche}</span>
                <span className="historico-hora">{formatarHora(c.chamada_em)}</span>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
