
from fastapi.testclient import TestClient


USUARIO_VALIDO = {
    "nome": "Bruno Lima",
    "email": "bruno@exemplo.com",
    "senha": "senha123",
}

# =============================================================================
# Dia 7 — `TestClient`: os endpoints públicos
# =============================================================================

def test_raiz_responde(cliente: TestClient):
    assert cliente.get("/").status_code == 200


def test_cadastrar_usuario_devolve_201_com_sessao_aberta(cliente: TestClient):
    resposta = cliente.post("/usuarios", json=USUARIO_VALIDO)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["accessToken"]
    assert corpo["tokenType"] == "bearer"
    assert corpo["usuario"]["nome"] == "Bruno Lima"
    assert "criadoEm" in corpo["usuario"]


def test_cadastro_nao_expoe_a_senha(cliente: TestClient):
    resposta = cliente.post("/usuarios", json=USUARIO_VALIDO)
    inteiro = resposta.text
    assert "senha123" not in inteiro
    assert "senhaHash" not in inteiro and "senha_hash" not in inteiro


def test_cadastrar_com_email_repetido_devolve_409(cliente: TestClient):
    cliente.post("/usuarios", json=USUARIO_VALIDO)
    resposta = cliente.post("/usuarios", json=USUARIO_VALIDO)
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "E-mail já cadastrado."


def test_email_duplicado_ignora_maiusculas_e_espacos(cliente: TestClient):
    cliente.post("/usuarios", json=USUARIO_VALIDO)
    resposta = cliente.post(
        "/usuarios", json={**USUARIO_VALIDO, "email": " BRUNO@Exemplo.com "}
    )
    assert resposta.status_code == 409


def test_email_malformado_devolve_422(cliente: TestClient):
    resposta = cliente.post("/usuarios", json={**USUARIO_VALIDO, "email": "bruno@"})
    assert resposta.status_code == 422


def test_senha_curta_devolve_422(cliente: TestClient):
    resposta = cliente.post("/usuarios", json={**USUARIO_VALIDO, "senha": "123"})
    assert resposta.status_code == 422


def test_login_correto_devolve_200_com_token(cliente: TestClient, usuario: dict):
    resposta = cliente.post(
        "/usuarios/login", json={"email": "ana@exemplo.com", "senha": "senha123"}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["usuario"]["id"] == usuario["id"]
    assert corpo["accessToken"]


def test_login_com_senha_errada_devolve_401(cliente: TestClient, usuario: dict):
    resposta = cliente.post(
        "/usuarios/login", json={"email": "ana@exemplo.com", "senha": "errada"}
    )
    assert resposta.status_code == 401


def test_login_com_email_inexistente_devolve_401_com_a_mesma_mensagem(
    cliente: TestClient, usuario: dict
):
    inexistente = cliente.post(
        "/usuarios/login", json={"email": "ninguem@exemplo.com", "senha": "senha123"}
    )
    senha_errada = cliente.post(
        "/usuarios/login", json={"email": "ana@exemplo.com", "senha": "errada"}
    )
    assert inexistente.status_code == senha_errada.status_code == 401
    assert inexistente.json()["detail"] == senha_errada.json()["detail"]


def test_nao_existe_mais_busca_de_usuario_por_id(cliente: TestClient):
    assert cliente.get("/usuarios/1").status_code == 404
    assert cliente.get("/usuarios/9999").status_code == 404


def test_consultar_a_propria_conta_exige_token(cliente: TestClient):
    assert cliente.get("/usuarios/eu").status_code == 401


def test_openapi_expoe_os_sete_endpoints(cliente: TestClient):
    caminhos = cliente.get("/openapi.json").json()["paths"]
    operacoes = sum(len(metodos) for metodos in caminhos.values())
    assert operacoes == 8
