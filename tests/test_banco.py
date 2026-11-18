import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, engine
from app.models import Tarefa, Usuario

# ------------------------------------------------------- a estrutura do banco

def test_as_duas_tabelas_existem_no_banco():
    assert set(inspect(engine).get_table_names()) == {"usuarios", "tarefas"}
def test_a_tabela_usuarios_tem_as_colunas_esperadas():
    colunas = {coluna["name"] for coluna in inspect(engine).get_columns("usuarios")}
    assert colunas == {"id", "nome", "email", "senha_hash", "criado_em"}
def test_a_coluna_do_banco_se_chama_senha_hash_e_nao_senha():
    assert Usuario.__table__.columns["senha_hash"].name == "senha_hash"
    
# ----------------------------------------------------- gravando e consultando

def test_tarefa_com_usuario_existente_e_aceita():
    sessao = SessionLocal()
    try:
        usuario = Usuario(nome="Ana", email="ana@exemplo.com")
        usuario._senha_hash = "hash-qualquer"
        sessao.add(usuario)
        sessao.commit()
        
        sessao.add(Tarefa(usuario_id=usuario.id, titulo="Tarefa válida"))
        sessao.commit()
        
        assert sessao.query(Tarefa).count() == 1
    finally:
        sessao.rollback()
        sessao.close()
        
def test_email_duplicado_e_recusado_pelo_banco(sessao, hasher):

    for _ in range(2):
        usuario = Usuario(nome="Ana", email="ana@exemplo.com")
        usuario.definir_senha("senha123", hasher)
        sessao.add(usuario)
    with pytest.raises(IntegrityError):
        sessao.commit()

# ----------------------------------------------- RN-04: a chave estrangeira
def test_verificacao_de_chave_estrangeira_esta_ligada():
    with engine.connect() as conexao:
        ligado = conexao.execute(text("PRAGMA foreign_keys")).scalar()
    assert ligado == 1, "a verificação de chave estrangeira do SQLite está desligada"

def test_tarefa_orfa_e_recusada_pelo_banco(sessao):
    sessao.add(Tarefa(usuario_id=9999, titulo="Tarefa de usuário inexistente"))
    with pytest.raises(IntegrityError):
        sessao.commit()

