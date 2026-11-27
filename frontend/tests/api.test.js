import { beforeEach, describe, expect, it } from 'vitest';
import { atendimentoAtual, chamarProximo, emitirSenha, obterPainel } from '../src/api/api.js';
import { ErroApi, sessao, textoDoErro } from '../src/api/cliente.js';
import { erroDaApi, servidorFalso } from './helpers.js';

beforeEach(() => sessao.limpar());

describe('cliente da API', () => {
  it('emite senha com POST /senhas e corpo JSON, sem token', async () => {
    const chamadas = servidorFalso({ 'POST /senhas': { status: 201, corpo: { numero: '261127-SG001' } } });
    expect(await emitirSenha('SG')).toEqual({ numero: '261127-SG001' });
    expect(chamadas[0].chave).toBe('POST /senhas');
    expect(chamadas[0].corpo).toEqual({ tipo: 'SG' });
    expect(chamadas[0].cabecalhos.Authorization).toBeUndefined();
  });

  it('envia o token só nas rotas autenticadas', async () => {
    sessao.salvar({ token: 'abc', nome: 'Ana', perfil: 'ATENDENTE' });
    const chamadas = servidorFalso({
      'GET /painel': { corpo: { ultimas: [] } },
      'POST /atendimentos/chamar-proximo': { corpo: {} },
    });
    await obterPainel();
    await chamarProximo();
    expect(chamadas[0].cabecalhos.Authorization).toBeUndefined();
    expect(chamadas[1].cabecalhos.Authorization).toBe('Bearer abc');
  });

  it('devolve null quando a API responde 200 com corpo null (nenhuma senha ativa)', async () => {
    servidorFalso({ 'GET /atendimentos/atual': { corpo: null } });
    expect(await atendimentoAtual()).toBeNull();
  });

  it('transforma o erro padronizado da API em ErroApi', async () => {
    servidorFalso({ 'POST /senhas': erroDaApi(409, 'FORA_DO_EXPEDIENTE', 'Fora do expediente') });
    const erro = await emitirSenha('SP').catch((e) => e);
    expect(erro).toBeInstanceOf(ErroApi);
    expect(erro.codigo).toBe('FORA_DO_EXPEDIENTE');
    expect(erro.status).toBe(409);
    expect(erro.indisponivel).toBe(false);
  });

  it('rede fora vira SEM_CONEXAO e conta como indisponível', async () => {
    servidorFalso({ 'GET /painel': new TypeError('Failed to fetch') });
    const erro = await obterPainel().catch((e) => e);
    expect(erro.codigo).toBe('SEM_CONEXAO');
    expect(erro.indisponivel).toBe(true);
    expect(textoDoErro(erro)).toMatch(/temporariamente indisponível/);
  });

  it('503 sem corpo vira BANCO_INDISPONIVEL', async () => {
    servidorFalso({ 'GET /painel': { status: 503, corpo: undefined } });
    const erro = await obterPainel().catch((e) => e);
    expect(erro.codigo).toBe('BANCO_INDISPONIVEL');
    expect(erro.indisponivel).toBe(true);
  });
});
