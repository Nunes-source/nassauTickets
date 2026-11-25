// Cliente HTTP do back end (FastAPI). A URL base vem de VITE_API_URL (veja frontend/.env.example).
const BASE = (import.meta.env?.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const CHAVE_SESSAO = 'nassautickets.sessao';

// Erro padronizado do back end: { codigo, mensagem, detalhes } (veja docs/api/contrato-api.md).
export class ErroApi extends Error {
  constructor(codigo, mensagem, status = 0, detalhes = {}) {
    super(mensagem);
    this.codigo = codigo;
    this.status = status;
    this.detalhes = detalhes;
  }

  // Rede fora (status 0) ou back end/banco indisponível (503).
  get indisponivel() {
    return this.status === 0 || this.status === 503;
  }
}

// Sessão do atendente (token JWT). Fica em sessionStorage: some ao fechar a aba.
let emMemoria = null;
export const sessao = {
  ler() {
    if (emMemoria) return emMemoria;
    try {
      emMemoria = JSON.parse(sessionStorage.getItem(CHAVE_SESSAO));
    } catch {
      emMemoria = null;
    }
    return emMemoria;
  },
  salvar(dados) {
    emMemoria = dados;
    try {
      sessionStorage.setItem(CHAVE_SESSAO, JSON.stringify(dados));
    } catch {
      /* sem sessionStorage: a sessão vale só enquanto a página estiver aberta */
    }
  },
  limpar() {
    emMemoria = null;
    try {
      sessionStorage.removeItem(CHAVE_SESSAO);
    } catch {
      /* nada a limpar */
    }
  },
};

export async function requisitar(caminho, { metodo = 'GET', corpo, autenticado = false } = {}) {
  const cabecalhos = { Accept: 'application/json' };
  if (corpo !== undefined) cabecalhos['Content-Type'] = 'application/json';
  if (autenticado) {
    const atual = sessao.ler();
    if (atual?.token) cabecalhos.Authorization = `Bearer ${atual.token}`;
  }

  let resposta;
  try {
    resposta = await fetch(`${BASE}${caminho}`, {
      method: metodo,
      headers: cabecalhos,
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw new ErroApi('SEM_CONEXAO', 'Não foi possível falar com o servidor.', 0);
  }

  let json = null;
  try {
    json = await resposta.json();
  } catch {
    /* resposta sem corpo JSON */
  }

  if (!resposta.ok) {
    const codigo = json?.codigo || (resposta.status === 503 ? 'BANCO_INDISPONIVEL' : 'ERRO_INTERNO');
    throw new ErroApi(codigo, json?.mensagem || 'Erro inesperado no servidor.', resposta.status, json?.detalhes || {});
  }
  return json;
}

const MENSAGENS = {
  SEM_CONEXAO: 'Sistema temporariamente indisponível. Verifique a conexão e tente de novo.',
  BANCO_INDISPONIVEL: 'Sistema temporariamente indisponível. Tente de novo em instantes.',
  ERRO_INTERNO: 'Erro inesperado no servidor. Tente de novo.',
  CREDENCIAIS_INVALIDAS: 'E-mail ou senha incorretos.',
  FORA_DO_EXPEDIENTE: 'Fora do expediente (07h às 17h).',
  FILA_VAZIA: 'Não há senhas aguardando.',
};

// Texto para mostrar ao usuário. Os demais códigos já vêm do servidor em português.
export const textoDoErro = (erro) => MENSAGENS[erro.codigo] || erro.message || MENSAGENS.ERRO_INTERNO;
