import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import Totem from '../src/pages/Totem.jsx';
import { erroDaApi, servidorFalso } from './helpers.js';

const EMITIDA = { id: 1, numero: '261127-SP001', tipo: 'SP', sequencial: 1, estado: 'AGUARDANDO', emitida_em: '2026-11-27T10:00:00-03:00' };

describe('Totem', () => {
  it('emite a senha escolhida e mostra o número que veio da API', async () => {
    const chamadas = servidorFalso({ 'POST /senhas': { status: 201, corpo: EMITIDA } });
    render(<Totem />);
    fireEvent.click(screen.getByRole('button', { name: /Prioritário/ }));
    expect(await screen.findByText('261127-SP001')).toBeTruthy();
    expect(chamadas).toHaveLength(1);
    expect(chamadas[0].corpo).toEqual({ tipo: 'SP' });
  });

  it('mostra o motivo quando a emissão é recusada (fora do expediente) e não exibe senha', async () => {
    servidorFalso({ 'POST /senhas': erroDaApi(409, 'FORA_DO_EXPEDIENTE', 'Fora do expediente (07h às 17h): não é possível emitir.') });
    render(<Totem />);
    fireEvent.click(screen.getByRole('button', { name: /Geral/ }));
    expect((await screen.findByRole('alert')).textContent).toMatch(/Fora do expediente/);
    expect(screen.queryByText('Sua senha')).toBeNull();
  });

  it('avisa que o sistema está indisponível quando o servidor não responde', async () => {
    servidorFalso({ 'POST /senhas': new TypeError('Failed to fetch') });
    render(<Totem />);
    fireEvent.click(screen.getByRole('button', { name: /Retirada de exames/ }));
    expect((await screen.findByRole('alert')).textContent).toMatch(/temporariamente indisponível/);
  });
});
