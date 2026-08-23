"""Helpers compartilhados: HTTP, slug, datas e serializacao YAML."""

from __future__ import annotations

import json
import os
import re
import ssl
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

USER_AGENT = "youtube-raw/0.1 (+obsidian karpathy pipeline)"

# Caracteres proibidos em nomes de arquivo no Windows/macOS mais os que o
# Obsidian usa na sintaxe de links.
_UNSAFE_FILENAME = re.compile(r'[\\/:*?"<>|#^\[\]]')
_WS = re.compile(r"\s+")


class FetchError(RuntimeError):
    """Falha recuperavel de rede: o pipeline segue sem esse dado."""


def _ssl_context() -> ssl.SSLContext:
    """Contexto TLS que respeita o CA bundle do proxy, quando configurado."""
    bundle = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if bundle and os.path.exists(bundle):
        return ssl.create_default_context(cafile=bundle)
    return ssl.create_default_context()


def http_get(url: str, timeout: float = 20.0) -> bytes:
    """GET simples. Honra http_proxy/https_proxy do ambiente via urllib."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} em {url}") from exc
    except Exception as exc:  # socket, DNS, TLS, proxy
        raise FetchError(f"{type(exc).__name__}: {exc} em {url}") from exc


def http_get_json(url: str, timeout: float = 20.0) -> Any:
    raw = http_get(url, timeout=timeout)
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise FetchError(f"resposta nao-JSON em {url}") from exc


def slugify(text: str, max_len: int = 70) -> str:
    """Nome de arquivo legivel e seguro para o Obsidian, preservando acentos."""
    cleaned = _UNSAFE_FILENAME.sub(" ", text or "")
    cleaned = "".join(
        char for char in cleaned if unicodedata.category(char)[0] != "C"
    )
    cleaned = _WS.sub(" ", cleaned).strip(" .-_")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip(" .-_")
    return cleaned or "sem-titulo"


def fmt_duration(seconds: Optional[float]) -> Optional[str]:
    """3725 -> '01:02:05'."""
    if seconds is None:
        return None
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def fmt_timestamp(seconds: float) -> str:
    """Marcador curto para transcricao: 90 -> '01:30', 3725 -> '1:02:05'."""
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


_ISO_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


def parse_iso8601_duration(value: str) -> Optional[int]:
    """'PT1H2M5S' -> 3725. Formato que a YouTube Data API devolve."""
    if not value:
        return None
    match = _ISO_DURATION.match(value.strip())
    if not match:
        return None
    parts = {key: int(val) for key, val in match.groupdict(default="0").items()}
    total = (
        parts["days"] * 86400
        + parts["hours"] * 3600
        + parts["minutes"] * 60
        + parts["seconds"]
    )
    return total or None


def parse_datetime(value: str) -> Optional[datetime]:
    """Aceita os formatos ISO que aparecem no Takeout e na Data API."""
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    # O Takeout usa microssegundos de tamanho variavel; fromisoformat exige 3 ou 6.
    text = re.sub(
        r"\.(\d+)(?=[+-]\d{2}:\d{2}$|$)",
        lambda m: "." + m.group(1)[:6].ljust(6, "0"),
        text,
    )
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def yaml_scalar(value: Any) -> str:
    """Serializa um escalar para YAML sempre citando strings (evita surpresas)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def yaml_list(values: Any) -> str:
    items = [yaml_scalar(item) for item in values if item not in (None, "")]
    return "[" + ", ".join(items) + "]"


_TAG_UNSAFE = re.compile(r"[^a-z0-9]+")


def tag_slug(text: str) -> str:
    """'Andrej Karpathy' -> 'andrej-karpathy' (tag valida no Obsidian)."""
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return _TAG_UNSAFE.sub("-", ascii_only).strip("-")
