import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "segredo-de-teste-nao-usar-em-producao"

import pytest  # noqa:E042

from app.security import HashBcrypt  # noqa: E402


# =============================================================================
# Dia 4 — a primeira fixture compartilhada
# =============================================================================

@pytest.fixture
def hasher() -> HashBcrypt:
    return HashBcrypt(custo=4)
