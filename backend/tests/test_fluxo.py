"""Fluxo completo da fila pela API (UC-01 a UC-09, UC-14). Relógio congelado em 27/11/2026."""
from tests.conftest import API, consultar

DIA = "2026-11-27"
PREFIXO = "261127"


# ---------------------------------------------------------------- ajudantes

def emitir(cliente, tipo):
    resposta = cliente.post(f"{API}/senhas", json={"tipo": tipo})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def ocupar(cliente, headers, numero):
    guiche = next(g for g in cliente.get(f"{API}/guiches", headers=headers).json() if g["numero"] == numero)
    resposta = cliente.post(f"{API}/guiches/{guiche['id']}/ocupar", headers=headers)
    assert resposta.status_code == 200, resposta.text
    return guiche["id"]


def chamar(cliente, headers):
    return cliente.post(f"{API}/atendimentos/chamar-proximo", headers=headers)


def acao(cliente, headers, senha_id, nome):
    return cliente.post(f"{API}/senhas/{senha_id}/{nome}", headers=headers)


def atender(cliente, headers):
    """Chama, inicia e encerra uma senha. Devolve a resposta da chamada."""
    chamada = chamar(cliente, headers)
    assert chamada.status_code == 200, chamada.text
    senha_id = chamada.json()["senha"]["id"]
    assert acao(cliente, headers, senha_id, "iniciar-atendimento").status_code == 200
    assert acao(cliente, headers, senha_id, "encerrar-atendimento").status_code == 200
    return chamada.json()


def historico(banco, senha_id):
    linhas = consultar(banco, "SELECT estado_anterior, estado_novo, origem FROM senha_historico "
                              "WHERE senha_id = %s ORDER BY id", (senha_id,))
    return [(l["estado_anterior"], l["estado_novo"], l["origem"]) for l in linhas]


# ------------------------------------------------------------------ emissão

def test_emissao_gera_numero_sequencia_por_tipo_e_historico(cliente, ambiente, relogio):
    sp1, sp2, sg1 = emitir(cliente, "SP"), emitir(cliente, "SP"), emitir(cliente, "SG")
    assert [s["numero"] for s in (sp1, sp2, sg1)] == [f"{PREFIXO}-SP001", f"{PREFIXO}-SP002", f"{PREFIXO}-SG001"]
    assert sp1["estado"] == "AGUARDANDO" and sp1["tipo"] == "SP" and sp1["sequencial"] == 1
    assert sp1["emitida_em"] == "2026-11-27T10:00:00-03:00"
    assert historico(ambiente, sp1["id"]) == [(None, "EMITIDA", "TOTEM"), ("EMITIDA", "AGUARDANDO", "SISTEMA")]


def test_tipo_invalido_e_422(cliente, relogio):
    resposta = cliente.post(f"{API}/senhas", json={"tipo": "XX"})
    assert resposta.status_code == 422 and resposta.json()["codigo"] == "VALIDACAO"


def test_emissao_so_dentro_do_expediente(cliente, relogio):
    relogio.definir(6, 59)
    antes = cliente.post(f"{API}/senhas", json={"tipo": "SG"})
    assert antes.status_code == 409 and antes.json()["codigo"] == "FORA_DO_EXPEDIENTE"
    relogio.definir(7, 0)
    assert cliente.post(f"{API}/senhas", json={"tipo": "SG"}).status_code == 201
    relogio.definir(17, 0)
    assert cliente.post(f"{API}/senhas", json={"tipo": "SG"}).json()["codigo"] == "FORA_DO_EXPEDIENTE"


def test_sequencia_esgotada_desfaz_o_contador(cliente, ambiente, relogio):
    with ambiente.cursor() as cur:
        cur.execute("INSERT INTO contadores_senha (data, tipo, ultimo_seq) VALUES (%s, 'SP', 999)", (DIA,))
    ambiente.commit()
    resposta = cliente.post(f"{API}/senhas", json={"tipo": "SP"})
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "SEQUENCIA_ESGOTADA"
    assert consultar(ambiente, "SELECT ultimo_seq FROM contadores_senha WHERE tipo = 'SP'")[0]["ultimo_seq"] == 999
    assert cliente.post(f"{API}/senhas", json={"tipo": "SG"}).status_code == 201  # outros tipos seguem


def test_rotas_publicas_nao_pedem_login_e_as_do_atendente_pedem(cliente, relogio):
    assert cliente.post(f"{API}/senhas", json={"tipo": "SE"}).status_code == 201
    assert cliente.get(f"{API}/painel").status_code == 200
    assert cliente.post(f"{API}/atendimentos/chamar-proximo").status_code == 401
    assert cliente.get(f"{API}/fila/resumo").status_code == 401
    assert cliente.post(f"{API}/senhas/1/iniciar-atendimento").status_code == 401


