"""
Bateria de Testes Unitários de Qualidade de Software (QA) com Pytest.

Cobre exaustivamente:
  1. Sucesso com dados íntegros (payloads em dicionário e string JSON).
  2. Rejeição de JSON malformado (strings truncadas ou chaves não fechadas).
  3. Rejeição por ausência de campos obrigatórios.
  4. Rejeição por tipos de dados incompatíveis.
  5. Rejeição por URLs inválidas (protocolo incorreto, ausência de domínio).
  6. Saneamento automático de links com descarte de URLs quebradas.
  7. Rejeição por violação de regras de negócio (título vazio/espaços, conteúdo curto).
  8. Auditoria de logs e isolamento físico na pasta de Quarentena (DLQ).
  9. Conformidade do JSON Schema exportado.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from schema import export_json_schema
from validator import DataQualityValidator


@pytest.fixture
def temp_quarantine_dir(tmp_path: Path) -> Path:
    """Cria um diretório temporário isolado para quarentena em cada teste."""
    q_dir = tmp_path / "test_quarantine"
    q_dir.mkdir(parents=True, exist_ok=True)
    return q_dir


@pytest.fixture
def validator(temp_quarantine_dir: Path) -> DataQualityValidator:
    """Instancia um DataQualityValidator apontando para o diretório temporário."""
    return DataQualityValidator(quarantine_dir=temp_quarantine_dir, auto_sanitize=True)


@pytest.fixture
def valid_payload_dict() -> dict:
    """Payload válido completo em formato de dicionário."""
    return {
        "titulo": "Guia Avançado de Crawl4AI e Qualidade de Software",
        "url": "https://ufs.br/qualidade-software/crawl4ai-guia",
        "conteudo": "A disciplina de Qualidade de Software exige validação rigorosa de dados coletados da web.",
        "links": [
            "https://ufs.br/qualidade-software/artigo-1",
            "https://crawler.example.org/docs",
        ],
    }


# ==============================================================================
# 1. TESTES DE CASOS DE SUCESSO (HAPPY PATH)
# ==============================================================================


def test_valid_payload_dict_success(
    validator: DataQualityValidator, valid_payload_dict: dict
):
    """Verifica a aprovação de um dicionário perfeitamente formatado."""
    result = validator.validate(valid_payload_dict)

    assert result.is_valid is True
    assert result.quarantined is False
    assert len(result.errors) == 0
    assert result.data is not None
    assert result.data.titulo == valid_payload_dict["titulo"]
    assert str(result.data.url).rstrip("/") == valid_payload_dict["url"]
    assert len(result.data.links) == 2
    assert "APROVADO" in result.summary()


def test_valid_payload_json_string_success(
    validator: DataQualityValidator, valid_payload_dict: dict
):
    """Verifica a aprovação a partir de uma string JSON válida."""
    json_str = json.dumps(valid_payload_dict)
    result = validator.validate(json_str)

    assert result.is_valid is True
    assert result.data is not None
    assert result.data.titulo == valid_payload_dict["titulo"]
    assert result.quarantined is False


def test_valid_payload_strips_outer_whitespaces(validator: DataQualityValidator):
    """Verifica se espaços em branco nas extremidades são higienizados com sucesso."""
    payload = {
        "titulo": "   Título com Espaços Extras   ",
        "url": "https://ufs.br/teste-espacos",
        "conteudo": "   Conteúdo longo o suficiente para passar no teste de tamanho mínimo de 20 chars.   ",
        "links": ["https://ufs.br/link1   "],
    }
    result = validator.validate(payload)

    assert result.is_valid is True
    assert result.data.titulo == "Título com Espaços Extras"
    assert result.data.conteudo.startswith("Conteúdo longo")
    assert result.data.conteudo.endswith("chars.")


# ==============================================================================
# 2. TESTES DE JSON MALFORMADO E ENTRADAS INVÁLIDAS
# ==============================================================================


@pytest.mark.parametrize(
    "malformed_json_str",
    [
        '{"titulo": "Incompleto", "url": "https://ex.com", ',  # Truncado
        '{ titulo: "Sem aspas nas chaves" }',  # Sintaxe JSON quebrada
        '{"titulo": "Aspas não fechadas, "url": "https://a.com"}',
        "",  # String vazia
        "   ",  # String apenas com espaços
    ],
)
def test_malformed_json_rejection(
    validator: DataQualityValidator, temp_quarantine_dir: Path, malformed_json_str: str
):
    """Garante que strings JSON malformadas sejam sumariamente rejeitadas e isoladas em quarentena."""
    result = validator.validate(malformed_json_str)

    assert result.is_valid is False
    assert result.quarantined is True
    assert result.quarantine_path is not None
    assert any("JSON" in err or "vazia" in err for err in result.errors)
    assert Path(result.quarantine_path).exists()


def test_unsupported_data_type_rejection(validator: DataQualityValidator):
    """Verifica a rejeição quando o dado fornecido não é nem str nem dict."""
    result = validator.validate(12345)  # Inteiro

    assert result.is_valid is False
    assert result.quarantined is True
    assert any("Tipo de entrada não suportado" in err for err in result.errors)


# ==============================================================================
# 3. TESTES DE CAMPOS OBRIGATÓRIOS AUSENTES
# ==============================================================================


@pytest.mark.parametrize(
    "missing_field",
    ["titulo", "url", "conteudo"],
)
def test_missing_mandatory_fields_rejection(
    validator: DataQualityValidator, valid_payload_dict: dict, missing_field: str
):
    """Rejeita registros quando qualquer campo mandatório estiver ausente."""
    incomplete_payload = dict(valid_payload_dict)
    del incomplete_payload[missing_field]

    result = validator.validate(incomplete_payload)

    assert result.is_valid is False
    assert result.quarantined is True
    assert missing_field in result.failed_fields
    assert any(missing_field in err for err in result.errors)


# ==============================================================================
# 4. TESTES DE TIPAGEM E VALIDAÇÃO DE URLs
# ==============================================================================


@pytest.mark.parametrize(
    "invalid_url",
    [
        "ftp://servidor-arquivos.com/arquivo.zip",  # Protocolo FTP não permitido
        "javascript:alert(1)",  # Esquema malicioso/inválido
        "arquivo://local/path",
        "ht!tp://formato-quebrado",
        "https://",  # Sem domínio
        "apenas_texto_sem_url",
        "http://",
    ],
)
def test_invalid_origin_url_rejection(
    validator: DataQualityValidator, valid_payload_dict: dict, invalid_url: str
):
    """Rejeita páginas cuja URL de origem seja inválida ou possua protocolo não suportado."""
    bad_payload = dict(valid_payload_dict)
    bad_payload["url"] = invalid_url

    result = validator.validate(bad_payload)

    assert result.is_valid is False
    assert result.quarantined is True
    assert "url" in result.failed_fields


def test_invalid_data_types_in_fields(
    validator: DataQualityValidator, valid_payload_dict: dict
):
    """Rejeita quando campos contêm tipos errados (ex: título numérico ou booleano)."""
    bad_payload = dict(valid_payload_dict)
    bad_payload["titulo"] = 99999  # Deveria ser str

    result = validator.validate(bad_payload)

    assert result.is_valid is False
    assert "titulo" in result.failed_fields


# ==============================================================================
# 5. TESTES DE REGRAS DE NEGÓCIO DE QA (TÍTULO E CONTEÚDO)
# ==============================================================================


def test_empty_or_whitespace_title_rejection(
    validator: DataQualityValidator, valid_payload_dict: dict
):
    """Rejeita títulos vazios ou preenchidos exclusivamente com espaços em branco."""
    bad_payload = dict(valid_payload_dict)
    bad_payload["titulo"] = "    \n\t   "

    result = validator.validate(bad_payload)

    assert result.is_valid is False
    assert "titulo" in result.failed_fields
    assert any("não pode ser vazio" in err for err in result.errors)


def test_content_shorter_than_minimum_rejection(
    validator: DataQualityValidator, valid_payload_dict: dict
):
    """Rejeita conteúdos com tamanho inferior a 20 caracteres representativos."""
    bad_payload = dict(valid_payload_dict)
    bad_payload["conteudo"] = "Texto muito curto."  # 18 caracteres

    result = validator.validate(bad_payload)

    assert result.is_valid is False
    assert "conteudo" in result.failed_fields
    assert any("no mínimo 20 caracteres" in err for err in result.errors)


# ==============================================================================
# 6. TESTES DE SANEAMENTO DE LINKS (FILTRO DE URLs QUEBRADAS)
# ==============================================================================


def test_sanitization_filters_invalid_links_while_preserving_valid_ones(
    validator: DataQualityValidator, valid_payload_dict: dict
):
    """
    Testa a política de QA de saneamento:
    Remove links corrompidos (javascript, âncoras locais, sem host) e preserva as URLs válidas.
    """
    payload_with_mixed_links = dict(valid_payload_dict)
    payload_with_mixed_links["links"] = [
        "https://ufs.br/link-valido-1",
        "javascript:void(0)",  # Inválido (deve ser descartado)
        "   https://ufs.br/link-valido-2   ",
        "#ancora-local",  # Inválido (deve ser descartado)
        "invalid-link-without-scheme",  # Inválido (deve ser descartado)
        "http://crawler.org/link-valido-3",
    ]

    result = validator.validate(payload_with_mixed_links)

    assert result.is_valid is True
    assert result.sanitized_links_discarded == 3
    assert len(result.data.links) == 3

    # Verifica se os links válidos foram devidamente preservados
    preserved_links = [str(u).rstrip("/") for u in result.data.links]
    assert "https://ufs.br/link-valido-1" in preserved_links
    assert "https://ufs.br/link-valido-2" in preserved_links
    assert "http://crawler.org/link-valido-3" in preserved_links


# ==============================================================================
# 7. TESTE DE ISOLAMENTO EM QUARENTENA E AUDITORIA DE LOGS
# ==============================================================================


def test_quarantine_file_structure_and_persistence(
    validator: DataQualityValidator, temp_quarantine_dir: Path
):
    """Verifica se o arquivo na quarentena contém todos os metadados de auditoria exigidos."""
    bad_payload = {"titulo": "Sem outros campos"}
    result = validator.validate(bad_payload)

    assert result.is_valid is False
    assert result.quarantine_path is not None

    quarantine_file = Path(result.quarantine_path)
    assert quarantine_file.exists()
    assert quarantine_file.parent == temp_quarantine_dir

    # Lê o arquivo gravado e valida o formato
    with open(quarantine_file, "r", encoding="utf-8") as f:
        quarantine_data = json.load(f)

    assert "quarantined_at" in quarantine_data
    assert quarantine_data["error_type"] == "ValidationError"
    assert "url" in quarantine_data["failed_fields"]
    assert "conteudo" in quarantine_data["failed_fields"]
    assert quarantine_data["raw_payload"] == bad_payload


def test_logging_audit_records(
    validator: DataQualityValidator, caplog: pytest.LogCaptureFixture
):
    """Verifica se os logs estruturados de auditoria são gerados adequadamente."""
    import logging

    with caplog.at_level(logging.INFO):
        # 1. Caso de sucesso
        validator.validate({
            "titulo": "Log Test Page",
            "url": "https://ufs.br/logs",
            "conteudo": "Conteúdo com mais de vinte caracteres para auditoria de log.",
            "links": ["https://ufs.br/sucesso"],
        })
        assert any(
            "Registro aprovado no QA Gate" in record.message
            for record in caplog.records
        )

        # 2. Caso de rejeição
        validator.validate('{"json": "quebrado"')
        assert any("Falha estrutural" in record.message for record in caplog.records)


# ==============================================================================
# 8. TESTE DO JSON SCHEMA EXPORTADO
# ==============================================================================


def test_json_schema_generation(tmp_path: Path):
    """Verifica se a exportação do JSON Schema segue o padrão Pydantic v2."""
    output_file = tmp_path / "page_schema.json"
    schema = export_json_schema(output_file)

    assert output_file.exists()
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "required" in schema
    assert {"titulo", "url", "conteudo"}.issubset(set(schema["required"]))
    assert schema["properties"]["titulo"]["type"] == "string"
