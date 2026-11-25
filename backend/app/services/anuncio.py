"""Texto da chamada para o áudio e para leitores de tela (RF-17, RNF-07)."""

_UNIDADES = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze",
             "doze", "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_DEZENAS = {2: "vinte", 3: "trinta", 4: "quarenta", 5: "cinquenta", 6: "sessenta", 7: "setenta",
            8: "oitenta", 9: "noventa"}
_CENTENAS = {1: "cento", 2: "duzentos", 3: "trezentos", 4: "quatrocentos", 5: "quinhentos", 6: "seiscentos",
             7: "setecentos", 8: "oitocentos", 9: "novecentos"}
TIPO_POR_EXTENSO = {"SP": "prioritária", "SG": "geral", "SE": "exames"}


def por_extenso(n: int) -> str:
    """Número cardinal em português, de 0 a 999 (usado no número do guichê)."""
    if not 0 <= n <= 999:
        raise ValueError("só de 0 a 999")
    if n < 20:
        return _UNIDADES[n]
    if n < 100:
        dezena, unidade = divmod(n, 10)
        return _DEZENAS[dezena] + (f" e {_UNIDADES[unidade]}" if unidade else "")
    if n == 100:
        return "cem"
    centena, resto = divmod(n, 100)
    return _CENTENAS[centena] + (f" e {por_extenso(resto)}" if resto else "")


def sequencial_por_extenso(sequencial: int) -> str:
    """Dígito a dígito, como se fala numa chamada: 1 -> 'zero zero um'; 123 -> 'um dois três'."""
    return " ".join(_UNIDADES[int(d)] for d in f"{sequencial:03d}")


def texto_chamada(tipo: str, sequencial: int, guiche: int, ultima_chamada: bool) -> str:
    texto = f"Senha {TIPO_POR_EXTENSO[tipo]} {sequencial_por_extenso(sequencial)}, guichê {por_extenso(guiche)}"
    return f"Última chamada. {texto}" if ultima_chamada else texto
