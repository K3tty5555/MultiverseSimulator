"""文件解析工具"""

import os
from typing import Optional


def extract_text(filepath: str) -> Optional[str]:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        return _parse_pdf(filepath)
    return _parse_text(filepath)


def _parse_pdf(filepath: str) -> Optional[str]:
    try:
        import fitz
        doc = fitz.open(filepath)
        return '\n'.join(page.get_text() for page in doc)
    except Exception as e:
        return None


def _parse_text(filepath: str) -> Optional[str]:
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    try:
        from charset_normalizer import from_path
        result = from_path(filepath).best()
        return str(result) if result else None
    except Exception:
        return None
