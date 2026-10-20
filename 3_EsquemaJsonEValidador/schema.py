"""
Esquema Pydantic v2 para extração e validação de páginas web com Crawl4AI.

Este módulo define o contrato de dados (PageExtractionSchema) com validações
estritas de tipos, limites de caracteres e sanitização de strings e URLs.
Também fornece utilitários para geração e exportação do JSON Schema padrão.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)


class PageExtractionSchema(BaseModel):
    """
    Modelo Pydantic v2 para estruturação e validação de páginas web extraídas.

    Campos obrigatórios:
        titulo (str): Título da página, não vazio, sem espaços redundantes nas pontas.
        url (HttpUrl): URL absoluta e válida com esquema http ou https.
        conteudo (str): Conteúdo textual representativo (mínimo de 20 caracteres).
        links (List[HttpUrl]): Coleção de URLs válidas encontradas na página.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "description": "Esquema padronizado para extração e auditoria de páginas web",
            "example": {
                "titulo": "Exemplo de Artigo de Qualidade de Software",
                "url": "https://crawler.example.org/artigos/qualidade-software",
                "conteudo": "A garantia de qualidade de dados (Data QA) em pipelines de web scraping previne anomalias a jusante.",
                "links": [
                    "https://crawler.example.org/artigos/crawl4ai-intro",
                    "https://crawler.example.org/docs",
                ],
            },
        },
    )

    titulo: str = Field(
        ...,
        description="Título da página extraída. Deve ser uma string não vazia.",
        min_length=1,
    )
    url: HttpUrl = Field(
        ...,
        description="URL canônica ou de origem da página. Deve conter esquema http:// ou https:// válido.",
    )
    conteudo: str = Field(
        ...,
        description="Conteúdo textual principal ou corpo da página (tamanho mínimo representativo: 20 caracteres).",
        min_length=20,
    )
    links: List[HttpUrl] = Field(
        default_factory=list,
        description="Lista de hiperlinks válidos presentes na página.",
    )

    @field_validator("titulo", mode="before")
    @classmethod
    def sanitize_and_validate_title(cls, value: Any) -> str:
        """Garante que o título é uma string e não contém apenas espaços em branco."""
        if not isinstance(value, str):
            raise ValueError(
                f"O campo 'titulo' deve ser do tipo string, recebido: {type(value).__name__}"
            )

        cleaned = value.strip()
        if not cleaned:
            raise ValueError(
                "O campo 'titulo' não pode ser vazio ou conter apenas espaços em branco."
            )

        return cleaned

    @field_validator("conteudo", mode="before")
    @classmethod
    def sanitize_and_validate_content(cls, value: Any) -> str:
        """Garante que o conteúdo textual seja limpo de espaços redundantes e válido."""
        if not isinstance(value, str):
            raise ValueError(
                f"O campo 'conteudo' deve ser do tipo string, recebido: {type(value).__name__}"
            )

        cleaned = value.strip()
        if len(cleaned) < 20:
            raise ValueError(
                f"O campo 'conteudo' deve ter no mínimo 20 caracteres representativos. Tamanho atual: {len(cleaned)}"
            )
        return cleaned

    @field_validator("url", mode="before")
    @classmethod
    def validate_origin_url(cls, value: Any) -> Any:
        """Validação prévia do esquema e estrutura da URL de origem."""
        if isinstance(value, str):
            value = value.strip()
            parsed = urlparse(value)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(
                    f"A URL de origem '{value}' possui protocolo inválido. Esperado 'http' ou 'https'."
                )
            if not parsed.netloc:
                raise ValueError(
                    f"A URL de origem '{value}' não possui domínio/host válido."
                )
        return value

    def to_dict(self) -> dict:
        """Converte a instância para um dicionário serializável em JSON."""
        return json.loads(self.model_dump_json())


def export_json_schema(output_path: Optional[str | Path] = None) -> dict:
    """
    Gera o JSON Schema padrão do modelo e opcionalmente salva em arquivo.

    Args:
        output_path: Caminho opcional do arquivo .json onde o schema será salvo.

    Returns:
        dict: Representação JSON Schema gerada pelo Pydantic v2.
    """
    schema_dict = PageExtractionSchema.model_json_schema()

    if output_path is not None:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(schema_dict, f, indent=2, ensure_ascii=False)

    return schema_dict


if __name__ == "__main__":
    # Quando executado diretamente, exporta o schema para o time
    schema_file = Path(__file__).parent / "page_schema.json"
    export_json_schema(schema_file)
    print(f"JSON Schema gerado com sucesso em: {schema_file.resolve()}")
