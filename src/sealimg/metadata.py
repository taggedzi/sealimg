"""Metadata mapping and XMP embedding helpers for PNG/JPEG."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from html import escape
from pathlib import Path


class MetadataError(ValueError):
    """Raised when metadata operations fail."""


XMP_HEADER = b"http://ns.adobe.com/xap/1.0/\x00"


@dataclass(frozen=True)
class MetadataFields:
    author: str
    website: str
    license: str
    copyright_notice: str | None = None
    title: str | None = None
    description: str | None = None


def build_xmp_packet(fields: MetadataFields) -> bytes:
    rights = fields.copyright_notice or f"Copyright {fields.author}"
    title = fields.title or ""
    description = fields.description or ""

    xml = f"""<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Sealimg">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/"
      xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
      xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"
      xmlns:dcterms="http://purl.org/dc/terms/">
      <dc:creator>
        <rdf:Seq><rdf:li>{escape(fields.author)}</rdf:li></rdf:Seq>
      </dc:creator>
      <dc:rights>
        <rdf:Alt><rdf:li xml:lang="x-default">{escape(rights)}</rdf:li></rdf:Alt>
      </dc:rights>
      <photoshop:CopyrightFlag>True</photoshop:CopyrightFlag>
      <xmpRights:Marked>True</xmpRights:Marked>
      <Iptc4xmpExt:WebStatement>{escape(fields.website)}</Iptc4xmpExt:WebStatement>
      <dcterms:identifier>{escape(fields.website)}</dcterms:identifier>
      <xmpRights:UsageTerms>
        <rdf:Alt><rdf:li xml:lang="x-default">{escape(fields.license)}</rdf:li></rdf:Alt>
      </xmpRights:UsageTerms>
      <dc:title>
        <rdf:Alt><rdf:li xml:lang="x-default">{escape(title)}</rdf:li></rdf:Alt>
      </dc:title>
      <dc:description>
        <rdf:Alt><rdf:li xml:lang="x-default">{escape(description)}</rdf:li></rdf:Alt>
      </dc:description>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""
    return xml.encode("utf-8")


def embed_xmp(input_path: Path, output_path: Path, xmp_packet: bytes) -> None:
    ext = input_path.suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        _embed_xmp_jpeg(input_path, output_path, xmp_packet)
        return
    if ext == ".png":
        _embed_xmp_png(input_path, output_path, xmp_packet)
        return
    raise MetadataError(f"Unsupported metadata target format: {ext}")


def has_xmp(path: Path) -> bool:
    ext = path.suffix.lower()
    data = path.read_bytes()
    if ext in {".jpg", ".jpeg"}:
        return XMP_HEADER in data
    if ext == ".png":
        return b"XML:com.adobe.xmp" in data
    return False


def _embed_xmp_jpeg(input_path: Path, output_path: Path, xmp_packet: bytes) -> None:
    data = input_path.read_bytes()
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        raise MetadataError("Invalid JPEG file")

    payload = XMP_HEADER + xmp_packet
    seg_len = len(payload) + 2
    if seg_len > 65535:
        raise MetadataError("XMP packet too large for JPEG APP1 segment")
    xmp_segment = b"\xff\xe1" + struct.pack(">H", seg_len) + payload

    out = bytearray()
    out.extend(data[:2])  # SOI
    out.extend(xmp_segment)

    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            out.extend(data[i:])
            break

        marker = data[i + 1]
        if marker == 0xDA:  # SOS
            out.extend(data[i:])
            break

        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            out.extend(data[i : i + 2])
            i += 2
            continue

        if i + 4 > len(data):
            raise MetadataError("Truncated JPEG segment header")
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        seg_end = i + 2 + length
        if seg_end > len(data):
            raise MetadataError("Truncated JPEG segment")

        segment = data[i:seg_end]
        segment_payload = segment[4:]
        is_existing_xmp = marker == 0xE1 and segment_payload.startswith(XMP_HEADER)
        if not is_existing_xmp:
            out.extend(segment)
        i = seg_end

    output_path.write_bytes(bytes(out))


def _embed_xmp_png(input_path: Path, output_path: Path, xmp_packet: bytes) -> None:
    data = input_path.read_bytes()
    png_sig = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(png_sig):
        raise MetadataError("Invalid PNG file")

    chunks: list[bytes] = []
    i = len(png_sig)
    while i < len(data):
        if i + 8 > len(data):
            raise MetadataError("Truncated PNG chunk header")
        length = struct.unpack(">I", data[i : i + 4])[0]
        chunk_type = data[i + 4 : i + 8]
        start = i + 8
        end = start + length
        crc_end = end + 4
        if crc_end > len(data):
            raise MetadataError("Truncated PNG chunk")

        chunk_data = data[start:end]
        keep_chunk = True
        if chunk_type == b"iTXt":
            keyword = chunk_data.split(b"\x00", 1)[0]
            if keyword == b"XML:com.adobe.xmp":
                keep_chunk = False

        if keep_chunk:
            chunks.append(data[i:crc_end])
        i = crc_end

    itxt_data = b"XML:com.adobe.xmp\x00\x00\x00\x00\x00" + xmp_packet
    itxt = _make_png_chunk(b"iTXt", itxt_data)

    out = bytearray(png_sig)
    inserted = False
    for raw in chunks:
        ctype = raw[4:8]
        if ctype == b"IEND" and not inserted:
            out.extend(itxt)
            inserted = True
        out.extend(raw)

    if not inserted:
        out.extend(itxt)
        out.extend(_make_png_chunk(b"IEND", b""))

    output_path.write_bytes(bytes(out))


def _make_png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    length = struct.pack(">I", len(chunk_data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF)
    return length + chunk_type + chunk_data + crc
