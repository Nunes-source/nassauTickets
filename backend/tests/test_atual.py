"""GET /atendimentos/atual: o front retoma a senha ativa do guichê depois de recarregar a página."""
from tests.conftest import API
from tests.test_fluxo import acao, chamar, emitir, ocupar


def atual(cliente, headers):
    resposta = cliente.get(f"{API}/atendimentos/atual", headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_sem_guiche_ou_sem_senha_ativa_devolve_null(cliente, relogio, atendente1):
    assert atual(cliente, atendente1) is None  # ainda sem guichê
    ocupar(cliente, atendente1, 1)
    assert atual(cliente, atendente1) is None  # com guichê, mas nada chamado


def test_acompanha_o_ciclo_da_senha(cliente, relogio, atendente1):
    senha = emitir(cliente, "SP")
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)

    a = atual(cliente, atendente1)
    assert a["senha"]["id"] == senha["id"] and a["senha"]["estado"] == "CHAMADA"
    assert a["chamada"]["numero"] == 1 and a["chamada"]["ultima_chamada"] is False
    assert a["guiche"]["numero"] == 1
    assert a["texto_chamada"] == "Senha prioritária zero zero um, guichê um"

    acao(cliente, atendente1, senha["id"], "chamar-novamente")
    a = atual(cliente, atendente1)
    assert a["senha"]["estado"] == "CHAMADA_NOVAMENTE" and a["chamada"]["ultima_chamada"] is True
    assert a["texto_chamada"].startswith("Última chamada.")

    acao(cliente, atendente1, senha["id"], "iniciar-atendimento")
    a = atual(cliente, atendente1)
    assert a["senha"]["estado"] == "EM_ATENDIMENTO" and a["chamada"]["numero"] == 2

    acao(cliente, atendente1, senha["id"], "encerrar-atendimento")
    assert atual(cliente, atendente1) is None


def test_nao_comparecimento_libera_o_guiche(cliente, relogio, atendente1):
    senha = emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)
    acao(cliente, atendente1, senha["id"], "chamar-novamente")
    acao(cliente, atendente1, senha["id"], "nao-compareceu")
    assert atual(cliente, atendente1) is None


def test_cada_atendente_ve_so_a_do_proprio_guiche(cliente, relogio, atendente1, atendente2):
    emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)
    ocupar(cliente, atendente2, 2)
    chamar(cliente, atendente1)
    assert atual(cliente, atendente1) is not None
    assert atual(cliente, atendente2) is None


def test_exige_login(cliente, relogio):
    resposta = cliente.get(f"{API}/atendimentos/atual")
    assert resposta.status_code == 401 and resposta.json()["codigo"] == "NAO_AUTENTICADO"
