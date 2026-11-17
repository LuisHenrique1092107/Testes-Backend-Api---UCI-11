from typing import Literal

from app.exceptions import TituloObrigatorio, ValorInvalido
from datetime import date, datetime, timedelta

import pytest

from app.enums import PrioridadeTarefa, StatusTarefa
from app.exceptions import ValorInvalido
from app.models import Tarefa, Usuario


def nova_tarefa(**ajustes) -> Tarefa:

    dados = {"usuario_id": 1, "titulo": "Estudar orientação a objetos"}
    dados.update(ajustes)
    return Tarefa(**dados)


def novo_usuario(**ajustes) -> Usuario:
    """Cria um usuário válido, permitindo sobrescrever campos pontualmente."""
    dados = {"nome": "Ana Souza", "email": "ana@exemplo.com"}
    dados.update(ajustes)
    return Usuario(**dados)


def test_tarefa_nasce_pendente_e_sem_data_de_conclusao():
    """RN-02: toda tarefa nasce pendente."""
    tarefa = nova_tarefa()
    assert tarefa.status is StatusTarefa.PENDENTE
    assert tarefa.concluido_em is None


def test_titulo_e_gravado_sem_espacos_nas_pontas():
    assert nova_tarefa(titulo=" Revisar ").titulo == "Revisar"  # type: ignore


def test_prioridade_aceita_enum_e_texto():
    assert nova_tarefa(prioridade=PrioridadeTarefa.ALTA).prioridade == "alta"  # type: ignore
    assert nova_tarefa(prioridade="urgente").prioridade == "urgente"  # type: ignore


def test_tarefa_sem_prazo_nunca_esta_atrasada():
    assert nova_tarefa(prazo=None).esta_atrasada() is False


def test_tarefa_com_prazo_vencido_e_pendente_esta_atrasada():
    ontem = date.today() - timedelta(days=1)
    assert nova_tarefa(prazo=ontem).esta_atrasada() is True


def test_pertence_a():
    tarefa = nova_tarefa(usuario_id=7)
    assert tarefa.pertence_a(7) is True
    assert tarefa.pertence_a(8) is False


def test_ordem_das_prioridades_vai_da_mais_urgente_para_a_menos():
    prioridades = (
        PrioridadeTarefa.URGENTE,
        PrioridadeTarefa.ALTA,
        PrioridadeTarefa.MEDIA,
        PrioridadeTarefa.BAIXA,
    )
    pesos = [p.peso for p in prioridades]
    assert pesos == sorted(pesos)


def test_email_e_normalizado_na_criacao():
    """RN-01: o e-mail é guardado sempre na mesma forma."""
    assert novo_usuario(email=" ANA@Exemplo.COM ").email == "ana@exemplo.com"  # type: ignore


def test_nome_e_gravado_sem_espacos_nas_pontas():
    assert novo_usuario(nome=" Ana Souza ").nome == "Ana Souza"  # type: ignore


# =============================================================================
# Dia 2 — `pytest.raises`: o que o objeto recusa
# =============================================================================


def test_status_e_somente_leitura():
    """A única porta para mudar o status são `concluir` e `reabrir`."""
    tarefa = nova_tarefa()
    with pytest.raises(AttributeError):
        tarefa.status = StatusTarefa.CONCLUIDA


def test_construtor_nao_aceita_status_como_parametro():
    """RN-02: não existe forma de criar uma tarefa já concluída."""
    with pytest.raises(TypeError):
        Tarefa(usuario_id=1, titulo="X", status=StatusTarefa.CONCLUIDA)  # type: ignore


def test_construtor_exige_argumentos_nomeados():
    with pytest.raises(TypeError):
        Usuario("Ana Souza", "ana@exemplo.com")  # type: ignore


def test_construtor_nao_aceita_senha():
    with pytest.raises(TypeError):
        Usuario(nome="Ana", email="ana@exemplo.com", senha="senha123")  # type: ignore


def test_prioridade_invalida_e_recusada():
    with pytest.raises(ValorInvalido):
        nova_tarefa(prioridade="altissima")


def test_nome_invalido_e_recusado_tambem_depois_da_criacao():
    usuario = novo_usuario()
    with pytest.raises(ValorInvalido):
        usuario.nome = "  "


# ----------------------------- RN-03: o ciclo de vida da data de conclusão ---------------------------


def test_concluir_registra_a_data():
    tarefa = nova_tarefa()
    tarefa.concluir()
    assert tarefa.status is StatusTarefa.CONCLUIDA
    assert tarefa.concluido_em is not None


