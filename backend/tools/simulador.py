"""Simulador de um dia de atendimento, usando só a API (ADR-004, RF-19).

Emite senhas ao longo do "dia", e atendentes (uma thread cada) ocupam guichês, chamam, atendem e encerram.
Em ~5% das senhas o cliente não aparece: duas chamadas e `nao-compareceu`. O tempo de atendimento é o
`duracao_simulada_seg` sorteado pela API (RN-07), acelerado por `--velocidade`. Serve para gerar volume
para os relatórios e para mostrar a concorrência ao vivo na demonstração.

Pré-requisitos: API no ar, seed aplicado e, fora das 07h–17h, `EXPEDIENTE_FORCAR_ABERTO=true` na API.

Exemplos:
    python -m tools.simulador                                  # 60 senhas, 3 guichês, 120x
    python -m tools.simulador --senhas 120 --velocidade 600    # um dia "cheio" em poucos minutos
"""
import argparse
import random
import sys
import threading
import time

TAXA_NAO_COMPARECIMENTO = 0.05
# Mistura de tipos que chegam (proporção do exemplo do contrato: SP 1/6, SE 1/3, SG 1/2)
TIPOS = ("SG", "SE", "SP")
PESOS = (0.50, 0.33, 0.17)
API = "/api/v1"


def decidir_desfecho(rng: random.Random, taxa: float = TAXA_NAO_COMPARECIMENTO) -> str:
    """'NAO_COMPARECEU' em ~5% dos casos; senão 'ATENDIDA'."""
    return "NAO_COMPARECEU" if rng.random() < taxa else "ATENDIDA"


def sortear_tipo(rng: random.Random) -> str:
    return rng.choices(TIPOS, weights=PESOS, k=1)[0]


class Placar:
    """Contadores compartilhados entre as threads."""

    def __init__(self):
        self._trava = threading.Lock()
        self.dados = {"emitidas": 0, "atendidas": 0, "nao_compareceu": 0, "erros": 0}
        self.por_tipo = {t: 0 for t in TIPOS}

    def somar(self, chave: str, tipo: str | None = None) -> None:
        with self._trava:
            self.dados[chave] += 1
            if tipo:
                self.por_tipo[tipo] += 1


def _codigo(resposta) -> str | None:
    try:
        return resposta.json().get("codigo")
    except ValueError:
        return None


def _emitir(base, total, velocidade, rng, placar, terminou, parar):
    import httpx

    with httpx.Client(base_url=base, timeout=30) as http:
        for i in range(total):
            if parar.is_set():
                break
            tipo = sortear_tipo(rng)
            resposta = http.post(f"{API}/senhas", json={"tipo": tipo})
            if resposta.status_code == 201:
                placar.somar("emitidas", tipo)
                print(f"  [totem] emitiu {resposta.json()['numero']}")
            else:
                print(f"  [totem] ERRO {resposta.status_code} {_codigo(resposta)}: {resposta.text[:120]}")
                placar.somar("erros")
                if _codigo(resposta) == "FORA_DO_EXPEDIENTE":
                    print("  → Fora do expediente. Suba a API com EXPEDIENTE_FORCAR_ABERTO=true para simular.")
                    parar.set()
                    break
            time.sleep(rng.uniform(20, 90) / velocidade)  # chegada a cada 20–90 s simulados
    terminou.set()


