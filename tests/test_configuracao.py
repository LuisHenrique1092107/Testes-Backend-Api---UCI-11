import pytest
from app.config import normalizar_url

# =============================================================================
# Dia 3 — `parametrize` numa função pura: a normalização da URL
# =============================================================================


@pytest.mark.parametrize(
    "url_recebida",
    [
        "postgres://usuario:senha@host:5432/banco",
        "postgresql://usuario:senha@host:5432/banco",
    ],
)
def test_url_de_postgres_recebe_o_driver_do_projeto(url_recebida):
    normalizada = normalizar_url(url_recebida)
    assert normalizada.startswith("postgresql+psycopg://")
    assert normalizada.endswith("usuario:senha@host:5432/banco")


def test_driver_declarado_explicitamente_e_respeitado():
    url = "postgresql+psycopg2://usuario:senha@host:5432/banco"
    assert normalizar_url(url) == url


def test_url_de_sqlite_nao_e_alterada():
    assert normalizar_url("sqlite:///./todo_list.db") == "sqlite:///./todo_list.db"


def test_parametros_da_url_sao_preservados():
    url = "postgres://u:s@host:5432/banco?sslmode=require"
    assert normalizar_url(url).endswith("?sslmode=require")

