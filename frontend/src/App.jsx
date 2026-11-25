import { useEffect, useState } from 'react';
import Cabecalho from './components/Cabecalho.jsx';
import Totem from './pages/Totem.jsx';
import Painel from './pages/Painel.jsx';
import Atendente from './pages/Atendente.jsx';

const TELAS_VALIDAS = ['totem', 'painel', 'atendente'];

// A tela atual vem do endereço (#totem, #painel ou #atendente).
const telaDoEndereco = () => {
  const id = window.location.hash.replace('#', '');
  return TELAS_VALIDAS.includes(id) ? id : 'totem';
};

export default function App() {
  const [tela, setTela] = useState(telaDoEndereco());

  useEffect(() => {
    const aoMudar = () => setTela(telaDoEndereco());
    window.addEventListener('hashchange', aoMudar);
    return () => window.removeEventListener('hashchange', aoMudar);
  }, []);

  // Cada tela conversa direto com a API: a fila, a alternância e os estados vivem no back end.
  return (
    <>
      <Cabecalho telaAtual={tela} />
      <main>
        {tela === 'totem' && <Totem />}
        {tela === 'painel' && <Painel />}
        {tela === 'atendente' && <Atendente />}
      </main>
      <footer className="rodape">nassauTickets · front-end integrado à API do back end (FastAPI + MySQL)</footer>
    </>
  );
}
