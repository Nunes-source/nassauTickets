from datetime import date, datetime, timezone

from app.core import tempo
from app.core.tempo import FUSO


def _hora(h, m=0, s=0):
    return datetime(2026, 11, 27, h, m, s, tzinfo=FUSO)


def test_expediente_vai_de_07h_ate_antes_das_17h():
    assert not tempo.dentro_do_expediente(_hora(6, 59, 59))
    assert tempo.dentro_do_expediente(_hora(7, 0, 0))
    assert tempo.dentro_do_expediente(_hora(16, 59, 59))
    assert not tempo.dentro_do_expediente(_hora(17, 0, 0))


def test_expediente_converte_outro_fuso_para_recife():
    # 10:00 UTC = 07:00 em Recife (UTC-3)
    assert tempo.dentro_do_expediente(datetime(2026, 11, 27, 10, 0, tzinfo=timezone.utc))
    assert not tempo.dentro_do_expediente(datetime(2026, 11, 27, 9, 59, tzinfo=timezone.utc))


def test_agora_e_hoje_usam_o_fuso_de_recife():
    assert tempo.agora().tzinfo is FUSO
    assert isinstance(tempo.hoje(), date)


def test_horas_de_expediente():
    assert tempo.horas_de_expediente() == 10.0


def test_com_fuso_anexa_recife_ao_datetime_do_banco():
    naive = datetime(2026, 11, 27, 9, 15, 2)
    resultado = tempo.com_fuso(naive)
    assert resultado.isoformat() == "2026-11-27T09:15:02-03:00"
    assert tempo.com_fuso(None) is None
