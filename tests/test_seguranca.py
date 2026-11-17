import pytest

from app.exceptions import ValorInvalido
from app.security import LIMITE_DE_BYTES_DO_BCRYPT, HashDeSenha
from tests.conftest import hasher

# ------------------------------------------------------------------ o contrato


def test_hash_bcrypt_cumpre_o_contrato(hasher):
    assert isinstance(hasher, HashDeSenha)


def test_contrato_nao_pode_ser_instanciado_direto():
    with pytest.raises(TypeError):
        HashDeSenha()


def test_implementacao_incompleta_nao_pode_ser_instanciada():
    class HashPelaMetade(HashDeSenha):
        def gerar(self, senha: str) -> str:
            return senha

    # `verificar` ficou de fora de propósito
    with pytest.raises(TypeError):
        HashPelaMetade()


# --------------------------------------------------------------- RN-05: a senha

def test_hash_nao_e_a_senha_em_texto_puro(hasher):
    assert hasher.gerar("senha123") != "senha123"


def test_mesma_senha_gera_hashes_diferentes(hasher):
    assert hasher.gerar("senha123") != hasher.gerar("senha123")


def test_hash_gerado_confere_com_a_senha(hasher):
    assert hasher.verificar("senha123", hasher.gerar("senha123")) is True


def test_senha_errada_nao_confere(hasher):
    assert hasher.verificar("errada", hasher.gerar("senha123")) is False


def test_hash_cabe_na_coluna_do_banco(hasher):
    assert len(hasher.gerar("senha123")) == 60

# ------------------------------------------------------- o limite de 72 *bytes*

def test_senha_no_limite_de_bytes_e_aceita(hasher):
    senha = "a" * LIMITE_DE_BYTES_DO_BCRYPT
    assert hasher.verificar(senha, hasher.gerar(senha)) is True

def test_senha_acima_do_limite_de_bytes_e_recusada(hasher):
    with pytest.raises(ValorInvalido):
        hasher.gerar("a" * (LIMITE_DE_BYTES_DO_BCRYPT + 1))

def test_o_limite_conta_bytes_e_nao_caracteres(hasher):   
    senha = "ã" * 40
    assert len(senha) < LIMITE_DE_BYTES_DO_BCRYPT
    assert len(senha.encode("utf-8")) > LIMITE_DE_BYTES_DO_BCRYPT
    with pytest.raises(ValorInvalido):
        hasher.gerar(senha)
# ---------------------------------------------------------- entrada malformada

def test_hash_invalido_nao_derruba_a_verificacao(hasher):
    assert hasher.verificar("senha123", "isto-nao-e-um-hash") is False