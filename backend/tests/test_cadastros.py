"""Usuários e guichês (RN-11, RN-13)."""
from concurrent.futures import ThreadPoolExecutor

from tests.conftest import API, consultar

NOVO = {"nome": "Maria Souza", "email": "maria@nassau.local", "senha": "Troque@123", "perfil": "ATENDENTE"}


def _guiches(cliente, headers, livres=False):
    return cliente.get(f"{API}/guiches", params={"livres": livres}, headers=headers).json()


def _id_guiche(cliente, headers, numero):
    return next(g["id"] for g in _guiches(cliente, headers) if g["numero"] == numero)


# ------------------------------------------------------------------ usuários

def test_gestor_cadastra_usuario_e_ele_consegue_entrar(cliente, gestor):
    resposta = cliente.post(f"{API}/usuarios", json=NOVO, headers=gestor)
    assert resposta.status_code == 201
    assert resposta.json()["email"] == "maria@nassau.local" and "senha" not in resposta.text.lower().replace("senha_", "")
    login = cliente.post(f"{API}/auth/login", json={"email": NOVO["email"], "senha": NOVO["senha"]})
    assert login.status_code == 200


def test_email_repetido_e_409(cliente, gestor):
    cliente.post(f"{API}/usuarios", json=NOVO, headers=gestor)
    resposta = cliente.post(f"{API}/usuarios", json={**NOVO, "nome": "Outra"}, headers=gestor)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "EMAIL_JA_CADASTRADO"


def test_so_pode_existir_um_gestor_ativo(cliente, gestor):
    resposta = cliente.post(f"{API}/usuarios", json={**NOVO, "perfil": "GESTOR"}, headers=gestor)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "GESTOR_JA_EXISTE"


def test_promover_atendente_a_gestor_tambem_e_barrado(cliente, gestor):
    maria = cliente.post(f"{API}/usuarios", json=NOVO, headers=gestor).json()
    resposta = cliente.patch(f"{API}/usuarios/{maria['id']}", json={"perfil": "GESTOR"}, headers=gestor)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "GESTOR_JA_EXISTE"


def test_senha_curta_e_422(cliente, gestor):
    resposta = cliente.post(f"{API}/usuarios", json={**NOVO, "senha": "123"}, headers=gestor)
    assert resposta.status_code == 422 and resposta.json()["codigo"] == "VALIDACAO"


def test_atendente_nao_cadastra_usuario(cliente, atendente1):
    assert cliente.post(f"{API}/usuarios", json=NOVO, headers=atendente1).status_code == 403


def test_listagem_nao_mostra_hash(cliente, gestor):
    resposta = cliente.get(f"{API}/usuarios", headers=gestor)
    assert resposta.status_code == 200 and len(resposta.json()) == 3
    assert "senha_hash" not in resposta.text and "argon2" not in resposta.text


def test_gestor_nao_inativa_a_si_mesmo(cliente, gestor):
    meu_id = cliente.get(f"{API}/auth/me", headers=gestor).json()["id"]
    resposta = cliente.patch(f"{API}/usuarios/{meu_id}", json={"ativo": False}, headers=gestor)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "AUTOALTERACAO_PROIBIDA"


def test_usuario_inexistente_e_404(cliente, gestor):
    resposta = cliente.patch(f"{API}/usuarios/9999", json={"nome": "X"}, headers=gestor)
    assert resposta.status_code == 404 and resposta.json()["codigo"] == "NAO_ENCONTRADO"


def test_inativar_atendente_libera_o_guichê_dele(cliente, gestor, atendente1):
    guiche = _id_guiche(cliente, atendente1, 1)
    cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente1)
    id_atendente1 = cliente.get(f"{API}/auth/me", headers=atendente1).json()["id"]
    cliente.patch(f"{API}/usuarios/{id_atendente1}", json={"ativo": False}, headers=gestor)
    assert next(g for g in _guiches(cliente, gestor) if g["id"] == guiche)["livre"] is True


# ------------------------------------------------------------------- guichês

def test_lista_guiches_do_seed(cliente, atendente1):
    guiches = _guiches(cliente, atendente1)
    assert [g["numero"] for g in guiches] == [1, 2, 3]
    assert all(g["livre"] and g["ocupante"] is None for g in guiches)


