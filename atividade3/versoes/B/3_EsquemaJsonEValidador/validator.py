"""
Módulo de Validação e Garantia de Qualidade de Dados (QA Gate / Data Validator).

Atua após a execução de spiders e web crawlers (ex: Crawl4AI), inspecionando
payloads brutos (strings JSON ou dicionários), aplicando sanitização básica,
enforcing do contrato de esquema Pydantic e despachando dados anômalos para Quarentena (DLQ).
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
from urllib.parse import urlparse

from pydantic import ValidationError
from schema import PageExtractionSchema


@dataclass
class ValidationResult:
    """Objeto de resultado contendo o status de auditoria do QA Gate."""

    is_valid: bool
    data: Optional[PageExtractionSchema] = None
    errors: List[str] = field(default_factory=list)
    failed_fields: List[str] = field(default_factory=list)
    quarantined: bool = False
    quarantine_path: Optional[str] = None
    sanitized_links_discarded: int = 0
    raw_payload: Any = None

    def summary(self) -> str:
        """Gera um resumo textual legível do resultado de validação."""
        if self.is_valid:
            links_count = len(self.data.links) if self.data else 0
            return (
                f"[QA APROVADO] URL: {self.data.url} | Título: '{self.data.titulo}' "
                f"| Links válidos: {links_count} | Links descartados na sanitização: {self.sanitized_links_discarded}"
            )
        return (
            f"[QA REJEITADO] Erros: {len(self.errors)} | Campos com falha: {self.failed_fields} "
            f"| Quarentena: {self.quarantine_path or 'Não salvo'}"
        )


class DataQualityValidator:
    """
    Camada de Qualidade de Software (QA Gate) para dados extraídos de web scraping.

    Responsabilidades:
        1. Validação estrutural de strings JSON ou dicionários Python.
        2. Sanitização automática (remoção de espaços nas bordas e descarte seletivo de URLs corrompidas).
        3. Enforce estrito do esquema Pydantic v2.
        4. Auditoria via logs detalhados e estruturados.
        5. Isolamento de registros reprovados em fila de quarentena (Dead Letter Queue local).
    """

    def __init__(
        self,
        quarantine_dir: Union[str, Path] = "quarantine",
        auto_sanitize: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Inicializa o validador de qualidade.

        Args:
            quarantine_dir: Diretório para armazenamento dos itens rejeitados.
            auto_sanitize: Se True, aplica remoção de espaços e filtra links quebrados preservando os válidos.
            logger: Logger customizado. Se None, cria um logger configurado para QA.
        """
        self.quarantine_dir = Path(quarantine_dir)
        self.auto_sanitize = auto_sanitize
        self.logger = logger or self._setup_default_logger()

    @staticmethod
    def _setup_default_logger() -> logging.Logger:
        """Configura um logger estruturado padrão para auditoria de QA."""
        logger = logging.getLogger("QA.DataValidator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [QA-GATE] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def validate(self, raw_data: Union[str, dict, Any]) -> ValidationResult:
        """
        Ponto de entrada principal para validação de dados extraídos.

        Args:
            raw_data: String JSON bruta ou dicionário Python extraído pelo crawler.

        Returns:
            ValidationResult: Objeto com status de aprovação, dados higienizados ou histórico de falha.
        """
        self.logger.info("Iniciando inspeção de qualidade de novo registro...")

        # 1. Parsing estrutural do JSON
        parsed_dict, json_error = self._parse_to_dict(raw_data)
        if json_error:
            self.logger.error(
                "Falha estrutural: JSON malformado ou inválido. Detalhe: %s", json_error
            )
            quarantine_file = self._dispatch_to_quarantine(
                raw_payload=raw_data,
                error_type="JSONDecodeError",
                errors=[json_error],
                failed_fields=["__root__"],
            )
            return ValidationResult(
                is_valid=False,
                errors=[json_error],
                failed_fields=["__root__"],
                quarantined=True,
                quarantine_path=str(quarantine_file),
                raw_payload=raw_data,
            )

        # 2. Saneamento prévio automático (se habilitado)
        sanitized_data = parsed_dict
        discarded_links_count = 0
        if self.auto_sanitize and isinstance(parsed_dict, dict):
            sanitized_data, discarded_links_count = self._sanitize_payload(parsed_dict)

        # 3. Validação de Contrato com o Pydantic Schema
        try:
            validated_model = PageExtractionSchema.model_validate(sanitized_data)
            self.logger.info(
                "Registro aprovado no QA Gate com sucesso! URL: %s | Título: '%s'",
                validated_model.url,
                validated_model.titulo,
            )
            return ValidationResult(
                is_valid=True,
                data=validated_model,
                sanitized_links_discarded=discarded_links_count,
                raw_payload=raw_data,
            )

        except ValidationError as val_err:
            errors_list: List[str] = []
            failed_fields_set = set()

            for err in val_err.errors():
                field_name = (
                    " -> ".join(str(loc) for loc in err.get("loc", [])) or "__root__"
                )
                failed_fields_set.add(field_name)
                msg = err.get("msg", "Erro de validação desconhecido")
                errors_list.append(f"Campo '{field_name}': {msg}")

            failed_fields = sorted(list(failed_fields_set))
            self.logger.error(
                "Registro REJEITADO no QA Gate. Total de erros: %d | Campos afetados: %s",
                len(errors_list),
                failed_fields,
            )
            for err_msg in errors_list:
                self.logger.error("  └─ %s", err_msg)

            quarantine_file = self._dispatch_to_quarantine(
                raw_payload=raw_data,
                error_type="ValidationError",
                errors=errors_list,
                failed_fields=failed_fields,
            )

            return ValidationResult(
                is_valid=False,
                errors=errors_list,
                failed_fields=failed_fields,
                quarantined=True,
                quarantine_path=str(quarantine_file),
                sanitized_links_discarded=discarded_links_count,
                raw_payload=raw_data,
            )

        except Exception as exc:
            unexpected_err = f"Erro inesperado durante a validação: {str(exc)}"
            self.logger.critical(unexpected_err, exc_info=True)
            quarantine_file = self._dispatch_to_quarantine(
                raw_payload=raw_data,
                error_type=type(exc).__name__,
                errors=[unexpected_err],
                failed_fields=["__system__"],
            )
            return ValidationResult(
                is_valid=False,
                errors=[unexpected_err],
                failed_fields=["__system__"],
                quarantined=True,
                quarantine_path=str(quarantine_file),
                raw_payload=raw_data,
            )

    def _parse_to_dict(self, raw_data: Any) -> Tuple[Optional[dict], Optional[str]]:
        """Interpreta strings JSON ou valida se já é um dicionário Python."""
        if isinstance(raw_data, dict):
            return dict(raw_data), None

        if isinstance(raw_data, str):
            trimmed = raw_data.strip()
            if not trimmed:
                return None, "Entrada vazia ou contendo apenas caracteres em branco."
            try:
                parsed = json.loads(trimmed)
                if not isinstance(parsed, dict):
                    return (
                        None,
                        f"O JSON decodificado deve ser um objeto/dicionário, recebido: {type(parsed).__name__}.",
                    )
                return parsed, None
            except json.JSONDecodeError as exc:
                return (
                    None,
                    f"Erro de sintaxe JSON: {exc.msg} na linha {exc.lineno}, coluna {exc.colno}.",
                )

        return (
            None,
            f"Tipo de entrada não suportado: {type(raw_data).__name__}. Esperado str (JSON) ou dict.",
        )

    def _sanitize_payload(self, data: dict) -> Tuple[dict, int]:
        """
        Aplica regras de saneamento tolerante:
          - Remove espaços em branco nas pontas de strings primitivas.
          - Limpa listas de links, descartando URLs sabidamente inválidas e preservando as válidas.
        """
        sanitized = dict(data)
        discarded_links_count = 0

        # Sanitiza campos de texto primários se presentes
        for key in ("titulo", "conteudo", "url"):
            val = sanitized.get(key)
            if isinstance(val, str):
                sanitized[key] = val.strip()

        # Saneamento seletivo de links
        raw_links = sanitized.get("links")
        if isinstance(raw_links, list):
            valid_links: List[str] = []
            for item in raw_links:
                if isinstance(item, str):
                    candidate = item.strip()
                    parsed = urlparse(candidate)
                    if parsed.scheme in ("http", "https") and parsed.netloc:
                        valid_links.append(candidate)
                    else:
                        discarded_links_count += 1
                        self.logger.warning(
                            "Link malformado descartado no saneamento: '%s'", candidate
                        )
                else:
                    discarded_links_count += 1
                    self.logger.warning(
                        "Item não-string na lista de links descartado: %r", item
                    )
            sanitized["links"] = valid_links

        if discarded_links_count > 0:
            self.logger.info(
                "Saneamento de links concluído: %d links descartados, %d válidos mantidos.",
                discarded_links_count,
                len(sanitized.get("links", [])),
            )

        return sanitized, discarded_links_count

    def _dispatch_to_quarantine(
        self,
        raw_payload: Any,
        error_type: str,
        errors: List[str],
        failed_fields: List[str],
    ) -> Path:
        """
        Despacha o registro rejeitado para a fila de quarentena (Dead Letter Queue local).
        """
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        unique_token = uuid.uuid4().hex[:8]
        filename = f"quarantine_{timestamp_str}_{unique_token}.json"
        target_path = self.quarantine_dir / filename

        quarantine_record = {
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type,
            "failed_fields": failed_fields,
            "error_messages": errors,
            "raw_payload": raw_payload,
        }

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(quarantine_record, f, indent=2, ensure_ascii=False)
            self.logger.warning("Item rejeitado isolado em quarentena: %s", target_path)
        except Exception as exc:
            self.logger.critical("Falha ao gravar item na pasta de quarentena: %s", exc)

        return target_path
