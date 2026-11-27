// Uma função por endpoint usado pelo front (veja docs/api/contrato-api.md).
import { requisitar } from './cliente.js';

// Públicos (totem e painel)
export const emitirSenha = (tipo) => requisitar('/senhas', { metodo: 'POST', corpo: { tipo } });
export const obterPainel = () => requisitar('/painel');

// Autenticação
export const entrar = (email, senha) => requisitar('/auth/login', { metodo: 'POST', corpo: { email, senha } });
export const obterMe = () => requisitar('/auth/me', { autenticado: true });

// Guichês
export const listarGuichesLivres = () => requisitar('/guiches?livres=true', { autenticado: true });
export const ocuparGuiche = (id) => requisitar(`/guiches/${id}/ocupar`, { metodo: 'POST', autenticado: true });
export const liberarGuiche = (id) => requisitar(`/guiches/${id}/liberar`, { metodo: 'POST', autenticado: true });

// Fila e atendimento
export const resumoFila = () => requisitar('/fila/resumo', { autenticado: true });
export const atendimentoAtual = () => requisitar('/atendimentos/atual', { autenticado: true });
export const chamarProximo = () => requisitar('/atendimentos/chamar-proximo', { metodo: 'POST', autenticado: true });

const acaoSobreSenha = (id, nome) => requisitar(`/senhas/${id}/${nome}`, { metodo: 'POST', autenticado: true });
export const chamarNovamente = (id) => acaoSobreSenha(id, 'chamar-novamente');
export const iniciarAtendimento = (id) => acaoSobreSenha(id, 'iniciar-atendimento');
export const encerrarAtendimento = (id) => acaoSobreSenha(id, 'encerrar-atendimento');
export const registrarNaoComparecimento = (id) => acaoSobreSenha(id, 'nao-compareceu');
