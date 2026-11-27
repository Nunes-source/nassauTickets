import { vi } from 'vitest';

const resposta = (status, corpo) => ({ ok: status >= 200 && status < 300, status, json: async () => corpo });

// Servidor falso: troca o fetch global. As rotas são "METODO /caminho" (sem o prefixo /api/v1).
// Cada rota é { status?, corpo } ou uma função que devolve isso (ou um Error, para simular rede fora).
export function servidorFalso(rotas) {
  const chamadas = [];
  globalThis.fetch = vi.fn(async (url, opcoes = {}) => {
    const caminho = String(url).replace(/^https?:\/\/[^/]+\/api\/v1/, '');
    const chave = `${opcoes.method || 'GET'} ${caminho}`;
    chamadas.push({ chave, corpo: opcoes.body ? JSON.parse(opcoes.body) : undefined, cabecalhos: opcoes.headers });
    const rota = rotas[chave];
    if (!rota) return resposta(404, { codigo: 'NAO_ENCONTRADO', mensagem: `rota ausente no servidor falso: ${chave}` });
    const r = typeof rota === 'function' ? rota() : rota;
    if (r instanceof Error) throw r;
    return resposta(r.status ?? 200, r.corpo);
  });
  return chamadas;
}

export const erroDaApi = (status, codigo, mensagem) => ({ status, corpo: { codigo, mensagem, detalhes: {}, request_id: 'teste' } });

export const SENHA_SP = { id: 7, numero: '261127-SP001', tipo: 'SP', sequencial: 1, estado: 'CHAMADA' };

export const chamadaResposta = (estado, numeroChamada = 1) => ({
  senha: { ...SENHA_SP, estado },
  guiche: { id: 1, numero: 1 },
  chamada: { numero: numeroChamada, ultima_chamada: numeroChamada === 2, chamada_em: '2026-11-27T10:00:00-03:00' },
  texto_chamada: numeroChamada === 2
    ? 'Última chamada. Senha prioritária zero zero um, guichê um'
    : 'Senha prioritária zero zero um, guichê um',
});
