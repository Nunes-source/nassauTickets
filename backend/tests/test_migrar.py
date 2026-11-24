from database.migrar import dividir_sql


def test_dividir_sql_ignora_comentarios_e_separa_comandos():
    texto = """
    -- comentário no início
    CREATE TABLE a (
      id INT,   -- comentário no meio
      nome VARCHAR(10)
    );
    CREATE TABLE b (id INT);
    """
    comandos = dividir_sql(texto)
    assert len(comandos) == 2
    assert comandos[0].startswith("CREATE TABLE a")
    assert "comentário" not in comandos[0]
    assert comandos[1] == "CREATE TABLE b (id INT)"


def test_o_schema_base_tem_as_tres_tabelas():
    from pathlib import Path

    comandos = dividir_sql((Path(__file__).parents[1] / "database/schema/01_base.sql").read_text(encoding="utf-8"))
    nomes = [c.split()[2] for c in comandos]
    assert nomes == ["usuarios", "guiches", "log_acesso"]
