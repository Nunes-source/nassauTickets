"""Concorrência (RNF-03, ADR-002): vários guichês chamando ao mesmo tempo nunca repetem senha
e a alternância se mantém. Usa os services direto, com uma conexão por thread (como um servidor real)."""
import threading
from concurrent.futures import ThreadPoolExecutor

from app.core.db import conectar
from app.core.errors import ErroNegocio
from app.core.security import UsuarioAtual
from app.repositories import guiches as repo_guiches
from app.repositories import usuarios as repo_usuarios
from app.services import atendimento, emissao
from app.services.fila import escolher_tipo
from tests.conftest import consultar

GUICHES = 6
POR_TIPO = 8


def _criar_atendentes_e_guiches(banco, quantidade):
    """Cria `quantidade` atendentes, cada um ocupando um guichê novo (nº 11, 12, ...)."""
    atendentes = []
    for i in range(quantidade):
        usuario_id = repo_usuarios.inserir(banco, f"Atendente de teste {i}", f"teste{i}@nassau.local", "hash-falso", "ATENDENTE")
        guiche_id = repo_guiches.inserir(banco, 11 + i)
        repo_guiches.definir_ocupante(banco, guiche_id, usuario_id)
        atendentes.append(UsuarioAtual(id=usuario_id, nome=f"Atendente de teste {i}", perfil="ATENDENTE"))
    banco.commit()
    return atendentes


def _emitir(banco, quantidades: dict[str, int]):
    for tipo, quantidade in quantidades.items():
        for _ in range(quantidade):
            emissao.emitir_senha(banco, tipo)


def test_varios_guiches_chamando_juntos_nao_repetem_senha_e_mantem_a_alternancia(ambiente, relogio):
    _emitir(ambiente, {"SP": POR_TIPO, "SE": POR_TIPO, "SG": POR_TIPO})
    atendentes = _criar_atendentes_e_guiches(ambiente, GUICHES)
    total = 3 * POR_TIPO
    erros, chamadas_por_guiche = [], []
    largada = threading.Barrier(GUICHES)

    def trabalhar(usuario):
        conn = conectar()
        try:
            largada.wait()  # todos começam no mesmo instante
            while True:
                try:
                    chamada = atendimento.chamar_proximo(conn, usuario)
                except ErroNegocio as erro:
                    if erro.codigo == "FILA_VAZIA":
                        return
                    raise
                senha_id = chamada["senha"]["id"]
                chamadas_por_guiche.append((chamada["guiche"]["numero"], senha_id))
                atendimento.iniciar_atendimento(conn, usuario, senha_id)    # libera o guichê (RN-12)
                atendimento.encerrar_atendimento(conn, usuario, senha_id)
        except Exception as erro:  # noqa: BLE001 - qualquer falha deve reprovar o teste
            erros.append(repr(erro))
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=GUICHES) as pool:
        list(pool.map(trabalhar, atendentes))

    assert erros == []

    # 1) zero duplicidade: cada senha foi chamada exatamente uma vez
    ids_chamados = [senha_id for _, senha_id in chamadas_por_guiche]
    assert len(ids_chamados) == total and len(set(ids_chamados)) == total
    assert consultar(ambiente, "SELECT COUNT(*) AS n FROM chamadas")[0]["n"] == total
    assert consultar(ambiente, "SELECT COUNT(*) AS n FROM senhas WHERE estado = 'ATENDIDA'")[0]["n"] == total
    assert len({g for g, _ in chamadas_por_guiche}) > 1  # de fato mais de um guichê trabalhou

    # 2) alternância mantida: refaz a decisão a cada chamada, na ordem em que o banco as gravou
    ordem = consultar(ambiente, "SELECT s.tipo, s.sequencia FROM chamadas c JOIN senhas s ON s.id = c.senha_id ORDER BY c.id")
    restantes = {t: list(range(1, POR_TIPO + 1)) for t in ("SP", "SE", "SG")}
    ultimo = None
    for chamada in ordem:
        esperado = escolher_tipo(ultimo, {t for t, fila in restantes.items() if fila})
        assert chamada["tipo"] == esperado, f"alternância quebrada depois de {ultimo}"
        assert chamada["sequencia"] == restantes[esperado].pop(0), "senha fora da ordem de chegada"
        ultimo = esperado


def test_emissoes_simultaneas_geram_sequencia_unica_e_sem_buracos(ambiente, relogio):
    threads, por_thread = 8, 10
    numeros, erros = [], []

    def emitir_varias(_):
        conn = conectar()
        try:
            for _ in range(por_thread):
                numeros.append(emissao.emitir_senha(conn, "SG")["numero"])
        except Exception as erro:  # noqa: BLE001
            erros.append(repr(erro))
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(emitir_varias, range(threads)))

    assert erros == []
    total = threads * por_thread
    assert len(numeros) == total and len(set(numeros)) == total
    esperados = {f"261127-SG{n:03d}" for n in range(1, total + 1)}
    assert set(numeros) == esperados  # 001..080, sem repetir nem pular
    assert consultar(ambiente, "SELECT ultimo_seq FROM contadores_senha WHERE tipo = 'SG'")[0]["ultimo_seq"] == total


def test_dois_cliques_no_mesmo_guiche_so_chamam_uma_senha(ambiente, relogio):
    """O atendente aperta 'chamar próximo' duas vezes seguidas: a 2ª encontra o guichê ocupado (RN-12)."""
    _emitir(ambiente, {"SG": 4})
    [atendente] = _criar_atendentes_e_guiches(ambiente, 1)
    resultados = []
    largada = threading.Barrier(2)

    def clicar(_):
        conn = conectar()
        try:
            largada.wait()
            resultados.append(atendimento.chamar_proximo(conn, atendente)["senha"]["id"])
        except ErroNegocio as erro:
            resultados.append(erro.codigo)
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(clicar, range(2)))

    codigos = [r for r in resultados if isinstance(r, str)]
    assert codigos == ["GUICHE_COM_SENHA_ATIVA"] and len(resultados) == 2
    assert consultar(ambiente, "SELECT COUNT(*) AS n FROM chamadas")[0]["n"] == 1
