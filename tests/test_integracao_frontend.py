
from datetime import date, timedelta
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

# =============================================================================
# Dia 8 — o contrato da autenticação
# =============================================================================


def test_todos_os_endpoints_de_tarefa_exigem_token(cliente: TestClient):
    chamadas = [
        cliente.get("/tasks"),
        cliente.post("/tasks", json={"titulo": "X"}),
        cliente.patch("/tasks/1", json={"titulo": "X"}),
        cliente.delete("/tasks/1"),
        cliente.get("/usuarios/eu"),
    ]
    assert [c.status_code for c in chamadas] == [401, 401, 401, 401, 401]


def test_erro_de_autenticacao_tem_detail_em_texto(cliente: TestClient):
    resposta = cliente.get("/tasks")
    assert resposta.status_code == 401
    assert isinstance(resposta.json()["detail"], str)
    assert resposta.json()["detail"].strip()


def test_cors_libera_o_cabecalho_authorization(cliente: TestClient):
    resposta = cliente.options(
        "/tasks",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert resposta.status_code == 200
    permitidos = resposta.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in permitidos


def test_total_e_exposto_ao_navegador(cliente: TestClient):
    resposta = cliente.get("/", headers={"Origin": "http://localhost:5173"})
    expostos = resposta.headers.get("access-control-expose-headers", "")
    assert "X-Total-Count" in expostos
    
# =============================================================================
# Dia 9 — duas contas e a cobertura
# =============================================================================

def criar_tarefa(cliente: TestClient, **campos) -> dict:
    corpo = {"titulo": "Tarefa"}
    corpo.update(campos)
    resposta = cliente.post("/tasks", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_tarefa_tem_exatamente_os_campos_do_typedef(cliente_logado: TestClient):
    tarefa = criar_tarefa(cliente_logado)
    assert set(tarefa) == {
        "id",
        "usuarioId",
        "titulo",
        "status",
        "prioridade",
        "prazo",
        "criadoEm",
        "atualizadoEm",
        "concluidoEm",
    }


def test_datas_saem_em_utc_declarado(
    cliente_logado: TestClient, usuario: dict
):
    tarefa = criar_tarefa(cliente_logado)
    concluida = cliente_logado.patch(
        f"/tasks/{tarefa['id']}", json={"status": "concluida"}
    ).json()

    assert tarefa["criadoEm"].endswith("Z")
    assert tarefa["atualizadoEm"].endswith("Z")
    assert concluida["concluidoEm"].endswith("Z")
    assert usuario["criadoEm"].endswith("Z")


def test_prazo_continua_sendo_so_a_data(cliente_logado: TestClient):
    tarefa = criar_tarefa(cliente_logado, prazo="2026-03-15")
    assert tarefa["prazo"] == "2026-03-15"


def test_ordenar_por_recente_e_aceito(cliente_logado: TestClient):
    criar_tarefa(cliente_logado, titulo="Primeira")
    criar_tarefa(cliente_logado, titulo="Segunda")

    resposta = cliente_logado.get("/tasks", params={"ordenarPor": "recente"})
    assert resposta.status_code == 200
    assert [t["titulo"] for t in resposta.json()] == ["Segunda", "Primeira"]


def test_sentinela_todas_vale_como_sem_filtro(cliente_logado: TestClient):
    criar_tarefa(cliente_logado, titulo="Pendente")
    concluida = criar_tarefa(cliente_logado, titulo="Concluida")
    cliente_logado.patch(
        f"/tasks/{concluida['id']}", json={"status": "concluida"}
    )

    resposta = cliente_logado.get(
        "/tasks", params={"status": "todas", "prioridade": "todas"}
    )
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_filtro_enviado_vazio_vale_como_sem_filtro(cliente_logado: TestClient):
    criar_tarefa(cliente_logado)
    resposta = cliente_logado.get("/tasks?status=&prioridade=")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_valor_de_filtro_invalido_continua_sendo_recusado(
    cliente_logado: TestClient,
):
    resposta = cliente_logado.get("/tasks", params={"status": "inventado"})
    assert resposta.status_code == 422


def test_ordem_natural_de_prazo_e_crescente(cliente_logado: TestClient):
    hoje = date.today()
    criar_tarefa(
        cliente_logado,
        titulo="Distante",
        prazo=str(hoje + timedelta(days=30)),
    )
    criar_tarefa(
        cliente_logado,
        titulo="Proxima",
        prazo=str(hoje + timedelta(days=1)),
    )

    resposta = cliente_logado.get("/tasks", params={"ordenarPor": "prazo"})
    assert [t["titulo"] for t in resposta.json()] == ["Proxima", "Distante"]


def test_tarefa_sem_prazo_vai_para_o_fim_nos_dois_sentidos(
    cliente_logado: TestClient,
):
    hoje = date.today()
    criar_tarefa(cliente_logado, titulo="Com prazo", prazo=str(hoje))
    criar_tarefa(cliente_logado, titulo="Sem prazo", prazo=None)

    for sentido in ("asc", "desc"):
        resposta = cliente_logado.get(
            "/tasks", params={"ordenarPor": "prazo", "ordem": sentido}
        )
        titulos = [t["titulo"] for t in resposta.json()]
        assert titulos[-1] == "Sem prazo", f"ordem={sentido} devolveu {titulos}"


def test_ordem_natural_de_prioridade_comeca_na_urgente(
    cliente_logado: TestClient,
):
    for prioridade in ("baixa", "urgente", "media"):
        criar_tarefa(
            cliente_logado, titulo=prioridade, prioridade=prioridade
        )

    resposta = cliente_logado.get(
        "/tasks", params={"ordenarPor": "prioridade"}
    )
    assert [t["prioridade"] for t in resposta.json()] == [
        "urgente",
        "media",
        "baixa",
    ]


def test_ordem_natural_de_criado_em_comeca_na_mais_recente(
    cliente_logado: TestClient,
):
    criar_tarefa(cliente_logado, titulo="Antiga")
    criar_tarefa(cliente_logado, titulo="Nova")

    resposta = cliente_logado.get("/tasks")
    assert [t["titulo"] for t in resposta.json()] == ["Nova", "Antiga"]


def test_busca_filtra_pelo_titulo_ignorando_maiusculas(
    cliente_logado: TestClient,
):
    criar_tarefa(cliente_logado, titulo="Revisar proposta do cliente")
    criar_tarefa(cliente_logado, titulo="Organizar planilha")

    resposta = cliente_logado.get("/tasks", params={"busca": "PROPOSTA"})
    assert [t["titulo"] for t in resposta.json()] == [
        "Revisar proposta do cliente"
    ]


def test_busca_trata_curingas_do_sql_como_texto(
    cliente_logado: TestClient,
):
    criar_tarefa(cliente_logado, titulo="Pagar 100% da fatura")
    criar_tarefa(cliente_logado, titulo="Revisar proposta")

    resposta = cliente_logado.get("/tasks", params={"busca": "100%"})
    assert [t["titulo"] for t in resposta.json()] == [
        "Pagar 100% da fatura"
    ]

    resposta = cliente_logado.get("/tasks", params={"busca": "%"})
    assert [t["titulo"] for t in resposta.json()] == [
        "Pagar 100% da fatura"
    ]


def test_busca_vazia_nao_filtra(cliente_logado: TestClient):
    criar_tarefa(cliente_logado)
    resposta = cliente_logado.get("/tasks", params={"busca": "   "})
    assert len(resposta.json()) == 1


def test_total_vem_no_cabecalho_e_ignora_o_limite(
    cliente_logado: TestClient,
):
    for n in range(3):
        criar_tarefa(cliente_logado, titulo=f"Tarefa {n}")

    resposta = cliente_logado.get("/tasks", params={"limit": 2})
    assert len(resposta.json()) == 2
    assert resposta.headers["X-Total-Count"] == "3"


def test_total_respeita_os_filtros(cliente_logado: TestClient):
    criar_tarefa(cliente_logado, titulo="Urgente", prioridade="urgente")
    criar_tarefa(cliente_logado, titulo="Baixa", prioridade="baixa")

    resposta = cliente_logado.get(
        "/tasks", params={"prioridade": "urgente"}
    )
    assert resposta.headers["X-Total-Count"] == "1"


def test_valor_de_enum_invalido_lista_os_aceitos(
    cliente_logado: TestClient,
):
    resposta = cliente_logado.post(
        "/tasks", json={"titulo": "X", "prioridade": "altissima"}
    )
    assert resposta.json()["detail"] == (
        "prioridade: valor inválido. Aceitos: baixa, media, alta ou urgente."
    )


def test_data_malformada_informa_o_formato(cliente_logado: TestClient):
    resposta = cliente_logado.post(
        "/tasks", json={"titulo": "X", "prazo": "15/03/2026"}
    )
    assert resposta.json()["detail"] == (
        "prazo: deve ser uma data no formato AAAA-MM-DD."
    )


def test_mensagem_usa_o_nome_publico_do_campo(cliente_logado: TestClient):
    resposta = cliente_logado.get("/tasks?prazoAte=15/03/2026")
    detalhe = resposta.json()["detail"]
    assert detalhe.startswith("prazoAte:"), detalhe
    assert "prazo_ate" not in detalhe


def test_fluxo_completo_que_o_front_vai_executar(cliente: TestClient):
    sessao = cliente.post(
        "/usuarios",
        json={
            "nome": "Davi",
            "email": "davi@exemplo.com",
            "senha": "senha123",
        },
    ).json()
    autorizacao = {"Authorization": f"Bearer {sessao['accessToken']}"}

    criada = cliente.post(
        "/tasks",
        json={"titulo": "Primeira tarefa"},
        headers=autorizacao,
    )
    assert criada.status_code == 201

    conta = cliente.get("/usuarios/eu", headers=autorizacao)
    assert conta.status_code == 200
    assert conta.json() == sessao["usuario"]

    minhas = cliente.get("/tasks", headers=autorizacao)
    assert [t["titulo"] for t in minhas.json()] == ["Primeira tarefa"]