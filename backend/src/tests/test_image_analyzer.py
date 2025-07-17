import pytest
from src.main import app
import os
from io import BytesIO

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Testa o endpoint de health check."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "message": "Serviço de análise de imagens funcionando"}

def test_upload_no_image(client):
    """Testa o upload sem imagem."""
    response = client.post("/api/upload")
    assert response.status_code == 400
    assert "Nenhuma imagem enviada no campo 'images'" in response.json["error"]

def test_upload_no_file_selected(client):
    """Testa o upload sem arquivo selecionado."""
    # Simula o envio de um formulário sem arquivos no campo 'images'
    data = {"method": "chatgpt"}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "Nenhuma imagem enviada no campo 'images'." in response.json["error"]

def test_upload_invalid_file_type(client):
    """Testa o upload com tipo de arquivo inválido."""
    # Cria um arquivo de texto em memória para simular o upload
    data = {"images": (BytesIO(b"conteudo de teste"), "test.txt", "text/plain")}
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "Arquivo inválido ou não permitido" in response.json["error"]

# Testes para analyze_with_chatgpt e analyze_with_ocr seriam mais complexos
# e exigiriam mocks da API OpenAI ou imagens de teste específicas.
# Por simplicidade, focaremos nos testes de rota e integração.

def test_generate_excel_no_data(client):
    """Testa a geração de Excel sem dados."""
    response = client.post("/api/generate-excel", json={})
    assert response.status_code == 400
    assert "Dados não fornecidos" in response.json["error"]

def test_generate_excel_empty_records(client):
    """Testa a geração de Excel com registros vazios."""
    response = client.post("/api/generate-excel", json={"records": []})
    assert response.status_code == 200 # Deve gerar um Excel vazio, não um erro 400
    assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Limpeza de arquivos de teste
@pytest.fixture(autouse=True)
def cleanup_test_files():
    yield
    # Limpar arquivos temporários criados pelos testes, se houver
    # if os.path.exists("test.txt"):
    #     os.remove("test.txt")
    # Adicionar lógica para limpar arquivos de upload e resultados se necessário