def _atender(base, email, senha, indice, velocidade, rng, placar, emissao_terminou, parar):
    import httpx

    nome = email.split("@")[0]
    with httpx.Client(base_url=base, timeout=30) as http:
        login = http.post(f"{API}/auth/login", json={"email": email, "senha": senha})
        if login.status_code != 200:
            print(f"  [{nome}] login falhou: {login.status_code} {_codigo(login)}")
            placar.somar("erros")
            return
        http.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

        guiche = None
        livres = http.get(f"{API}/guiches", params={"livres": "true"}).json()
        for livre in livres[indice:] + livres[:indice]:  # cada atendente começa por um guichê diferente
            if http.post(f"{API}/guiches/{livre['id']}/ocupar").status_code == 200:
                guiche = livre
                break
        if guiche is None:
            print(f"  [{nome}] nenhum guichê livre")
            placar.somar("erros")
            return
        print(f"  [{nome}] ocupou o guichê {guiche['numero']}")

        try:
            while not parar.is_set():
                chamada = http.post(f"{API}/atendimentos/chamar-proximo")
                if chamada.status_code == 404:  # FILA_VAZIA
                    if emissao_terminou.is_set():
                        break
                    time.sleep(0.3)
                    continue
                if chamada.status_code != 200:
                    print(f"  [{nome}] ERRO ao chamar: {chamada.status_code} {_codigo(chamada)}")
                    placar.somar("erros")
                    if _codigo(chamada) == "FORA_DO_EXPEDIENTE":
                        break
                    time.sleep(1)
                    continue
                corpo = chamada.json()
                senha_id, numero = corpo["senha"]["id"], corpo["senha"]["numero"]
                print(f"  [{nome}] guichê {guiche['numero']}: {corpo['texto_chamada']}")

                if decidir_desfecho(rng) == "NAO_COMPARECEU":
                    time.sleep(rng.uniform(10, 30) / velocidade)
                    http.post(f"{API}/senhas/{senha_id}/chamar-novamente")
                    time.sleep(rng.uniform(10, 30) / velocidade)
                    http.post(f"{API}/senhas/{senha_id}/nao-compareceu")
                    placar.somar("nao_compareceu")
                    print(f"  [{nome}] {numero}: não compareceu")
                else:
                    inicio = http.post(f"{API}/senhas/{senha_id}/iniciar-atendimento")
                    duracao = inicio.json().get("duracao_simulada_seg", 60)
                    time.sleep(duracao / velocidade)
                    http.post(f"{API}/senhas/{senha_id}/encerrar-atendimento")
                    placar.somar("atendidas")
                    print(f"  [{nome}] {numero}: atendida ({duracao}s simulados)")
        finally:
            http.post(f"{API}/guiches/{guiche['id']}/liberar")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Simula um dia de atendimento pela API.")
    ap.add_argument("--url", default="http://localhost:8000", help="endereço da API")
    ap.add_argument("--senhas", type=int, default=60, help="quantas senhas emitir (padrão 60)")
    ap.add_argument("--velocidade", type=float, default=120, help="fator de aceleração do tempo (padrão 120x)")
    ap.add_argument("--guiches", type=int, default=3, choices=(1, 2, 3), help="atendentes simultâneos (padrão 3)")
    ap.add_argument("--semente", type=int, default=None, help="semente do sorteio (resultado repetível)")
    ap.add_argument("--senha-atendente", default="Atendente@123", help="senha do seed dos atendentes")
    ap.add_argument("--senha-gestor", default="Gestor@123", help="senha do seed do gestor (3º atendente)")
    args = ap.parse_args(argv)
    if args.senhas < 1 or args.velocidade <= 0:
        ap.error("--senhas deve ser ≥ 1 e --velocidade > 0")

    try:
        import httpx  # noqa: F401
    except ImportError:
        sys.exit("Falta o httpx: pip install -r requirements.txt")

    contas = [("atendente1@nassau.local", args.senha_atendente), ("atendente2@nassau.local", args.senha_atendente),
              ("gestor@nassau.local", args.senha_gestor)][:args.guiches]
    base_rng = random.Random(args.semente)
    placar, emissao_terminou, parar = Placar(), threading.Event(), threading.Event()
    print(f"Simulando {args.senhas} senhas com {len(contas)} guichê(s), {args.velocidade:g}x, em {args.url}")

    inicio = time.perf_counter()
    threads = [threading.Thread(target=_emitir, daemon=True, args=(
        args.url, args.senhas, args.velocidade, random.Random(base_rng.random()), placar, emissao_terminou, parar))]
    for i, (email, senha) in enumerate(contas):
        threads.append(threading.Thread(target=_atender, daemon=True, args=(
            args.url, email, senha, i, args.velocidade, random.Random(base_rng.random()), placar,
            emissao_terminou, parar)))
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        parar.set()
        print("\nInterrompido.")

    d = placar.dados
    print("\n=== Resumo da simulação ===")
    print(f"Emitidas: {d['emitidas']}  (SP {placar.por_tipo['SP']} · SE {placar.por_tipo['SE']} · SG {placar.por_tipo['SG']})")
    print(f"Atendidas: {d['atendidas']} · Não compareceram: {d['nao_compareceu']} · Erros: {d['erros']}")
    print(f"Duração real: {time.perf_counter() - inicio:.1f} s")
    print("Veja os números nos relatórios do gestor: GET /api/v1/relatorios/diario/resumo")
    return 1 if d["erros"] else 0


if __name__ == "__main__":
    sys.exit(main())
