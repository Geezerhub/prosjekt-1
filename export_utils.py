from __future__ import annotations

from pathlib import Path


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_text_pdf(text: str, output_path: Path, title: str = "Oppskrift") -> None:
    """Write a minimal PDF containing plain text (WinAnsi/Latin-1 safe)."""
    sanitized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = sanitized.split("\n")

    page_width = 595
    page_height = 842
    top = 800
    left = 50
    line_height = 14
    bottom = 50

    max_lines_per_page = max(1, (top - bottom) // line_height)

    pages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        wrapped = [line[i : i + 95] for i in range(0, len(line), 95)] or [""]
        for wline in wrapped:
            current.append(wline)
            if len(current) >= max_lines_per_page:
                pages.append(current)
                current = []
    if current:
        pages.append(current)
    if not pages:
        pages = [[""]]

    objects: list[bytes] = []

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    font_obj = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    content_ids: list[int] = []
    page_ids: list[int] = []

    for page_lines in pages:
        y = top
        stream_parts = [b"BT", b"/F1 11 Tf"]
        for line in page_lines:
            safe = _pdf_escape(line).encode("latin-1", errors="replace")
            stream_parts.append(f"1 0 0 1 {left} {y} Tm".encode("ascii"))
            stream_parts.append(b"(" + safe + b") Tj")
            y -= line_height
        stream_parts.append(b"ET")
        stream = b"\n".join(stream_parts) + b"\n"

        content_payload = b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream"
        content_id = add_object(content_payload)
        content_ids.append(content_id)

        page_payload = (
            b"<< /Type /Page /Parent PAGES_ID 0 R /MediaBox [0 0 "
            + str(page_width).encode("ascii")
            + b" "
            + str(page_height).encode("ascii")
            + b"] /Resources << /Font << /F1 "
            + str(font_obj).encode("ascii")
            + b" 0 R >> >> /Contents "
            + str(content_id).encode("ascii")
            + b" 0 R >>"
        )
        page_id = add_object(page_payload)
        page_ids.append(page_id)

    kids = b"[" + b" ".join(f"{pid} 0 R".encode("ascii") for pid in page_ids) + b"]"
    pages_obj = add_object(b"<< /Type /Pages /Kids " + kids + b" /Count " + str(len(page_ids)).encode("ascii") + b" >>")

    # patch page parent refs
    for pid in page_ids:
        objects[pid - 1] = objects[pid - 1].replace(b"PAGES_ID", str(pages_obj).encode("ascii"))

    title_safe = _pdf_escape(title).encode("latin-1", errors="replace")
    catalog_obj = add_object(b"<< /Type /Catalog /Pages " + str(pages_obj).encode("ascii") + b" 0 R >>")
    info_obj = add_object(b"<< /Title (" + title_safe + b") /Producer (Oppskriftsapp) >>")

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    trailer = (
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode("ascii")
        + b" /Root "
        + str(catalog_obj).encode("ascii")
        + b" 0 R /Info "
        + str(info_obj).encode("ascii")
        + b" 0 R >>\nstartxref\n"
        + str(xref_pos).encode("ascii")
        + b"\n%%EOF\n"
    )
    pdf.extend(trailer)

    output_path.write_bytes(bytes(pdf))
