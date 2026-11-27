import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import Painel from '../src/pages/Painel.jsx';
import { servidorFalso } from './helpers.js';

const item = (numero, tipo, guiche, chamada = 1) => ({
  numero, tipo, sequencial: Number(numero.slice(-3)), guiche, chamada, ultima_chamada: chamada === 2,
  chamada_em: '2026-11-27T10:05:00-03:00', texto_chamada: 'texto',
});
const PAINEL = { ultimas: [item('261127-SG002', 'SG', 2), item('261127-SP001', 'SP', 1)], atualizado_em: '2026-11-27T10:05:03-03:00' };

describe('Painel', () => {
  it('mostra a chamada atual e as anteriores vindas da API', async () => {
    servidorFalso({ 'GET /painel': { corpo: PAINEL } });
    render(<Painel intervaloMs={20} />);
    expect(await screen.findByText('261127-SG002')).toBeTruthy();
    expect(screen.getByText('Chamando agora')).toBeTruthy();
    expect(screen.getByText('261127-SP001')).toBeTruthy();
    expect(screen.getByText('Últimas chamadas')).toBeTruthy();
  });

  it('rotula como "Última chamada" quando é a segunda chamada', async () => {
    servidorFalso({ 'GET /painel': { corpo: { ultimas: [item('261127-SP001', 'SP', 1, 2)], atualizado_em: 'x' } } });
    render(<Painel intervaloMs={20} />);
    expect(await screen.findByText('Última chamada')).toBeTruthy();
  });

  it('com a lista vazia, explica que ainda não houve chamadas', async () => {
    servidorFalso({ 'GET /painel': { corpo: { ultimas: [], atualizado_em: 'x' } } });
    render(<Painel intervaloMs={20} />);
    expect(await screen.findByText('Nenhuma senha chamada ainda.')).toBeTruthy();
  });

  it('se o servidor cair, mantém a última lista na tela e avisa que está reconectando', async () => {
    let consultas = 0;
    servidorFalso({ 'GET /painel': () => (++consultas === 1 ? { corpo: PAINEL } : new TypeError('Failed to fetch')) });
    render(<Painel intervaloMs={20} />);
    expect(await screen.findByText('261127-SG002')).toBeTruthy();
    expect(await screen.findByText(/Reconectando/)).toBeTruthy();
    expect(screen.getByText('261127-SG002')).toBeTruthy(); // continua visível
  });

  it('volta ao normal quando o servidor se recupera', async () => {
    let consultas = 0;
    servidorFalso({ 'GET /painel': () => (++consultas === 2 ? new TypeError('x') : { corpo: PAINEL }) });
    render(<Painel intervaloMs={20} />);
    await screen.findByText(/Reconectando/);
    await new Promise((r) => setTimeout(r, 120));
    expect(screen.queryByText(/Reconectando/)).toBeNull();
  });
});
