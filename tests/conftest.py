import os

import pytest
from fastapi.testclient import TestClient 
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "segredo-de-teste-nao-usar-em-producao"

import pytest 

from app.security import HashBcrypt
from sqlalchemy.orm import Session 

from app.database import Base, SessionLocal, criar_tabelas, engine
from app.dependencies import obter_hasher 
from app.main import app
from app.security import HashBcrypt, HashDeSenha

# =============================================================================
# Dia 4 — a primeira fixture compartilhada
# =============================================================================


@pytest.fixture
def hasher() -> HashBcrypt:
    return HashBcrypt(custo=4)


@pytest.fixture
def sessao() -> Session:
    sessao = SessionLocal()
    try:
        yield sessao
    finally:
        sessao.rollback()
        sessao.close()


# =============================================================================
# Dia 5 — o banco: limpo antes, limpo depois
# =============================================================================
@pytest.fixture(autouse=True)
def banco_limpo():

    Base.metadata.drop_all(bind=engine)
    criar_tabelas()
    yield
    Base.metadata.drop_all(bind=engine)
    
# =============================================================================
# Dia 7 — HTTP: o dublê e o cliente
# =============================================================================

class HashFake(HashDeSenha):

    def gerar(self, senha: str) -> str:
        return f"fake${senha}"

    def verificar(self, senha: str, hash_armazenado: str) -> bool:
        return hash_armazenado == self.gerar(senha)


@pytest.fixture
def cliente(banco_limpo) -> TestClient:
    app.dependency_overrides[obter_hasher] = HashFake
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def sessao_aberta(cliente: TestClient) -> dict:
    resposta = cliente.post(
        "/usuarios",
        json={"nome": "Ana Souza", "email": "ana@exemplo.com", "senha": "senha123"},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def usuario(sessao_aberta: dict) -> dict:
    return sessao_aberta["usuario"]
