import pytest
from app.config import (
 CAMINHO_DO_ENV,
 ORIGENS_PADRAO,
 RAIZ_DO_PROJETO,
 SEGREDO_DE_EXEMPLO,
 TAMANHO_MINIMO_DO_SEGREDO,
 Configuracao,
 normalizar_url,
)


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

# =============================================================================
# Dia 6 — `monkeypatch`: a DATABASE_URL é obrigatória
# =============================================================================

def test_sem_database_url_a_aplicacao_recusa_subir(monkeypatch): 
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        Configuracao.do_ambiente()
        
@pytest.mark.parametrize("valor_vazio", ["", " "])
def test_database_url_vazia_conta_como_ausente(monkeypatch, valor_vazio):
    monkeypatch.setenv("DATABASE_URL", valor_vazio)
    with pytest.raises(RuntimeError):
        Configuracao.do_ambiente()
        
def test_a_mensagem_de_erro_diz_onde_o_env_foi_procurado(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL") as erro:
        Configuracao.do_ambiente()
    assert str(CAMINHO_DO_ENV) in str(erro.value)