# ------------------------------------------------------ atendimento completo

def test_fluxo_completo_ate_atendida(cliente, ambiente, relogio, atendente1):
    senha = emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)

    chamada = chamar(cliente, atendente1)
    corpo = chamada.json()
    assert chamada.status_code == 200
    assert corpo["senha"] == {"id": senha["id"], "numero": f"{PREFIXO}-SG001", "tipo": "SG", "sequencial": 1,
                              "estado": "CHAMADA"}
    assert corpo["guiche"]["numero"] == 1
    assert corpo["chamada"] == {"numero": 1, "ultima_chamada": False, "chamada_em": "2026-11-27T10:00:00-03:00"}
    assert corpo["texto_chamada"] == "Senha geral zero zero um, guichê um"

    iniciado = acao(cliente, atendente1, senha["id"], "iniciar-atendimento")
    assert iniciado.status_code == 200 and iniciado.json()["senha"]["estado"] == "EM_ATENDIMENTO"
    assert 120 <= iniciado.json()["duracao_simulada_seg"] <= 480  # SG: 2 a 8 min (RN-07)

    encerrado = acao(cliente, atendente1, senha["id"], "encerrar-atendimento")
    assert encerrado.status_code == 200 and encerrado.json()["estado"] == "ATENDIDA"

    assert historico(ambiente, senha["id"]) == [
        (None, "EMITIDA", "TOTEM"), ("EMITIDA", "AGUARDANDO", "SISTEMA"), ("AGUARDANDO", "CHAMADA", "ATENDENTE"),
        ("CHAMADA", "EM_ATENDIMENTO", "ATENDENTE"), ("EM_ATENDIMENTO", "ATENDIDA", "ATENDENTE")]
    atendimento = consultar(ambiente, "SELECT * FROM atendimentos WHERE senha_id = %s", (senha["id"],))[0]
    assert atendimento["finalizado_em"] is not None and atendimento["duracao_simulada_seg"] == iniciado.json()["duracao_simulada_seg"]
    assert consultar(ambiente, "SELECT estado FROM senhas WHERE id = %s", (senha["id"],))[0]["estado"] == "ATENDIDA"


def test_fluxo_de_nao_comparecimento(cliente, ambiente, relogio, atendente1):
    senha = emitir(cliente, "SP")
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)

    segunda = acao(cliente, atendente1, senha["id"], "chamar-novamente")
    corpo = segunda.json()
    assert segunda.status_code == 200 and corpo["senha"]["estado"] == "CHAMADA_NOVAMENTE"
    assert corpo["chamada"]["numero"] == 2 and corpo["chamada"]["ultima_chamada"] is True
    assert corpo["texto_chamada"] == "Última chamada. Senha prioritária zero zero um, guichê um"

    final = acao(cliente, atendente1, senha["id"], "nao-compareceu")
    assert final.status_code == 200 and final.json()["estado"] == "NAO_COMPARECEU"
    linha = consultar(ambiente, "SELECT estado, motivo_descarte FROM senhas WHERE id = %s", (senha["id"],))[0]
    assert (linha["estado"], linha["motivo_descarte"]) == ("NAO_COMPARECEU", "ABANDONO")
    assert len(consultar(ambiente, "SELECT id FROM chamadas WHERE senha_id = %s", (senha["id"],))) == 2
    assert ("CHAMADA", "CHAMADA_NOVAMENTE", "ATENDENTE") in historico(ambiente, senha["id"])
    assert historico(ambiente, senha["id"])[-1] == ("CHAMADA_NOVAMENTE", "NAO_COMPARECEU", "ATENDENTE")
    assert consultar(ambiente, "SELECT id FROM atendimentos") == []  # nunca foi atendida


def test_cliente_aparece_na_segunda_chamada_e_e_atendido(cliente, relogio, atendente1):
    senha = emitir(cliente, "SE")
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)
    acao(cliente, atendente1, senha["id"], "chamar-novamente")
    assert acao(cliente, atendente1, senha["id"], "iniciar-atendimento").status_code == 200  # CHAMADA_NOVAMENTE -> EM_ATENDIMENTO
    assert acao(cliente, atendente1, senha["id"], "encerrar-atendimento").json()["estado"] == "ATENDIDA"


