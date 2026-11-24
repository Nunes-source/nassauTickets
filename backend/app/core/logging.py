"""Logs estruturados em JSON com request_id (RNF-10)."""
import json
import logging
import time
import uuid

from fastapi import Request

from app.core.config import get_config
from app.core.errors import resposta_erro
from app.core.tempo import agora

logger = logging.getLogger("nassau.http")
_CAMPOS_EXTRAS = ("request_id", "metodo", "rota", "status", "duracao_ms")


class FormatadorJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        dados = {
            "ts": agora().isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensagem": record.getMessage(),
        }
        for campo in _CAMPOS_EXTRAS:
            if hasattr(record, campo):
                dados[campo] = getattr(record, campo)
        if record.exc_info:
            dados["excecao"] = self.formatException(record.exc_info)
        return json.dumps(dados, ensure_ascii=False)


def configurar_logging() -> None:
    manipulador = logging.StreamHandler()
    manipulador.setFormatter(FormatadorJson())
    raiz = logging.getLogger()
    raiz.handlers = [manipulador]
    raiz.setLevel(get_config().log_nivel)


async def middleware_requisicao(request: Request, call_next):
    """Gera o request_id, mede a duração e registra uma linha de log por requisição."""
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    inicio = time.perf_counter()
    try:
        resposta = await call_next(request)
    except Exception:
        logger.exception("erro não tratado", extra={"request_id": request_id})
        resposta = resposta_erro(request, "ERRO_INTERNO",
                                 "Erro interno. Informe o request_id ao suporte.", 500)
    resposta.headers["X-Request-ID"] = request_id
    rota = request.scope.get("route")
    logger.info("requisicao", extra={
        "request_id": request_id,
        "metodo": request.method,
        "rota": getattr(rota, "path", request.url.path),
        "status": resposta.status_code,
        "duracao_ms": round((time.perf_counter() - inicio) * 1000, 1),
    })
    return resposta
