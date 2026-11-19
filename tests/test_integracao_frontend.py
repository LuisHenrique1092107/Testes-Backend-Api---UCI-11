
from fastapi.testclient import TestClient

# =============================================================================
# Dia 7 — o contrato dos endpoints públicos
# =============================================================================
# ---------------------------------------------- campos — `@typedef Usuario`



def test_usuario_tem_exatamente_os_campos_publicos(usuario: dict):
    assert set(usuario) == {"id", "nome", "email", "criadoEm"}


def test_sessao_tem_os_campos_que_o_authcontext_vai_consumir(sessao_aberta: dict):
    assert set(sessao_aberta) == {"accessToken", "tokenType", "usuario"}
    assert sessao_aberta["tokenType"] == "bearer"


def test_cadastro_e_login_continuam_publicos(cliente: TestClient):
    cadastro = cliente.post(
        "/usuarios",
        json={"nome": "Carla", "email": "carla@exemplo.com", "senha": "senha123"},
    )
    assert cadastro.status_code == 201

    login = cliente.post(
        "/usuarios/login",
        json={"email": "carla@exemplo.com", "senha": "senha123"},
    )
    assert login.status_code == 200


# ------------------------------- formato do erro — `setErro(e.message)` no front

def test_erro_de_validacao_tem_detail_em_texto(cliente: TestClient):
    resposta = cliente.post(
        "/usuarios", json={"nome": "A", "email": "nao-e-email", "senha": "123"}
    )
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert isinstance(corpo["detail"], str)
    assert corpo["detail"].strip()


def test_erro_de_validacao_preserva_os_detalhes_em_erros(cliente: TestClient):
    resposta = cliente.post("/usuarios", json={"email": "nao-e-email"})
    corpo = resposta.json()
    assert isinstance(corpo["erros"], list)
    assert corpo["erros"]
    assert all("loc" in erro for erro in corpo["erros"])


def test_erro_de_negocio_tem_detail_em_texto(cliente: TestClient, usuario: dict):
    resposta = cliente.post(
        "/usuarios",
        json={"nome": "Outra", "email": usuario["email"], "senha": "senha123"},
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "E-mail já cadastrado."


def test_credencial_invalida_responde_401(cliente: TestClient, usuario: dict):
    resposta = cliente.post(
        "/usuarios/login", json={"email": usuario["email"], "senha": "errada"}
    )
    assert resposta.status_code == 401

# ------------------------------------- mensagens em pt-BR, prontas para a tela


def test_campo_obrigatorio_em_portugues(cliente: TestClient):
    resposta = cliente.post("/usuarios", json={})
    assert resposta.status_code == 422
    assert "campo obrigatório" in resposta.json()["detail"]


def test_tamanho_minimo_cita_o_numero(cliente: TestClient):
    resposta = cliente.post(
        "/usuarios", json={"nome": "A", "email": "ana@exemplo.com", "senha": "123"}
    )
    detalhe = resposta.json()["detail"]
    assert "nome: deve ter no mínimo 2 caracteres." in detalhe
    assert "senha: deve ter no mínimo 6 caracteres." in detalhe


def test_email_invalido_em_portugues(cliente: TestClient):
    resposta = cliente.post(
        "/usuarios",
        json={"nome": "Ana", "email": "nao-e-email", "senha": "senha123"},
    )
    assert "e-mail inválido" in resposta.json()["detail"]
