"""Разбор POST из браузера: поля и загруженные файлы."""

from __future__ import annotations

import cgi
import io
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qs


@dataclass(frozen=True)
class Uploaded:
    filename: str
    data: bytes


def parse_post_body(content_type: str | None, body: bytes) -> tuple[dict[str, str], dict[str, Uploaded]]:
    if content_type and "multipart/form-data" in content_type.lower():
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(len(body)),
        }
        fields: dict[str, str] = {}
        files: dict[str, Uploaded] = {}
        form = cgi.FieldStorage(fp=io.BytesIO(body), environ=environ, keep_blank_values=True)
        if isinstance(form.list, list):
            for item in form.list:
                name = item.name
                if not name:
                    continue
                if item.filename:
                    payload = item.file.read() if item.file else b""
                    if payload:
                        files[name] = Uploaded(item.filename, payload)
                else:
                    fields[name] = item.value if item.value is not None else ""
        return fields, files
    text = body.decode("utf-8", errors="replace")
    fields = {key: values[0] for key, values in parse_qs(text).items()}
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