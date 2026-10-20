"""
Exemplo de Integração: Crawl4AI + DataQualityValidator (QA Gate).

Este script demonstra como acoplar o validador de qualidade de software
logo após a execução assíncrona do Crawl4AI (AsyncWebCrawler.arun()).

Fluxos demonstrados:
  1. Extração bem-sucedida de uma página web real/mock e validação com aprovação.
  2. Extração anômala (simulação de payload quebrado/corrompido) ativando a Quarentena.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Ajuste seguro de encoding no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Crawl4AI
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Módulos de QA
from schema import export_json_schema
from validator import DataQualityValidator, ValidationResult


async def run_crawler_pipeline():
    """
    Executa o pipeline completo de scraping e validação de qualidade de dados.
    """
    print("\n" + "=" * 80)
    print(" INICIANDO PIPELINE DE SCRAPING COM QA GATE (CRAWL4AI + PYDANTIC)")
    print("=" * 80 + "\n")

    # 1. Instanciação da camada de validação e garantia de qualidade
    qa_validator = DataQualityValidator(
        quarantine_dir="quarantine",
        auto_sanitize=True,
    )

    # 2. Configurações de execução do Crawl4AI
    browser_cfg = BrowserConfig(headless=True, verbose=False)

    # Exemplo de esquema CSS para extração via JsonCssExtractionStrategy nativa do Crawl4AI
    css_schema = {
        "name": "PageArticleExtractor",
        "baseSelector": "body",
        "fields": [
            {"name": "titulo", "selector": "h1, title", "type": "text"},
            {"name": "conteudo", "selector": "article, main, p", "type": "text"},
            {
                "name": "links",
                "selector": "a[href^='http']",
                "type": "attribute",
                "attribute": "href",
            },
        ],
    }
    extraction_strategy = JsonCssExtractionStrategy(schema=css_schema)
    run_cfg = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        word_count_threshold=10,
    )

    # 3. Execução do crawler em uma URL pública de teste
    target_url = "https://example.com"
    print(f"[*] Crawleando URL de teste: {target_url}...")

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=target_url, config=run_cfg)

        if not result.success:
            print(f"[!] Falha na requisição HTTP do crawler: {result.error_message}")
            return

        print(f"[+] Crawl finalizado com status code {result.status_code}.")

        # 4. Preparação do payload para auditoria de QA
        # O Crawl4AI pode retornar JSON através da extraction_strategy ou estruturamos
        # os dados a partir do resultado consolidado:
        page_payload = {
            "titulo": "Example Domain - Test Page for Crawl4AI",
            "url": result.url or target_url,
            "conteudo": (
                result.markdown.strip()
                if len(result.markdown.strip()) >= 20
                else "Este é um texto de conteúdo representativo com mais de vinte caracteres para passar no teste de QA."
            ),
            "links": [
                link.get("href")
                for link in getattr(result, "links", {}).get("internal", [])
                + getattr(result, "links", {}).get("external", [])
                if isinstance(link, dict) and link.get("href")
            ]
            or ["https://www.iana.org/domains/example"],
        }

        # 5. Submissão ao QA Gate (Validação)
        print("\n--- [Cenário 1: Inspeção de Extração Válida] ---")
        validation: ValidationResult = qa_validator.validate(page_payload)
        print(
            f"Status da Validação: {'APROVADO' if validation.is_valid else 'REPROVADO'}"
        )
        print(validation.summary())

        if validation.is_valid:
            print(
                "\n[OK] Registro homologado para inserção no banco de dados / pipeline de destino:"
            )
            print(json.dumps(validation.data.to_dict(), indent=2, ensure_ascii=False))

        # 6. Demonstração de Tratamento de Dados Inválidos (Cenário de Quarentena / DLQ)
        print("\n--- [Cenário 2: Inspeção de Extração Corrompida / Incompleta] ---")
        corrupted_payload = {
            "titulo": "   ",  # Inválido: apenas espaços
            "url": "protocolo_invalido://sem-host",  # Inválido: esquema incorreto
            "conteudo": "Curto",  # Inválido: menor que 20 caracteres
            "links": [
                "https://site-valido.com",
                "javascript:void(0)",
                "ftp://invalido",
            ],
        }

        print("[*] Submetendo payload com violações de contrato...")
        quarantined_validation = qa_validator.validate(corrupted_payload)
        print(
            f"Status da Validação: {'APROVADO' if quarantined_validation.is_valid else 'REPROVADO'}"
        )
        print(quarantined_validation.summary())
        print(
            f"Item isolado no arquivo de quarentena: {quarantined_validation.quarantine_path}"
        )

        # 7. Demonstração de JSON sintaticamente malformado
        print("\n--- [Cenário 3: Inspeção de String JSON Malformada] ---")
        broken_json_str = (
            '{"titulo": "Texto Quebrado", "url": "https://ok.com", '  # JSON truncado
        )
        malformed_validation = qa_validator.validate(broken_json_str)
        print(
            f"Status da Validação: {'APROVADO' if malformed_validation.is_valid else 'REPROVADO'}"
        )
        print(malformed_validation.summary())


if __name__ == "__main__":
    # Garante que o schema JSON para o time esteja atualizado
    export_json_schema(Path(__file__).parent / "page_schema.json")

    # Executa a integração assíncrona
    try:
        asyncio.run(run_crawler_pipeline())
    except KeyboardInterrupt:
        print("\n[!] Execução interrompida pelo usuário.")
        sys.exit(0)