def test_transicoes_invalidas_dao_409(cliente, relogio, atendente1):
    aguardando = emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)
    for nome in ("iniciar-atendimento", "encerrar-atendimento", "chamar-novamente", "nao-compareceu"):
        resposta = acao(cliente, atendente1, aguardando["id"], nome)  # ainda AGUARDANDO
        assert resposta.status_code == 409 and resposta.json()["codigo"] == "TRANSICAO_INVALIDA", nome

    chamar(cliente, atendente1)  # agora CHAMADA
    assert acao(cliente, atendente1, aguardando["id"], "encerrar-atendimento").json()["codigo"] == "TRANSICAO_INVALIDA"
    assert acao(cliente, atendente1, aguardando["id"], "nao-compareceu").json()["codigo"] == "TRANSICAO_INVALIDA"
    assert acao(cliente, atendente1, aguardando["id"], "chamar-novamente").status_code == 200
    assert acao(cliente, atendente1, aguardando["id"], "chamar-novamente").json()["codigo"] == "TRANSICAO_INVALIDA"  # RN-15


def test_senha_inexistente_e_404(cliente, relogio, atendente1):
    resposta = acao(cliente, atendente1, 9999, "iniciar-atendimento")
    assert resposta.status_code == 404 and resposta.json()["codigo"] == "NAO_ENCONTRADO"


def test_so_quem_chamou_mexe_na_senha_mas_o_gestor_supervisiona(cliente, relogio, atendente1, atendente2, gestor):
    senha = emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)
    ocupar(cliente, atendente2, 2)
    chamar(cliente, atendente1)
    intruso = acao(cliente, atendente2, senha["id"], "iniciar-atendimento")
    assert intruso.status_code == 403 and intruso.json()["codigo"] == "SEM_PERMISSAO"
    assert acao(cliente, gestor, senha["id"], "iniciar-atendimento").status_code == 200


# ------------------------------------------------------ erros ao chamar

def test_chamar_sem_guiche(cliente, relogio, atendente1):
    emitir(cliente, "SG")
    resposta = chamar(cliente, atendente1)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "ATENDENTE_SEM_GUICHE"


def test_fila_vazia(cliente, relogio, atendente1):
    ocupar(cliente, atendente1, 1)
    resposta = chamar(cliente, atendente1)
    assert resposta.status_code == 404 and resposta.json()["codigo"] == "FILA_VAZIA"


def test_guiche_com_senha_ativa_nao_chama_outra(cliente, relogio, atendente1):
    primeira, _ = emitir(cliente, "SG"), emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)
    bloqueada = chamar(cliente, atendente1)
    assert bloqueada.status_code == 409 and bloqueada.json()["codigo"] == "GUICHE_COM_SENHA_ATIVA"
    acao(cliente, atendente1, primeira["id"], "iniciar-atendimento")
    assert chamar(cliente, atendente1).json()["codigo"] == "GUICHE_COM_SENHA_ATIVA"  # EM_ATENDIMENTO também prende
    acao(cliente, atendente1, primeira["id"], "encerrar-atendimento")
    assert chamar(cliente, atendente1).status_code == 200  # liberou


def test_chamar_fora_do_expediente(cliente, relogio, atendente1):
    emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)
    relogio.definir(6, 30)
    resposta = chamar(cliente, atendente1)
    assert resposta.status_code == 409 and resposta.json()["codigo"] == "FORA_DO_EXPEDIENTE"


# ------------------------------------------------------- alternância (ADR-003)

def test_alternancia_pela_api(cliente, relogio, atendente1):
    for tipo in ("SG", "SE", "SP", "SG", "SE", "SP"):  # ordem de chegada embaralhada de propósito
        emitir(cliente, tipo)
    ocupar(cliente, atendente1, 1)
    chamadas = [atender(cliente, atendente1)["senha"]["numero"] for _ in range(6)]
    assert chamadas == [f"{PREFIXO}-SP001", f"{PREFIXO}-SE001", f"{PREFIXO}-SP002",
                        f"{PREFIXO}-SE002", f"{PREFIXO}-SG001", f"{PREFIXO}-SG002"]
    assert chamar(cliente, atendente1).json()["codigo"] == "FILA_VAZIA"


# ------------------------------------------------------------ painel e resumo

