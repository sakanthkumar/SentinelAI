"""Configuration and Prompt Template Loader Module for Enterprise DLP System.

Supports AWS cloud readiness by enabling environment variable overrides for config paths
and secrets parameter stores while providing robust local fallback defaults.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_yaml_or_json(file_path: Path) -> dict[str, Any]:
    """Helper loading YAML or JSON configuration files with fallback parsing."""
    if not file_path.exists():
        logger.warning("Configuration file not found at path '%s'. Using empty dict fallback.", file_path)
        return {}

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return {}

    try:
        import yaml
        return yaml.safe_load(content) or {}
    except ImportError:
        logger.debug("PyYAML not installed. Attempting standard JSON parsing for '%s'.", file_path.name)
        try:
            return json.loads(content)
        except Exception as exc:
            logger.error("Failed to parse config file '%s': %s", file_path, exc)
            return {}
    except Exception as exc:
        logger.error("Failed YAML parsing for '%s': %s", file_path, exc)
        return {}


class ConfigLoader:
    """Loads enterprise DLP policies, sensitivity levels, security options, and environment configurations."""

    def __init__(self, config_dir: str | Path | None = None) -> None:
        """Initialize ConfigLoader with configurable directory path (AWS cloud-ready)."""
        env_config_dir = os.getenv("SENTINEL_CONFIG_DIR")
        if env_config_dir:
            self.config_dir = Path(env_config_dir).resolve()
        elif config_dir:
            self.config_dir = Path(config_dir).resolve()
        else:
            self.config_dir = Path(__file__).resolve().parents[2] / "config"

        logger.info("ConfigLoader initialized pointing to directory '%s'.", self.config_dir)

    def load_dlp_policy(self) -> dict[str, Any]:
        """Load enterprise DLP policy configuration."""
        env_policy_path = os.getenv("SENTINEL_DLP_POLICY_PATH")
        file_path = Path(env_policy_path).resolve() if env_policy_path else self.config_dir / "dlp_policy.yaml"

        data = _load_yaml_or_json(file_path)

        if not data:
            data = {
                "blocked_categories": [
                    "PASSWORD", "DATABASE_CREDENTIAL", "API_KEY", "TOKEN", "SECRET",
                    "SSH_KEY", "PRIVATE_KEY", "CONNECTION_STRING", "INTERNAL_HOSTNAME",
                    "INTERNAL_IP", "CUSTOMER_PII", "EMPLOYEE_PII", "FINANCIAL_DATA",
                    "TRADE_SECRET", "PROPRIETARY_ALGORITHM", "BUSINESS_PLAN"
                ],
                "allowed_categories": ["GENERAL_INFORMATION", "SECURITY_POLICY", "OTHER"],
                "confidence_threshold": 0.80,
                "default_replacement_message": "Response blocked due to enterprise security policy.",
            }
        return data

    def load_security_levels(self) -> dict[str, Any]:
        """Load document sensitivity level mappings."""
        env_levels_path = os.getenv("SENTINEL_SECURITY_LEVELS_PATH")
        file_path = Path(env_levels_path).resolve() if env_levels_path else self.config_dir / "security_levels.yaml"

        data = _load_yaml_or_json(file_path)
        if not data:
            data = {
                "sensitivity_levels": {
                    "PUBLIC": {"strictness": "LOW", "default_policy": "ALLOW"},
                    "INTERNAL": {"strictness": "MEDIUM", "default_policy": "ALLOW"},
                    "CONFIDENTIAL": {"strictness": "HIGH", "default_policy": "EVALUATE"},
                    "RESTRICTED": {"strictness": "HIGH", "default_policy": "EVALUATE"},
                    "SECRET": {"strictness": "CRITICAL", "default_policy": "BLOCK"},
                }
            }
        return data

    def load_security_config(self) -> dict[str, Any]:
        """Load API security, security mode (PRODUCTION vs DEVELOPMENT), sensitive value redaction, and document masking options."""
        env_sec_path = os.getenv("SENTINEL_SECURITY_CONFIG_PATH")
        file_path = Path(env_sec_path).resolve() if env_sec_path else self.config_dir / "security.yaml"

        data = _load_yaml_or_json(file_path)
        if not data:
            mode = os.getenv("SENTINEL_SECURITY_MODE", "PRODUCTION").upper()
            data = {
                "security_mode": mode,
                "expose_confidential_sources": False,
                "sanitize_sources_on_block": True,
                "expose_document_names": False,
                "expose_sensitive_values": False,
            }

        # Normalize security mode & options
        mode = str(data.get("security_mode", "PRODUCTION")).upper()
        data["security_mode"] = mode

        if mode == "DEVELOPMENT":
            data["expose_confidential_sources"] = bool(data.get("expose_confidential_sources", True))
            data["expose_document_names"] = bool(data.get("expose_document_names", True))
            data["expose_sensitive_values"] = bool(data.get("expose_sensitive_values", True))
            data["sanitize_sources_on_block"] = bool(data.get("sanitize_sources_on_block", False))
        else:
            # PRODUCTION mode defaults: strictly redact secrets, mask doc names, hide confidential sources
            data["expose_confidential_sources"] = bool(data.get("expose_confidential_sources", False))
            data["expose_document_names"] = bool(data.get("expose_document_names", False))
            data["expose_sensitive_values"] = bool(data.get("expose_sensitive_values", False))
            data["sanitize_sources_on_block"] = bool(data.get("sanitize_sources_on_block", True))

        return data


class PromptTemplateLoader:
    """Loads and renders externalized prompt templates for DLP security reasoning."""

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        """Initialize PromptTemplateLoader with configurable directory path."""
        env_templates_dir = os.getenv("SENTINEL_PROMPT_TEMPLATES_DIR")
        if env_templates_dir:
            self.templates_dir = Path(env_templates_dir).resolve()
        elif templates_dir:
            self.templates_dir = Path(templates_dir).resolve()
        else:
            self.templates_dir = Path(__file__).resolve().parents[2] / "config" / "prompt_templates"

        logger.info("PromptTemplateLoader initialized pointing to '%s'.", self.templates_dir)

    def load_system_prompt_template(self) -> str:
        """Load system prompt template text."""
        file_path = self.templates_dir / "dlp_system_prompt.txt"
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return (
            "You are an Enterprise Data Loss Prevention (DLP) Security Officer.\n"
            "Evaluate whether the AI response violates enterprise security policy.\n"
            "Policy: {enterprise_policy}\nReturn ONLY valid JSON."
        )

    def load_user_prompt_template(self) -> str:
        """Load user prompt template text."""
        file_path = self.templates_dir / "dlp_user_prompt.txt"
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return (
            "Protected Reference Chunk:\n\"\"\"\n{matched_chunk}\n\"\"\"\n\n"
            "Generated Response:\n\"\"\"\n{response}\n\"\"\"\n\n"
            "Return JSON matching decision schema."
        )

    def render_system_prompt(
        self,
        classification: str,
        sensitivity: str,
        document_type: str,
        source: str,
        enterprise_policy: str,
    ) -> str:
        """Render system prompt template with injected context variables."""
        template = self.load_system_prompt_template()
        replacements = {
            "{classification}": classification,
            "{sensitivity}": sensitivity,
            "{document_type}": document_type,
            "{source}": source,
            "{enterprise_policy}": enterprise_policy,
        }
        res = template
        for k, v in replacements.items():
            res = res.replace(k, str(v))
        return res

    def render_user_prompt(
        self,
        matched_chunk: str,
        response: str,
        sensitivity: str,
        user_query: str = "General inquiry",
    ) -> str:
        """Render user prompt template with injected context variables."""
        template = self.load_user_prompt_template()
        replacements = {
            "{user_query}": user_query,
            "{matched_chunk}": matched_chunk,
            "{response}": response,
            "{sensitivity}": sensitivity,
        }
        res = template
        for k, v in replacements.items():
            res = res.replace(k, str(v))
        return res
