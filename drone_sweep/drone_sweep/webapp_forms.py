"""Разбор POST из браузера: поля и загруженные файлы."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import HTTP
from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qs


@dataclass(frozen=True)
class Uploaded:
    filename: str
    data: bytes


def _field_name(value: object) -> str:
    if isinstance(value, tuple):
        value = value[-1]
    return "" if value is None else str(value)


def _multipart_form(content_type: str, body: bytes) -> tuple[dict[str, str], dict[str, Uploaded]]:
    """multipart/form-data без модуля cgi (его нет в Python 3.13+)."""
    header = f"Content-Type: {content_type}\r\n\r\n".encode("utf-8", "surrogateescape")
    message = BytesParser(policy=HTTP).parsebytes(header + body)
    fields: dict[str, str] = {}
    files: dict[str, Uploaded] = {}
    if not message.is_multipart():
        return fields, files
    for part in message.iter_parts():
        name = _field_name(part.get_param("name", header="content-disposition"))
        if not name:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            payload = b""
        if filename:
            if payload:
                files[name] = Uploaded(str(filename), payload)
        else:
            fields[name] = payload.decode("utf-8", errors="replace")
    return fields, files


def parse_post_body(content_type: str | None, body: bytes) -> tuple[dict[str, str], dict[str, Uploaded]]:
    if content_type and "multipart/form-data" in content_type.lower():
        return _multipart_form(content_type, body)
    text = body.decode("utf-8", errors="replace")
    fields = {key: values[0] for key, values in parse_qs(text, keep_blank_values=True).items()}
    return fields, {}


def stash_upload(upload: Uploaded | None) -> Path | None:
    if upload is None or not upload.data:
        return None
    suffix = Path(upload.filename).suffix or ".upload"
    handle, raw = tempfile.mkstemp(suffix=suffix)
    os.close(handle)
    path = Path(raw)
    path.write_bytes(upload.data)
    return path


def resolve_upload_path(
    form: Mapping[str, str],
    files: Mapping[str, Uploaded],
    file_field: str,
    path_field: str,
) -> Path | None:
    """Файл с ПК важнее; иначе путь из текстового поля."""
    from_disk = stash_upload(files.get(file_field))
    if from_disk is not None:
        return from_disk
    text = form.get(path_field, "").strip()
    if not text:
        return None
    path = Path(text)
    return path if path.is_file() else None


def merge_uploaded_paths(
    form: dict[str, str],
    files: Mapping[str, Uploaded],
    field_names: tuple[str, ...],
) -> dict[str, str]:
    """Подставляет в form пути к временным файлам для каждого поля ``name`` / ``name_file``."""
    merged = dict(form)
    for name in field_names:
        resolved = resolve_upload_path(form, files, f"{name}_file", name)
        if resolved is not None:
            merged[name] = str(resolved)
    return merged