def test_reabrir_apaga_a_data():
    tarefa = nova_tarefa()
    tarefa.concluir()
    tarefa.reabrir()
    assert tarefa.status is StatusTarefa.PENDENTE
    assert tarefa.concluido_em is None


def test_editar_outro_campo_nao_mexe_na_data_de_conclusao():
    tarefa = nova_tarefa()
    tarefa.concluir(agora=datetime(2026, 1, 10, 9, 0, 0))
    antes = tarefa.concluido_em
    tarefa.titulo = "Título novo"
    assert tarefa.concluido_em == antes


def test_definir_status_encaminha_para_a_operação_correta():
    tarefa = nova_tarefa()
    tarefa.definir_status("concluida")
    assert tarefa.concluido_em is not None
    tarefa.definir_status(StatusTarefa.PENDENTE)
    assert tarefa.concluido_em is None


def test_tarefa_concluida_nao_esta_atrasada_mesmo_com_prazo_vencido():
    tarefa = nova_tarefa(prazo=date.today() - timedelta(days=5))
    tarefa.concluir()
    assert tarefa.esta_atrasada() is False


def test_tarefas_pendentes_filtra_as_concluidas():
    usuario = novo_usuario()
    pendente = nova_tarefa(titulo="Pendente")
    concluida = nova_tarefa(titulo="Concluída")
    concluida.concluir()
    usuario.tarefas = [pendente, concluida]
    assert usuario.tarefas_pendentes() == [pendente]


def test_concluir_tarefa_ja_concluida_preserva_a_data_original():
    original = datetime(2026, 1, 10, 9, 0, 0)
    tarefa = nova_tarefa()
    tarefa.concluir(agora=original)
    tarefa.concluir(agora=datetime(2026, 3, 1, 15, 30, 0))
    assert tarefa.concluido_em == original


# =============================================================================
# Dia 3 — `@pytest.mark.parametrize`: a mesma regra, várias entradas
# =============================================================================


@pytest.mark.parametrize("titulo_invalido", ["", "  "])
def test_titulo_vazio_e_recusado(titulo_invalido):
    with pytest.raises(TituloObrigatorio):
        nova_tarefa(titulo=titulo_invalido)


@pytest.mark.parametrize("nome_invalido", ["", " ", "\t", "\n"])
def test_nome_vazio_e_recusado(nome_invalido):
    with pytest.raises(ValorInvalido):
        novo_usuario(nome=nome_invalido)


@pytest.mark.parametrize(
    "informado, esperado",
    [
        ("ana@exemplo.com", "ana@exemplo.com"),
        ("ANA@EXEMPLO.COM", "ana@exemplo.com"),
        (" ana@exemplo.com ", "ana@exemplo.com"),
        ("Ana@Exemplo.Com\n", "ana@exemplo.com"),
    ],
)
def test_normalizar_email_padroniza_espacos_e_maiusculas(informado, esperado):
    assert Usuario.normalizar_email(informado) == esperado


# =============================================================================
# Dia 4 — fixtures: a senha (RN-05), com o `hasher` do conftest.py
# =============================================================================

def test_a_senha_nao_fica_guardada_em_atributo_algum(hasher):
  
    usuario = novo_usuario()
    usuario.definir_senha("senha123", hasher)
    assert not hasattr(usuario, "senha")
    assert usuario._senha_hash != "senha123"


def test_senha_correta_confere(hasher):
    usuario = novo_usuario()
    usuario.definir_senha("senha123", hasher)
    assert usuario.senha_confere("senha123", hasher) is True


def test_senha_errada_nao_confere(hasher):
    usuario = novo_usuario()
    usuario.definir_senha("senha123", hasher)
    assert usuario.senha_confere("errada", hasher) is False


def test_definir_senha_de_novo_substitui_a_anterior(hasher):
    usuario = novo_usuario()
    usuario.definir_senha("antiga", hasher)
    usuario.definir_senha("nova", hasher)
    assert usuario.senha_confere("nova", hasher) is True
    assert usuario.senha_confere("antiga", hasher) is False


def test_repr_nao_expoe_o_hash_da_senha(hasher):
    """Um `print` de objeto não deve despejar credencial em log."""
    usuario = novo_usuario()
    usuario.definir_senha("senha123", hasher)
    assert "senha123" not in repr(usuario)
    assert usuario._senha_hash not in repr(usuario)