def test_painel_mostra_as_5_ultimas_e_nunca_a_proxima(cliente, relogio, atendente1):
    for _ in range(7):
        emitir(cliente, "SG")
    ocupar(cliente, atendente1, 1)
    for _ in range(6):
        atender(cliente, atendente1)
    painel = cliente.get(f"{API}/painel").json()
    numeros = [i["numero"] for i in painel["ultimas"]]
    assert numeros == [f"{PREFIXO}-SG00{n}" for n in (6, 5, 4, 3, 2)]  # 5 itens, mais recente primeiro
    assert f"{PREFIXO}-SG007" not in numeros  # a sétima ainda aguarda: nunca aparece (RN-09)
    assert painel["ultimas"][0] == {"numero": f"{PREFIXO}-SG006", "tipo": "SG", "sequencial": 6, "guiche": 1,
                                    "chamada": 1, "ultima_chamada": False, "chamada_em": "2026-11-27T10:00:00-03:00",
                                    "texto_chamada": "Senha geral zero zero seis, guichê um"}
    assert painel["atualizado_em"].startswith("2026-11-27T10:00")


def test_senha_chamada_duas_vezes_aparece_uma_vez_com_a_ultima_chamada(cliente, relogio, atendente1):
    senha = emitir(cliente, "SP")
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)
    acao(cliente, atendente1, senha["id"], "chamar-novamente")
    itens = cliente.get(f"{API}/painel").json()["ultimas"]
    assert len(itens) == 1 and itens[0]["chamada"] == 2 and itens[0]["ultima_chamada"] is True


def test_painel_vazio(cliente, relogio):
    emitir(cliente, "SP")  # emitida, mas ninguém chamou
    assert cliente.get(f"{API}/painel").json()["ultimas"] == []


def test_resumo_da_fila(cliente, relogio, atendente1):
    assert cliente.get(f"{API}/fila/resumo", headers=atendente1).json() == {"SP": 0, "SE": 0, "SG": 0}
    for tipo in ("SG", "SG", "SP"):
        emitir(cliente, tipo)
    assert cliente.get(f"{API}/fila/resumo", headers=atendente1).json() == {"SP": 1, "SE": 0, "SG": 2}
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)  # chama a SP
    assert cliente.get(f"{API}/fila/resumo", headers=atendente1).json() == {"SP": 0, "SE": 0, "SG": 2}


# --------------------------------------------------- fim do expediente (RN-10)

def test_descarte_as_17h_so_pega_quem_aguarda(cliente, ambiente, relogio, atendente1):
    em_curso, *aguardando = [emitir(cliente, "SG") for _ in range(3)]
    ocupar(cliente, atendente1, 1)
    chamar(cliente, atendente1)  # SG001 fica CHAMADA

    relogio.definir(17, 5)
    assert cliente.get(f"{API}/fila/resumo", headers=atendente1).json() == {"SP": 0, "SE": 0, "SG": 0}  # 1ª requisição após as 17h

    for senha in aguardando:
        linha = consultar(ambiente, "SELECT estado, motivo_descarte FROM senhas WHERE id = %s", (senha["id"],))[0]
        assert (linha["estado"], linha["motivo_descarte"]) == ("NAO_COMPARECEU", "FIM_EXPEDIENTE")
        assert historico(ambiente, senha["id"])[-1] == ("AGUARDANDO", "NAO_COMPARECEU", "SISTEMA")
    assert consultar(ambiente, "SELECT estado FROM senhas WHERE id = %s", (em_curso["id"],))[0]["estado"] == "CHAMADA"

    # o que já estava em curso pode ser concluído depois das 17h
    assert acao(cliente, atendente1, em_curso["id"], "iniciar-atendimento").status_code == 200
    assert acao(cliente, atendente1, em_curso["id"], "encerrar-atendimento").json()["estado"] == "ATENDIDA"

    # ...mas não entra senha nova nem se chama outra
    assert cliente.post(f"{API}/senhas", json={"tipo": "SG"}).json()["codigo"] == "FORA_DO_EXPEDIENTE"
    assert chamar(cliente, atendente1).json()["codigo"] == "FORA_DO_EXPEDIENTE"


def test_descarte_e_idempotente(cliente, ambiente, relogio, atendente1):
    emitir(cliente, "SP")
    relogio.definir(17, 0)
    cliente.get(f"{API}/painel")
    cliente.get(f"{API}/painel")
    cliente.get(f"{API}/fila/resumo", headers=atendente1)
    assert len(consultar(ambiente, "SELECT id FROM senha_historico WHERE estado_novo = 'NAO_COMPARECEU'")) == 1


def test_antes_das_17h_nada_e_descartado(cliente, ambiente, relogio, atendente1):
    emitir(cliente, "SP")
    relogio.definir(16, 59)
    cliente.get(f"{API}/fila/resumo", headers=atendente1)
    assert consultar(ambiente, "SELECT estado FROM senhas")[0]["estado"] == "AGUARDANDO"
