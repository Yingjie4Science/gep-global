#!/usr/bin/env python3
"""Fetch one GLC_FCS30D tile from a Zenodo ZIP and extract its 2019 band."""

from __future__ import annotations

import argparse
import binascii
import io
from pathlib import Path
import struct
import subprocess
import os
import re
import tempfile
import urllib.request
import zipfile
import zlib


def request_bytes(url: str, start: int, end: int) -> bytes:
    # Optional curl transport works around Python TLS failures without disabling
    # certificate validation. Check the returned range before accepting bytes.
    if os.environ.get('GEP_DOWNLOAD_TRANSPORT') == 'curl':
        with tempfile.TemporaryDirectory() as folder:
            headers = Path(folder) / 'headers'
            body = Path(folder) / 'body'
            subprocess.run(['curl', '--silent', '--show-error', '--fail', '--location',
                            '--retry', '3', '--retry-all-errors', '--connect-timeout', '20',
                            '--max-time', '180', '--range', f'{start}-{end}',
                            '--dump-header', str(headers), '--output', str(body), url], check=True)
            text = headers.read_text()
            ranges = re.findall(r'(?im)^content-range:\s*bytes (\d+)-(\d+)/', text)
            if not ranges or ranges[-1] != (str(start), str(end)):
                raise RuntimeError('curl response did not match requested byte range')
            data = body.read_bytes()
            if len(data) != end-start+1:
                raise RuntimeError('curl response length mismatch')
            return data
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(request, timeout=300) as response:
        if response.status != 206:
            raise RuntimeError(f"Expected HTTP 206 for range {start}-{end}; got {response.status}")
        expected_range = f"bytes {start}-{end}/"
        if not response.headers.get("Content-Range", "").startswith(expected_range):
            raise RuntimeError("Server returned an unexpected Content-Range")
        data = response.read()
    expected = end - start + 1
    if len(data) != expected:
        raise RuntimeError(f"Range returned {len(data)} bytes; expected {expected}")
    return data


def content_length(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=120) as response:
        return int(response.headers["Content-Length"])


def member_info(url: str, member: str) -> zipfile.ZipInfo:
    size = content_length(url)
    tail_size = min(size, 16 * 1024 * 1024)
    tail = request_bytes(url, size - tail_size, size - 1)
    with tempfile.NamedTemporaryFile(suffix=".zip") as sparse:
        sparse.truncate(size)
        sparse.seek(size - tail_size)
        sparse.write(tail)
        sparse.flush()
        with zipfile.ZipFile(sparse.name) as archive:
            return archive.getinfo(member)


def fetch_member(url: str, member: str, output: Path) -> zipfile.ZipInfo:
    info = member_info(url, member)
    header = request_bytes(url, info.header_offset, info.header_offset + 65535)
    signature, *_fields, name_length, extra_length = struct.unpack("<4s5H3I2H", header[:30])
    if signature != b"PK\x03\x04":
        raise RuntimeError("Invalid ZIP local header")
    data_start = info.header_offset + 30 + name_length + extra_length
    compressed = request_bytes(url, data_start, data_start + info.compress_size - 1)
    if info.compress_type == zipfile.ZIP_DEFLATED:
        content = zlib.decompress(compressed, -15)
    elif info.compress_type == zipfile.ZIP_STORED:
        content = compressed
    else:
        raise RuntimeError(f"Unsupported ZIP compression method: {info.compress_type}")
    if len(content) != info.file_size:
        raise RuntimeError("Extracted member size mismatch")
    if (binascii.crc32(content) & 0xFFFFFFFF) != info.CRC:
        raise RuntimeError("Extracted member CRC mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    return info


def extract_2019(source: Path, output: Path) -> None:
    import rasterio

    band = 20  # band 1 is 2000, so band 20 is 2019
    with rasterio.open(source) as src:
        if src.count != 23:
            raise RuntimeError(f"Expected 23 annual bands for 2000-2022; found {src.count}")
        profile = src.profile.copy()
        profile.update(count=1, compress="deflate", tiled=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output, "w", **profile) as dst:
            for _, window in src.block_windows(band):
                dst.write(src.read(band, window=window), 1, window=window)
            dst.set_band_description(1, "GLC_FCS30D land cover, 2019 (source annual band 20)")
            dst.update_tags(
                source_member=source.name,
                source_band="20",
                source_year="2019",
                preprocessing="Extracted without resampling from the 2000-2022 annual tile",
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive_url")
    parser.add_argument("member")
    parser.add_argument("raw_output", type=Path)
    parser.add_argument("year2019_output", type=Path)
    args = parser.parse_args()
    info = fetch_member(args.archive_url, args.member, args.raw_output)
    print(f"Fetched {info.filename}: {info.file_size} bytes; CRC {info.CRC:08x}")
    extract_2019(args.raw_output, args.year2019_output)
    print(f"Created 2019 land-cover tile: {args.year2019_output}")


if __name__ == "__main__":
    main()
