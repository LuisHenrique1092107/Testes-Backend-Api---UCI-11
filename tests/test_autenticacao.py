from datetime import timedelta
import token
import jwt
import pytest
from app.exceptions import NaoAutenticado, SessaoExpirada
from app.tokens import ALGORITMO, TokenDeAcesso

#: Segredo próprio deste arquivo, com mais de 32 bytes.

SEGREDO = "segredo-de-teste-com-mais-de-trinta-e-dois-bytes"
@pytest.fixture
def tokens() -> TokenDeAcesso:
    return TokenDeAcesso(segredo=SEGREDO, validade=timedelta(hours=1))

# =============================================================================
# Dia 4 — a mecânica do token, sem HTTP
# =============================================================================

def test_token_emitido_devolve_o_mesmo_usuario(tokens: TokenDeAcesso):
    assert tokens.ler(tokens.emitir(42)) == 42

def test_token_nao_e_o_id_em_texto_puro(tokens: TokenDeAcesso):
    assert tokens.emitir(42) != "42"
    assert len(tokens.emitir(42)) > 40

def test_token_assinado_com_outro_segredo_e_recusado(tokens: TokenDeAcesso):
    intruso = TokenDeAcesso(
        segredo="outro-segredo-tambem-com-trinta-e-dois-bytes",
        validade=timedelta(hours=1),
    )
    with pytest.raises(NaoAutenticado):
        tokens.ler(intruso.emitir(42))

def test_token_alterado_e_recusado(tokens: TokenDeAcesso):
    token = tokens.emitir(42)
    adulterado = token[:-2] + ("ab" if not token.endswith("ab") else "cd")
    with pytest.raises(NaoAutenticado):
        tokens.ler(adulterado)


@pytest.mark.parametrize(
    "texto_invalido", ["", " ", "nao-e-um-token", "a.b.c", "Bearer abc"]
)

def test_texto_que_nao_e_token_e_recusado(
 tokens: TokenDeAcesso, texto_invalido: str
):
    with pytest.raises(NaoAutenticado):
        tokens.ler(texto_invalido)
 
 
def test_token_expirado_e_recusado_com_excecao_propria(tokens: TokenDeAcesso):
    vencido = TokenDeAcesso(segredo=SEGREDO, validade=timedelta(seconds=-10))
    with pytest.raises(SessaoExpirada):
        tokens.ler(vencido.emitir(42))
def test_sessao_expirada_tambem_e_nao_autenticado():
    assert issubclass(SessaoExpirada, NaoAutenticado)

def test_token_sem_sub_utilizavel_e_recusado(tokens: TokenDeAcesso):
    sem_sub = jwt.encode({"outro": "campo"}, SEGREDO, algorithm=ALGORITMO)
    with pytest.raises(NaoAutenticado):
        tokens.ler(sem_sub)

def test_token_nao_guarda_dados_pessoais(tokens: TokenDeAcesso):
    conteudo = jwt.decode(tokens.emitir(42), SEGREDO, algorithms=[ALGORITMO])
    assert set(conteudo) == {"sub", "iat", "exp"}
