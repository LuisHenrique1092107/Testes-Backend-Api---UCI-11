import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "segredo-de-teste-nao-usar-em-producao"

import pytest  # noqa:E042

from app.security import HashBcrypt  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database import Base, SessionLocal, criar_tabelas, engine  # noqa: E402
from app.security import HashBcrypt  # noqa: E402

# =============================================================================
# Dia 4 — a primeira fixture compartilhada
# =============================================================================


@pytest.fixture
def hasher() -> HashBcrypt:
    return HashBcrypt(custo=4)


# =============================================================================
# Dia 5 — o banco: limpo antes, limpo depois
# =============================================================================
@pytest.fixture(autouse=True)
def banco_limpo():

    Base.metadata.drop_all(bind=engine)
    criar_tabelas()
    yield
    Base.metadata.drop_all(bind=engine)
