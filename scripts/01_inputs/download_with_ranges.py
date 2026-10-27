#!/usr/bin/env python3
"""Resumable parallel HTTP downloader for large public research files."""

from __future__ import annotations

import argparse
import hashlib
import math
import os
from pathlib import Path
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def remote_size(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=120) as response:
        value = response.headers.get("Content-Length")
    if not value:
        raise RuntimeError(f"Server did not report Content-Length: {url}")
    return int(value)


def download_part(url: str, part: Path, start: int, end: int, retries: int) -> None:
    expected = end - start + 1
    if part.exists() and part.stat().st_size == expected:
        return
    partial = part.with_suffix(part.suffix + ".partial")
    for attempt in range(1, retries + 1):
        try:
            existing = partial.stat().st_size if partial.exists() else 0
            if existing > expected:
                partial.unlink()
                existing = 0
            headers = {"Range": f"bytes={start + existing}-{end}"}
            request = urllib.request.Request(url, headers=headers)
            mode = "ab" if existing else "wb"
            with urllib.request.urlopen(request, timeout=180) as response, partial.open(mode) as target:
                if response.status != 206:
                    raise RuntimeError(f"Range request returned HTTP {response.status}")
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    target.write(block)
            if partial.stat().st_size != expected:
                raise RuntimeError(f"Part has {partial.stat().st_size} bytes; expected {expected}")
            partial.replace(part)
            return
        except Exception:
            if attempt == retries:
                raise
            time.sleep(min(30, 2 ** attempt))


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--chunk-mib", type=int, default=64)
    parser.add_argument("--retries", type=int, default=8)
    parser.add_argument("--checksum", help="Expected checksum as md5:HEX or sha256:HEX")
    args = parser.parse_args()

    size = remote_size(args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() and args.output.stat().st_size == size:
        print(f"Already complete: {args.output} ({size} bytes)")
    else:
        part_dir = args.output.with_name(args.output.name + ".parts")
        part_dir.mkdir(exist_ok=True)
        chunk = args.chunk_mib * 1024 * 1024
        ranges = []
        for index in range(math.ceil(size / chunk)):
            start = index * chunk
            end = min(size - 1, start + chunk - 1)
            ranges.append((index, start, end))
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(download_part, args.url, part_dir / f"{index:06d}.part", start, end, args.retries): index
                for index, start, end in ranges
            }
            finished = 0
            for future in as_completed(futures):
                future.result()
                finished += 1
                if finished == 1 or finished % 8 == 0 or finished == len(ranges):
                    print(f"Downloaded {finished}/{len(ranges)} parts", flush=True)
        temporary = args.output.with_suffix(args.output.suffix + ".assembling")
        with temporary.open("wb") as target:
            for index, _, _ in ranges:
                with (part_dir / f"{index:06d}.part").open("rb") as source:
                    while True:
                        block = source.read(8 * 1024 * 1024)
                        if not block:
                            break
                        target.write(block)
        if temporary.stat().st_size != size:
            raise RuntimeError("Assembled file size mismatch")
        temporary.replace(args.output)
        for child in part_dir.iterdir():
            child.unlink()
        part_dir.rmdir()
        print(f"Completed: {args.output} ({size} bytes)")

    if args.checksum:
        algorithm, expected = args.checksum.split(":", 1)
        actual = digest(args.output, algorithm.lower())
        if actual.lower() != expected.lower():
            raise RuntimeError(f"Checksum mismatch: expected {expected}, got {actual}")
        print(f"Verified {algorithm.lower()}: {actual}")


if __name__ == "__main__":
    main()
