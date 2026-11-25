"""Login, JWT, perfis e log de acesso (RNF-01, RNF-02)."""
from datetime import datetime, timedelta, timezone

import jwt

from tests.conftest import API, consultar


def _login(cliente, email, senha):
    return cliente.post(f"{API}/auth/login", json={"email": email, "senha": senha})


def test_login_correto_devolve_token_e_perfil(cliente):
    resposta = _login(cliente, "gestor@nassau.local", "Gestor@123")
    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["token_type"] == "bearer" and corpo["perfil"] == "GESTOR" and corpo["nome"] == "Gestor"
    assert corpo["access_token"] and "expira_em" in corpo
    assert "senha" not in resposta.text.lower().replace("senha_", "")  # nada de senha/hash na resposta


def test_senha_fica_salva_com_argon2id(ambiente):
    hashes = consultar(ambiente, "SELECT senha_hash FROM usuarios")
    assert hashes and all(h["senha_hash"].startswith("$argon2id$") for h in hashes)


def test_credenciais_erradas_dao_a_mesma_resposta(cliente):
    senha_errada = _login(cliente, "gestor@nassau.local", "errada")
    email_inexistente = _login(cliente, "ninguem@nassau.local", "Gestor@123")
    for resposta in (senha_errada, email_inexistente):
        assert resposta.status_code == 401
        assert resposta.json()["codigo"] == "CREDENCIAIS_INVALIDAS"
    assert senha_errada.json()["mensagem"] == email_inexistente.json()["mensagem"]


def test_usuario_inativo_nao_entra_e_perde_o_token(cliente, gestor, ambiente):
    token_antigo = _login(cliente, "atendente2@nassau.local", "Atendente@123").json()["access_token"]
    usuarios = cliente.get(f"{API}/usuarios", headers=gestor).json()
    id_atendente2 = next(u["id"] for u in usuarios if u["email"] == "atendente2@nassau.local")
    assert cliente.patch(f"{API}/usuarios/{id_atendente2}", json={"ativo": False}, headers=gestor).status_code == 200

    assert _login(cliente, "atendente2@nassau.local", "Atendente@123").json()["codigo"] == "CREDENCIAIS_INVALIDAS"
    antigo = cliente.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token_antigo}"})
    assert antigo.status_code == 401


def test_me_sem_token_e_401_padronizado(cliente):
    resposta = cliente.get(f"{API}/auth/me")
    assert resposta.status_code == 401
    corpo = resposta.json()
    assert corpo["codigo"] == "NAO_AUTENTICADO" and corpo["request_id"]


def test_token_invalido_e_token_expirado_sao_401(cliente):
    from app.core.config import get_config

    assert cliente.get(f"{API}/auth/me", headers={"Authorization": "Bearer lixo"}).status_code == 401
    expirado = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
                          get_config().jwt_segredo, algorithm="HS256")
    assert cliente.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {expirado}"}).status_code == 401
    assinado_errado = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                                 "outro-segredo-qualquer-123", algorithm="HS256")
    assert cliente.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {assinado_errado}"}).status_code == 401


def test_me_devolve_dados_e_guiche_nulo(cliente, atendente1):
    corpo = cliente.get(f"{API}/auth/me", headers=atendente1).json()
    assert corpo["email"] == "atendente1@nassau.local" and corpo["perfil"] == "ATENDENTE"
    assert corpo["guiche"] is None
    assert "senha_hash" not in corpo


def test_atendente_nao_acessa_rotas_de_gestor(cliente, atendente1):
    for metodo, rota in (("get", "/usuarios"), ("get", "/indicadores"), ("get", "/relatorios/diario/resumo")):
        resposta = getattr(cliente, metodo)(f"{API}{rota}", headers=atendente1)
        assert resposta.status_code == 403, rota
        assert resposta.json()["codigo"] == "SEM_PERMISSAO"


def test_gestor_herda_o_perfil_de_atendente(cliente, gestor):
    assert cliente.get(f"{API}/guiches", headers=gestor).status_code == 200
    assert cliente.get(f"{API}/usuarios", headers=gestor).status_code == 200


def test_log_de_acesso_registra_sem_senha_nem_token(cliente, ambiente, atendente1):
    cliente.get(f"{API}/auth/me", headers=atendente1)
    cliente.get(f"{API}/usuarios", headers=atendente1)  # negado
    _login(cliente, "atendente1@nassau.local", "errada")  # falha

    linhas = consultar(ambiente, "SELECT acao, recurso, ip, resultado FROM log_acesso ORDER BY id")
    resultados = {(l["acao"], l["recurso"], l["resultado"]) for l in linhas}
    assert ("LOGIN", "POST /auth/login", "SUCESSO") in resultados
    assert ("LOGIN", "POST /auth/login", "FALHA") in resultados
    assert ("ACESSO", "GET /auth/me", "SUCESSO") in resultados
    assert ("ACESSO", "GET /usuarios", "NEGADO") in resultados
    token = atendente1["Authorization"].split()[1]
    texto = str(linhas)
    assert token not in texto and "Atendente@123" not in texto and "errada" not in texto


def test_corpo_invalido_devolve_422_com_campos(cliente):
    resposta = cliente.post(f"{API}/auth/login", json={"email": "sem-arroba", "senha": ""})
    corpo = resposta.json()
    assert resposta.status_code == 422 and corpo["codigo"] == "VALIDACAO"
    assert {c["campo"] for c in corpo["detalhes"]["campos"]} == {"email", "senha"}


def test_toda_resposta_traz_x_request_id(cliente):
    assert cliente.get(f"{API}/health").headers["X-Request-ID"]