def test_ocupar_e_liberar(cliente, atendente1):
    guiche = _id_guiche(cliente, atendente1, 2)
    ocupado = cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente1)
    assert ocupado.status_code == 200 and ocupado.json()["livre"] is False
    assert cliente.get(f"{API}/auth/me", headers=atendente1).json()["guiche"]["numero"] == 2
    assert [g["numero"] for g in _guiches(cliente, atendente1, livres=True)] == [1, 3]
    liberado = cliente.post(f"{API}/guiches/{guiche}/liberar", headers=atendente1)
    assert liberado.status_code == 200 and liberado.json()["livre"] is True


def test_ocupar_o_proprio_guiche_de_novo_e_inofensivo(cliente, atendente1):
    guiche = _id_guiche(cliente, atendente1, 1)
    assert cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente1).status_code == 200
    assert cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente1).status_code == 200


def test_guiche_ocupado_por_outro_e_409(cliente, atendente1, atendente2):
    guiche = _id_guiche(cliente, atendente1, 1)
    cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente1)
    resposta = cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente2)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "GUICHE_OCUPADO"


def test_um_atendente_nao_ocupa_dois_guiches(cliente, atendente1):
    cliente.post(f"{API}/guiches/{_id_guiche(cliente, atendente1, 1)}/ocupar", headers=atendente1)
    resposta = cliente.post(f"{API}/guiches/{_id_guiche(cliente, atendente1, 2)}/ocupar", headers=atendente1)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "ATENDENTE_JA_TEM_GUICHE"


def test_so_o_ocupante_ou_o_gestor_libera(cliente, gestor, atendente1, atendente2):
    guiche = _id_guiche(cliente, atendente1, 1)
    cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente1)
    assert cliente.post(f"{API}/guiches/{guiche}/liberar", headers=atendente2).status_code == 403
    assert cliente.post(f"{API}/guiches/{guiche}/liberar", headers=gestor).status_code == 200


def test_guiche_inexistente_e_404(cliente, atendente1):
    assert cliente.post(f"{API}/guiches/9999/ocupar", headers=atendente1).status_code == 404


def test_gestor_cadastra_e_desativa_guiche(cliente, gestor, atendente1):
    criado = cliente.post(f"{API}/guiches", json={"numero": 4}, headers=gestor)
    assert criado.status_code == 201 and criado.json()["numero"] == 4
    repetido = cliente.post(f"{API}/guiches", json={"numero": 4}, headers=gestor)
    assert repetido.status_code == 409 and repetido.json()["codigo"] == "GUICHE_JA_CADASTRADO"
    desativado = cliente.patch(f"{API}/guiches/{criado.json()['id']}", json={"ativo": False}, headers=gestor)
    assert desativado.json()["ativo"] is False and desativado.json()["livre"] is False
    resposta = cliente.post(f"{API}/guiches/{criado.json()['id']}/ocupar", headers=atendente1)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "GUICHE_INATIVO"


def test_nao_desativa_guiche_ocupado(cliente, gestor, atendente1):
    guiche = _id_guiche(cliente, atendente1, 1)
    cliente.post(f"{API}/guiches/{guiche}/ocupar", headers=atendente1)
    resposta = cliente.patch(f"{API}/guiches/{guiche}", json={"ativo": False}, headers=gestor)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "GUICHE_OCUPADO"


def test_atendente_nao_cadastra_guiche(cliente, atendente1):
    assert cliente.post(f"{API}/guiches", json={"numero": 9}, headers=atendente1).status_code == 403


def test_dois_atendentes_disputando_o_mesmo_guiche_so_um_ganha(cliente, ambiente, atendente1, atendente2):
    from fastapi.testclient import TestClient

    from app.main import app

    guiche = _id_guiche(cliente, atendente1, 3)
    clientes = [TestClient(app), TestClient(app)]
    cabecalhos = [atendente1, atendente2]
    with ThreadPoolExecutor(max_workers=2) as pool:
        respostas = list(pool.map(
            lambda i: clientes[i].post(f"{API}/guiches/{guiche}/ocupar", headers=cabecalhos[i]), range(2)))
    assert sorted(r.status_code for r in respostas) == [200, 409]
    linha = consultar(ambiente, "SELECT usuario_id FROM guiches WHERE id = %s", (guiche,))[0]
    assert linha["usuario_id"] is not None
