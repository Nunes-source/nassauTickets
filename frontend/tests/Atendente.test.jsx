import { beforeEach, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import Atendente from '../src/pages/Atendente.jsx';
import { sessao } from '../src/api/cliente.js';
import { chamadaResposta, erroDaApi, servidorFalso } from './helpers.js';

const LOGIN = { access_token: 'tok', token_type: 'bearer', perfil: 'ATENDENTE', nome: 'Atendente 1', expira_em: '2026-11-27T18:00:00-03:00' };
const ME = (guiche) => ({ id: 2, nome: 'Atendente 1', email: 'a@nassau.local', perfil: 'ATENDENTE', guiche });
const GUICHE_LIVRE = { id: 1, numero: 1, ativo: true, livre: true, ocupante: null };

beforeEach(() => sessao.limpar());

function entrar() {
  fireEvent.change(screen.getByLabelText('E-mail'), { target: { value: 'atendente1@nassau.local' } });
  fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'Atendente@123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Entrar' }));
}

describe('Atendente', () => {
  it('login, ocupa o guichê e atende uma senha do início ao fim', async () => {
    let guicheOcupado = false;
    let ativa = null;
    const chamadas = servidorFalso({
      'POST /auth/login': { corpo: LOGIN },
      'GET /auth/me': () => ({ corpo: ME(guicheOcupado ? { id: 1, numero: 1 } : null) }),
      'GET /guiches?livres=true': { corpo: [GUICHE_LIVRE] },
      'POST /guiches/1/ocupar': () => { guicheOcupado = true; return { corpo: { ...GUICHE_LIVRE, livre: false } }; },
      'GET /atendimentos/atual': () => ({ corpo: ativa }),
      'GET /fila/resumo': { corpo: { SP: 1, SE: 0, SG: 0 } },
      'POST /atendimentos/chamar-proximo': () => { ativa = chamadaResposta('CHAMADA'); return { corpo: ativa }; },
      'POST /senhas/7/iniciar-atendimento': () => {
        ativa = chamadaResposta('EM_ATENDIMENTO');
        return { corpo: { senha: ativa.senha, duracao_simulada_seg: 600 } };
      },
      'POST /senhas/7/encerrar-atendimento': () => { ativa = null; return { corpo: { ...chamadaResposta('ATENDIDA').senha } }; },
    });

    render(<Atendente intervaloMs={20} />);
    entrar();
    fireEvent.click(await screen.findByRole('button', { name: 'Guichê 1' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Chamar próxima' }));

    expect(await screen.findByText('261127-SP001')).toBeTruthy();
    expect(screen.getByText('Senha prioritária zero zero um, guichê um')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Encerrar atendimento' })).toBeNull(); // ainda não iniciou

    fireEvent.click(screen.getByRole('button', { name: 'Iniciar atendimento' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Encerrar atendimento' }));
    expect(await screen.findByText('Atendimento da senha 261127-SP001 encerrado.')).toBeTruthy();
    expect(await screen.findByRole('button', { name: 'Chamar próxima' })).toBeTruthy();

    const chamar = chamadas.find((c) => c.chave === 'POST /atendimentos/chamar-proximo');
    expect(chamar.cabecalhos.Authorization).toBe('Bearer tok');
    expect(sessao.ler().token).toBe('tok');
  });

  it('retoma a senha ativa do guichê ao recarregar a página', async () => {
    sessao.salvar({ token: 'tok', nome: 'Atendente 1', perfil: 'ATENDENTE' });
    servidorFalso({
      'GET /auth/me': { corpo: ME({ id: 1, numero: 1 }) },
      'GET /atendimentos/atual': { corpo: chamadaResposta('EM_ATENDIMENTO', 2) },
      'GET /fila/resumo': { corpo: { SP: 0, SE: 0, SG: 3 } },
    });
    render(<Atendente intervaloMs={20} />);
    expect(await screen.findByText('Em atendimento')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Encerrar atendimento' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Chamar próxima' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Liberar guichê' }).disabled).toBe(true); // há senha ativa
  });

  it('chama novamente, depois registra o não comparecimento', async () => {
    sessao.salvar({ token: 'tok', nome: 'Atendente 1', perfil: 'ATENDENTE' });
    let ativa = chamadaResposta('CHAMADA');
    const chamadas = servidorFalso({
      'GET /auth/me': { corpo: ME({ id: 1, numero: 1 }) },
      'GET /atendimentos/atual': () => ({ corpo: ativa }),
      'GET /fila/resumo': { corpo: { SP: 0, SE: 0, SG: 0 } },
      'POST /senhas/7/chamar-novamente': () => { ativa = chamadaResposta('CHAMADA_NOVAMENTE', 2); return { corpo: ativa }; },
      'POST /senhas/7/nao-compareceu': () => { ativa = null; return { corpo: chamadaResposta('NAO_COMPARECEU').senha }; },
    });
    render(<Atendente intervaloMs={20} />);

    expect(screen.queryByRole('button', { name: 'Cliente não compareceu' })).toBeNull();
    fireEvent.click(await screen.findByRole('button', { name: 'Chamar novamente' }));
    expect(await screen.findByText(/Última chamada\. Senha prioritária/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Chamar novamente' })).toBeNull(); // só uma vez (RN-15)

    fireEvent.click(screen.getByRole('button', { name: 'Cliente não compareceu' }));
    expect(await screen.findByText(/registrada como não comparecimento/)).toBeTruthy();
    expect(chamadas.map((c) => c.chave)).toContain('POST /senhas/7/nao-compareceu');
  });

  it('mostra a mensagem do servidor quando não há senhas para chamar', async () => {
    sessao.salvar({ token: 'tok', nome: 'Atendente 1', perfil: 'ATENDENTE' });
    servidorFalso({
      'GET /auth/me': { corpo: ME({ id: 1, numero: 1 }) },
      'GET /atendimentos/atual': { corpo: null },
      'GET /fila/resumo': { corpo: { SP: 0, SE: 0, SG: 0 } },
      'POST /atendimentos/chamar-proximo': erroDaApi(404, 'FILA_VAZIA', 'Não há senhas aguardando.'),
    });
    render(<Atendente intervaloMs={20} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Chamar próxima' }));
    expect((await screen.findByRole('alert')).textContent).toBe('Não há senhas aguardando.');
  });

  it('sincroniza com o servidor quando a ação dá conflito (estado mudou em outra aba)', async () => {
    sessao.salvar({ token: 'tok', nome: 'Atendente 1', perfil: 'ATENDENTE' });
    let ativa = null;
    servidorFalso({
      'GET /auth/me': { corpo: ME({ id: 1, numero: 1 }) },
      'GET /atendimentos/atual': () => ({ corpo: ativa }),
      'GET /fila/resumo': { corpo: { SP: 0, SE: 0, SG: 1 } },
      'POST /atendimentos/chamar-proximo': () => {
        ativa = chamadaResposta('CHAMADA'); // outra aba já tinha chamado
        return erroDaApi(409, 'GUICHE_COM_SENHA_ATIVA', 'Este guichê ainda tem uma senha chamada ou em atendimento.');
      },
    });
    render(<Atendente intervaloMs={20} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Chamar próxima' }));
    expect(await screen.findByText('261127-SP001')).toBeTruthy(); // a tela passou a mostrar a senha ativa
    expect(screen.getByRole('button', { name: 'Iniciar atendimento' })).toBeTruthy();
  });

  it('login incorreto mostra o erro e fica na tela de login', async () => {
    servidorFalso({ 'POST /auth/login': erroDaApi(401, 'CREDENCIAIS_INVALIDAS', 'Credenciais inválidas.') });
    render(<Atendente intervaloMs={20} />);
    entrar();
    expect((await screen.findByRole('alert')).textContent).toBe('E-mail ou senha incorretos.');
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeTruthy();
    expect(sessao.ler()).toBeNull();
  });

  it('sessão expirada (401) volta ao login com aviso e apaga o token', async () => {
    sessao.salvar({ token: 'velho', nome: 'Atendente 1', perfil: 'ATENDENTE' });
    servidorFalso({ 'GET /auth/me': erroDaApi(401, 'NAO_AUTENTICADO', 'Sessão inválida.') });
    render(<Atendente intervaloMs={20} />);
    expect(await screen.findByText('Sessão expirada. Entre de novo.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeTruthy();
    expect(sessao.ler()).toBeNull();
  });

  it('sair libera o guichê quando não há senha ativa', async () => {
    sessao.salvar({ token: 'tok', nome: 'Atendente 1', perfil: 'ATENDENTE' });
    const chamadas = servidorFalso({
      'GET /auth/me': { corpo: ME({ id: 1, numero: 1 }) },
      'GET /atendimentos/atual': { corpo: null },
      'GET /fila/resumo': { corpo: { SP: 0, SE: 0, SG: 0 } },
      'POST /guiches/1/liberar': { corpo: { ...GUICHE_LIVRE } },
    });
    render(<Atendente intervaloMs={20} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Sair' }));
    expect(await screen.findByRole('button', { name: 'Entrar' })).toBeTruthy();
    expect(chamadas.map((c) => c.chave)).toContain('POST /guiches/1/liberar');
    expect(sessao.ler()).toBeNull();
  });
});
