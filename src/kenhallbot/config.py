from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DOTENV_PATH = Path(".env")


def _load_dotenv(path: Path = DOTENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _format_env_assignment(key: str, value: str) -> str:
    if not value:
        return f"{key}="
    if any(char.isspace() for char in value) or any(char in value for char in {'"', "'", "#"}):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'{key}="{escaped}"'
    return f"{key}={value}"


def save_settings_values(values: dict[str, str], path: Path = DOTENV_PATH) -> None:
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    pending = {key: str(value) for key, value in values.items()}
    rendered_lines: list[str] = []

    for raw_line in existing_lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            rendered_lines.append(raw_line)
            continue

        key, _ = raw_line.split("=", 1)
        key = key.strip()
        if key in pending:
            rendered_lines.append(_format_env_assignment(key, pending.pop(key)))
        else:
            rendered_lines.append(raw_line)

    if pending:
        if rendered_lines and rendered_lines[-1].strip():
            rendered_lines.append("")
        for key in sorted(pending):
            rendered_lines.append(_format_env_assignment(key, pending[key]))

    text = "\n".join(rendered_lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")

    for key, value in values.items():
        os.environ[str(key)] = str(value)


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    openai_api_key: str
    openai_model: str
    openrouter_api_key: str
    openrouter_model: str
    article_openrouter_model: str
    final_details_openrouter_model: str
    openrouter_base_url: str
    openrouter_site_url: str
    openrouter_app_name: str
    fmp_api_key: str
    fmp_base_url: str
    output_dir: Path
    style_notes_file: Path
    motley_rules_file: Path


def load_settings() -> Settings:
    _load_dotenv()
    output_dir = Path(os.getenv("OUTPUT_DIR", "output"))
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai").strip().lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
        article_openrouter_model=os.getenv("ARTICLE_OPENROUTER_MODEL", "anthropic/claude-sonnet-4.6"),
        final_details_openrouter_model=os.getenv(
            "FINAL_DETAILS_OPENROUTER_MODEL",
            os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
        ),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", ""),
        openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "KenHallBot"),
        fmp_api_key=os.getenv("FMP_API_KEY", ""),
        fmp_base_url=os.getenv("FMP_BASE_URL", "https://financialmodelingprep.com/stable"),
        output_dir=output_dir,
        style_notes_file=Path(os.getenv("STYLE_NOTES_FILE", "config/style_notes.md")),
        motley_rules_file=Path(os.getenv("MOTLEY_RULES_FILE", "config/motley_rules_uk.md")),
    )
