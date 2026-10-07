#!/usr/bin/env python3
"""Read-only paper discovery through Zotero, Semantic Scholar, DeepXiv and Exa."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


SOURCES = ("zotero", "s2", "deepxiv", "exa")
KEYS = ("SEMANTIC_SCHOLAR_API_KEY", "DEEPXIV_TOKEN", "EXA_API_KEY")


def settings() -> dict[str, str]:
    """Read simple KEY=value lines from the current project; environment wins."""
    values: dict[str, str] = {}
    path = Path.cwd() / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key in KEYS:
                values[key] = value.strip().strip('"\'')
    for key in KEYS:
        if os.environ.get(key):
            values[key] = os.environ[key].strip()
    return values


def request_json(url: str, *, headers: dict[str, str] | None = None,
                 body: dict | None = None, timeout: int = 20) -> object:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        url, data=data, method="POST" if body is not None else "GET",
        headers={"User-Agent": "literature-landscape/1.0", "Accept": "application/json",
                 **(headers or {})},
    )
    host = urllib.parse.urlsplit(url).netloc
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {exc.code} from {host}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Connection failed to {host}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON from {host}") from exc
    raise RuntimeError(f"Request failed to {host}")


def original_url(doi: str = "", arxiv_id: str = "", fallback: str = "") -> str:
    doi = doi.removeprefix("https://doi.org/").removeprefix("doi:")
    arxiv_id = arxiv_id.removeprefix("arXiv:")
    return ("https://doi.org/" + doi if doi else
            "https://arxiv.org/abs/" + arxiv_id if arxiv_id else fallback)


def search_zotero(query: str, limit: int, _: dict[str, str]) -> list[dict]:
    url = "http://127.0.0.1:23119/api/users/0/items/top?" + urllib.parse.urlencode(
        {"q": query, "limit": limit, "format": "json"})
    payload = request_json(url, headers={"Zotero-API-Version": "3"}, timeout=4)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Zotero response")
    records = []
    for item in payload:
        data = item.get("data") or {}
        if data.get("itemType") in {"attachment", "note", "annotation"}:
            continue
        authors = [c.get("name") or " ".join(filter(None, (c.get("firstName"), c.get("lastName"))))
                   for c in data.get("creators") or []]
        key = item.get("key") or data.get("key") or ""
        doi = (data.get("DOI") or "").strip()
        records.append({"source": "zotero", "source_url":
                        f"http://127.0.0.1:23119/api/users/0/items/{key}" if key else "",
                        "title": data.get("title") or "", "authors": [a for a in authors if a],
                        "year_or_date": data.get("date") or "", "doi": doi,
                        "paper_url": original_url(doi, fallback=data.get("url") or ""),
                        "abstract": data.get("abstractNote") or ""})
    return records


def search_s2(query: str, limit: int, config: dict[str, str]) -> list[dict]:
    fields = "title,year,authors,abstract,url,venue,externalIds,openAccessPdf"
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(
        {"query": query, "limit": limit, "fields": fields})
    headers = {"x-api-key": config["SEMANTIC_SCHOLAR_API_KEY"]} if config.get("SEMANTIC_SCHOLAR_API_KEY") else {}
    payload = request_json(url, headers=headers)
    records = []
    for item in payload.get("data", []):
        ids = item.get("externalIds") or {}
        doi, arxiv_id = ids.get("DOI") or "", ids.get("ArXiv") or ""
        records.append({"source": "semantic-scholar", "source_url": item.get("url") or "",
                        "title": item.get("title") or "",
                        "authors": [a.get("name") for a in item.get("authors") or [] if a.get("name")],
                        "year_or_date": item.get("year") or "", "venue": item.get("venue") or "",
                        "doi": doi, "arxiv_id": arxiv_id,
                        "paper_url": original_url(doi, arxiv_id,
                                                  (item.get("openAccessPdf") or {}).get("url") or item.get("url") or ""),
                        "abstract": item.get("abstract") or ""})
    return records


def search_deepxiv(query: str, limit: int, config: dict[str, str]) -> list[dict]:
    if not shutil.which("deepxiv"):
        raise LookupError("install deepxiv-sdk to enable DeepXiv")
    env = os.environ.copy()
    if config.get("DEEPXIV_TOKEN"):
        env["DEEPXIV_TOKEN"] = config["DEEPXIV_TOKEN"]
    for attempt in range(2):
        proc = subprocess.run(["deepxiv", "search", query, "--limit", str(limit), "--format", "json"],
                              capture_output=True, text=True, timeout=50, env=env, check=False)
        if proc.returncode:
            raise RuntimeError(f"DeepXiv exited {proc.returncode}")
        try:
            payload = json.loads(proc.stdout)
            break
        except json.JSONDecodeError as exc:
            if attempt:
                raise RuntimeError("Invalid DeepXiv JSON") from exc
    items = payload if isinstance(payload, list) else next(
        (payload[k] for k in ("result", "results", "papers", "data", "items")
         if isinstance(payload, dict) and isinstance(payload.get(k), list)), [])
    records = []
    for item in items:
        if not isinstance(item, dict):
            continue
        arxiv_id = item.get("arxiv_id") or item.get("arxivId") or ""
        url = item.get("url") or item.get("abs_url") or ""
        records.append({"source": "deepxiv", "source_url": url,
                        "title": item.get("title") or "", "authors": item.get("authors") or [],
                        "year_or_date": item.get("year") or item.get("published") or "",
                        "arxiv_id": arxiv_id, "paper_url": original_url(arxiv_id=arxiv_id, fallback=url),
                        "abstract": item.get("abstract") or item.get("tldr") or ""})
    return records


def search_exa(query: str, limit: int, config: dict[str, str]) -> list[dict]:
    key = config.get("EXA_API_KEY")
    if not key:
        raise LookupError("set EXA_API_KEY to enable Exa")
    payload = request_json("https://api.exa.ai/search",
                           headers={"x-api-key": key, "Content-Type": "application/json"},
                           body={"query": query, "type": "auto", "category": "publication",
                                 "numResults": limit, "contents": {"highlights": True}})
    return [{"source": "exa", "source_url": item.get("url") or "",
             "title": item.get("title") or "", "authors": [item["author"]] if item.get("author") else [],
             "year_or_date": item.get("publishedDate") or "", "paper_url": item.get("url") or "",
             "highlights": item.get("highlights") or []}
            for item in payload.get("results", [])]


def doctor(config: dict[str, str]) -> dict[str, str]:
    try:
        items = request_json("http://127.0.0.1:23119/api/users/0/items/top?limit=1&format=json", timeout=4)
        if not isinstance(items, list):
            raise RuntimeError("Unexpected Zotero response")
        zotero = "available"
    except RuntimeError:
        zotero = "unavailable: open Zotero Desktop and enable local API"
    if config.get("SEMANTIC_SCHOLAR_API_KEY"):
        try:
            request_json(
                "https://api.semanticscholar.org/graph/v1/paper/ARXIV:1706.03762?fields=title",
                headers={"x-api-key": config["SEMANTIC_SCHOLAR_API_KEY"]}, timeout=12,
            )
            s2 = "available"
        except RuntimeError as exc:
            s2 = f"key present but API check failed: {exc}"
    else:
        s2 = "no key; public API may return HTTP 429"
    return {"zotero": zotero,
            "semantic-scholar": s2,
            "deepxiv": "CLI installed" if shutil.which("deepxiv") else "CLI missing: install deepxiv-sdk",
            "exa": "key configured" if config.get("EXA_API_KEY") else "key missing: set EXA_API_KEY"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="English research query")
    parser.add_argument("--sources", default=",".join(SOURCES), help="zotero,s2,deepxiv,exa")
    parser.add_argument("--limit", type=int, default=8, help="results per source (1–20)")
    parser.add_argument("--doctor", action="store_true", help="check available sources without revealing keys")
    args = parser.parse_args()
    config = settings()
    if args.doctor:
        print(json.dumps(doctor(config), ensure_ascii=False, indent=2))
        return 0
    if not args.query or not 1 <= args.limit <= 20:
        parser.error("provide a query and a --limit between 1 and 20")
    selected = list(dict.fromkeys(x.strip() for x in args.sources.split(",") if x.strip()))
    if not selected or any(x not in SOURCES for x in selected):
        parser.error("--sources must contain zotero,s2,deepxiv,exa")
    fetchers = {"zotero": search_zotero, "s2": search_s2,
                "deepxiv": search_deepxiv, "exa": search_exa}
    result: dict = {"query": args.query, "sources": {}}
    successes = 0
    for source in selected:
        try:
            records = fetchers[source](args.query, args.limit, config)
            result["sources"][source] = {"status": "ok", "count": len(records), "records": records}
            successes += 1
        except LookupError as exc:
            result["sources"][source] = {"status": "skipped", "reason": str(exc)}
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            result["sources"][source] = {"status": "error", "reason": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if successes else 2


if __name__ == "__main__":
    sys.exit(main())
