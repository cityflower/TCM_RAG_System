#!/usr/bin/env python3
"""Clean TCM datasets into JSONL records ready for knowledge-base import."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Iterator


DEFAULT_DATASET_DIR = Path("/Users/whs/WHS/xmut/毕业论文/毕设数据集")
DEFAULT_CSV = DEFAULT_DATASET_DIR / "bb613e73-950f-43ff-8c5c-ce7e84a0a7f4.csv"
DEFAULT_CHATMED = DEFAULT_DATASET_DIR / "ChatMed_TCM-v0.2.json"
DEFAULT_HWTCM = DEFAULT_DATASET_DIR / "hwtcm.json"
DEFAULT_OUTPUT_DIR = Path("data/cleaned")


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines).strip()


def clean_question(text: str) -> str:
    text = normalize_text(text)
    text = re.split(r"要求[:：]", text, maxsplit=1)[0]
    text = re.sub(r"请(?:根据)?输出.*?推理过程[。；;，,]?", "", text)
    text = re.sub(r"请.*?一步步.*?推理过程[。；;，,]?", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" ，,。；;")


def content_fingerprint(content: str) -> str:
    compact = re.sub(r"\s+", "", content)
    return hashlib.sha1(compact.encode("utf-8")).hexdigest()


def split_text(text: str, max_chars: int, prefix: str = "") -> list[str]:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[。！？；;])", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            for start in range(0, len(sentence), max_chars):
                chunks.append(sentence[start : start + max_chars].strip())
            continue

        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current}{sentence}" if current else sentence

    if current:
        chunks.append(current.strip())

    if prefix:
        prefixed = []
        for chunk in chunks:
            if not chunk.startswith(prefix):
                prefixed.append(f"{prefix}\n{chunk}")
            else:
                prefixed.append(chunk)
        chunks = prefixed

    return chunks


def extract_syndrome_name(text: str, fallback_index: int) -> str:
    match = re.search(r"证型名称[:：]\s*([^\n]+)", text)
    if match:
        return match.group(1).strip()
    return f"证型记录{fallback_index:04d}"


def iter_json_records(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8-sig") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            data = json.load(f)
            for item in data:
                if isinstance(item, dict):
                    yield item
        else:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    yield item


def make_record(
    *,
    record_id: str,
    content: str,
    source: str,
    dataset: str,
    record_type: str,
    metadata: dict | None = None,
) -> dict:
    return {
        "id": record_id,
        "content": normalize_text(content),
        "source": source,
        "data_type": "text",
        "metadata": {
            "dataset": dataset,
            "record_type": record_type,
            **(metadata or {}),
        },
    }


def clean_syndrome_csv(path: Path, max_chars: int) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for index, row in enumerate(reader, 1):
            text = normalize_text(row.get("text"))
            if not text:
                continue
            name = extract_syndrome_name(text, index)
            prefix = f"证型名称：{name}"
            chunks = split_text(text, max_chars=max_chars, prefix=prefix)
            for chunk_index, chunk in enumerate(chunks, 1):
                suffix = f"片段{chunk_index}" if len(chunks) > 1 else "完整"
                records.append(
                    make_record(
                        record_id=f"syndrome-{index:04d}-{chunk_index:02d}",
                        content=chunk,
                        source=f"证型知识库/{name}/{suffix}",
                        dataset=path.name,
                        record_type="syndrome",
                        metadata={
                            "title": name,
                            "original_index": index,
                            "chunk_index": chunk_index,
                            "chunk_total": len(chunks),
                        },
                    )
                )
    return records


def clean_hwtcm(path: Path, min_score: float, max_chars: int) -> list[dict]:
    records: list[dict] = []
    for index, obj in enumerate(iter_json_records(path), 1):
        score = float(obj.get("score") or 0)
        if score < min_score:
            continue

        instruction = clean_question(obj.get("instruction", ""))
        extra_input = normalize_text(obj.get("input", ""))
        output = normalize_text(obj.get("output", ""))
        category = normalize_text(obj.get("category", "未分类"))
        if not instruction or not output:
            continue

        question = f"{instruction}\n补充信息：{extra_input}" if extra_input else instruction
        content = f"问题：{question}\n回答：{output}"
        chunks = split_text(content, max_chars=max_chars)
        for chunk_index, chunk in enumerate(chunks, 1):
            suffix = f"片段{chunk_index}" if len(chunks) > 1 else "完整"
            records.append(
                make_record(
                    record_id=f"hwtcm-{index:05d}-{chunk_index:02d}",
                    content=chunk,
                    source=f"HWTCM/{category}/评分{score:g}/{suffix}",
                    dataset=path.name,
                    record_type="qa",
                    metadata={
                        "category": category,
                        "score": score,
                        "original_index": index,
                        "chunk_index": chunk_index,
                        "chunk_total": len(chunks),
                    },
                )
            )
    return records


def clean_chatmed(path: Path, limit: int, max_chars: int) -> list[dict]:
    records: list[dict] = []
    seen_questions: set[str] = set()
    for index, obj in enumerate(iter_json_records(path), 1):
        query = clean_question(obj.get("query", ""))
        response = normalize_text(obj.get("response", ""))
        if not query or not response:
            continue
        if len(query) < 6 or len(response) < 40:
            continue

        question_key = re.sub(r"\s+", "", query)
        if question_key in seen_questions:
            continue
        seen_questions.add(question_key)

        content = f"问题：{query}\n回答：{response}"
        chunks = split_text(content, max_chars=max_chars)
        for chunk_index, chunk in enumerate(chunks, 1):
            suffix = f"片段{chunk_index}" if len(chunks) > 1 else "完整"
            records.append(
                make_record(
                    record_id=f"chatmed-{index:06d}-{chunk_index:02d}",
                    content=chunk,
                    source=f"ChatMed_TCM/问答案例/{suffix}",
                    dataset=path.name,
                    record_type="qa",
                    metadata={
                        "original_index": index,
                        "chunk_index": chunk_index,
                        "chunk_total": len(chunks),
                    },
                )
            )

        if limit and len(records) >= limit:
            return records[:limit]
    return records


def dedupe_records(records: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for record in records:
        key = content_fingerprint(record["content"])
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def write_jsonl(path: Path, records: Iterable[dict]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_upload_csv(path: Path, records: Iterable[dict]) -> int:
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["content", "source"])
        writer.writeheader()
        for record in records:
            writer.writerow({"content": record["content"], "source": record["source"]})
            count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--chatmed", type=Path, default=DEFAULT_CHATMED)
    parser.add_argument("--hwtcm", type=Path, default=DEFAULT_HWTCM)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--chatmed-limit", type=int, default=5000)
    parser.add_argument("--hwtcm-min-score", type=float, default=7.0)
    parser.add_argument("--max-chars", type=int, default=1200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    syndrome_records = clean_syndrome_csv(args.csv, max_chars=args.max_chars)
    hwtcm_records = clean_hwtcm(args.hwtcm, min_score=args.hwtcm_min_score, max_chars=args.max_chars)
    chatmed_records = clean_chatmed(args.chatmed, limit=args.chatmed_limit, max_chars=args.max_chars)

    combined = dedupe_records([*syndrome_records, *hwtcm_records, *chatmed_records])

    outputs = {
        "syndrome_cleaned.jsonl": syndrome_records,
        "hwtcm_cleaned.jsonl": hwtcm_records,
        "chatmed_sample_cleaned.jsonl": chatmed_records,
        "tcm_knowledge_pilot.jsonl": combined,
    }

    summary = {
        "settings": {
            "chatmed_limit": args.chatmed_limit,
            "hwtcm_min_score": args.hwtcm_min_score,
            "max_chars": args.max_chars,
        },
        "counts": {},
        "outputs": {},
    }

    for filename, records in outputs.items():
        output_path = args.out_dir / filename
        count = write_jsonl(output_path, records)
        summary["counts"][filename] = count
        summary["outputs"][filename] = str(output_path)

    csv_count = write_upload_csv(args.out_dir / "tcm_knowledge_pilot_upload.csv", combined)
    summary["counts"]["tcm_knowledge_pilot_upload.csv"] = csv_count
    summary["outputs"]["tcm_knowledge_pilot_upload.csv"] = str(
        args.out_dir / "tcm_knowledge_pilot_upload.csv"
    )

    summary_path = args.out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
