#!/usr/bin/env python3
"""Batch upload cleaned TCM knowledge records through the FastAPI backend."""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import time
from pathlib import Path
from typing import Iterator
from urllib import error, parse, request


DEFAULT_INPUT = Path("data/cleaned/tcm_knowledge_debug_500.jsonl")
DEFAULT_API_URL = "http://127.0.0.1:8000/api/upload_knowledge"
DEFAULT_LOG = Path("data/cleaned/import_results.jsonl")


def read_records(path: Path) -> Iterator[dict[str, str]]:
    base_dir = path.parent
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                content = str(obj.get("content", "")).strip()
                source = str(obj.get("source", "")).strip() or f"{path.name}:{line_no}"
                image_path = resolve_image_path(str(obj.get("image_path", "")).strip(), base_dir)
                if content:
                    yield {"content": content, "source": source, "image_path": image_path}
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row_no, row in enumerate(reader, 1):
                content = str(row.get("content", "")).strip()
                source = str(row.get("source", "")).strip() or f"{path.name}:{row_no}"
                image_path = resolve_image_path(str(row.get("image_path", "")).strip(), base_dir)
                if content:
                    yield {"content": content, "source": source, "image_path": image_path}
    else:
        raise ValueError(f"Unsupported input format: {path}")


def resolve_image_path(raw_path: str, base_dir: Path) -> str:
    if not raw_path:
        return ""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return str(path)


def post_form(api_url: str, record: dict[str, str], timeout: int) -> dict:
    image_path = record.get("image_path", "")
    if image_path:
        return post_multipart(api_url, record, image_path, timeout)

    body = parse.urlencode(
        {
            "content": record["content"],
            "source": record["source"],
        }
    ).encode("utf-8")
    req = request.Request(
        api_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
    )
    with request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def post_multipart(api_url: str, record: dict[str, str], image_path: str, timeout: int) -> dict:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    boundary = f"----tcmrag{int(time.time() * 1000)}"
    body_parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
        body_parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body_parts.append(value.encode("utf-8"))
        body_parts.append(b"\r\n")

    add_field("content", record["content"])
    add_field("source", record["source"])

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
    body_parts.append(
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'.encode("utf-8")
    )
    body_parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
    body_parts.append(path.read_bytes())
    body_parts.append(b"\r\n")
    body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    req = request.Request(
        api_url,
        data=b"".join(body_parts),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Cleaned JSONL or CSV file.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Backend upload endpoint.")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="JSONL import result log.")
    parser.add_argument("--limit", type=int, default=0, help="Upload at most N records. 0 means all.")
    parser.add_argument("--start", type=int, default=1, help="1-based record index to start from.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Seconds to sleep between records.")
    parser.add_argument("--timeout", type=int, default=300, help="HTTP request timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Print records without uploading.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = list(read_records(args.input))
    if args.start < 1:
        raise SystemExit("--start must be >= 1")

    selected = records[args.start - 1 :]
    if args.limit:
        selected = selected[: args.limit]

    print(f"Input: {args.input}")
    print(f"Endpoint: {args.api_url}")
    print(f"Selected records: {len(selected)} / {len(records)}")

    if args.dry_run:
        for index, record in enumerate(selected[:5], args.start):
            print(f"\n[{index}] {record['source']}")
            if record.get("image_path"):
                print(f"image: {record['image_path']}")
            print(record["content"][:300].replace("\n", " | "))
        if len(selected) > 5:
            print(f"\n... {len(selected) - 5} more records")
        return

    args.log.parent.mkdir(parents=True, exist_ok=True)
    success = 0
    failed = 0

    with args.log.open("a", encoding="utf-8") as log:
        for offset, record in enumerate(selected, 0):
            record_index = args.start + offset
            started = time.time()
            try:
                response = post_form(args.api_url, record, timeout=args.timeout)
                success += 1
                result = {
                    "index": record_index,
                    "ok": True,
                    "source": record["source"],
                    "response": response,
                    "elapsed_sec": round(time.time() - started, 3),
                }
                print(f"[{record_index}/{len(records)}] OK {record['source']}")
            except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                failed += 1
                result = {
                    "index": record_index,
                    "ok": False,
                    "source": record["source"],
                    "error": str(exc),
                    "elapsed_sec": round(time.time() - started, 3),
                }
                print(f"[{record_index}/{len(records)}] FAIL {record['source']} :: {exc}")

            log.write(json.dumps(result, ensure_ascii=False) + "\n")
            log.flush()

            if args.sleep:
                time.sleep(args.sleep)

    print(f"\nDone. success={success}, failed={failed}, log={args.log}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
