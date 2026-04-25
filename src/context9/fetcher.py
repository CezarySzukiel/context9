from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path

import httpx
from pydantic import BaseModel

HTTP_TIMEOUT = httpx.Timeout(30.0)


class RawDocument(BaseModel):
    """Raw document content fetched from a local file or remote URL."""

    source: str
    body: str
    content_type: str | None = None


async def fetch_document(source: str, client: httpx.AsyncClient | None = None) -> RawDocument:
    """Fetch raw document content from a URL or local filesystem path."""
    if source.startswith(("http://", "https://")):
        if client is not None:
            response = await client.get(source)
            response.raise_for_status()
            return RawDocument(
                source=source,
                body=response.text,
                content_type=response.headers.get("content-type"),
            )

        async with httpx.AsyncClient(follow_redirects=True, timeout=HTTP_TIMEOUT) as short_lived_client:
            response = await short_lived_client.get(source)
            response.raise_for_status()

        return RawDocument(
            source=source,
            body=response.text,
            content_type=response.headers.get("content-type"),
        )

    path = Path(source)
    if not path.exists():
        msg = f"Local source does not exist: {source}"
        raise FileNotFoundError(msg)
    if not path.is_file():
        msg = f"Local source is not a file: {source}"
        raise IsADirectoryError(msg)

    content_type, _encoding = guess_type(path.name)
    return RawDocument(
        source=str(path),
        body=path.read_text(encoding="utf-8"),
        content_type=content_type,
    )
