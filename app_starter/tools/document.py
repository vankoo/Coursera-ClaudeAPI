from markitdown import MarkItDown, StreamInfo
from io import BytesIO
from pathlib import Path

from pydantic import Field

SUPPORTED_EXTENSIONS = {"pdf", "docx"}


def binary_document_to_markdown(binary_data: bytes, file_type: str) -> str:
    """Converts binary document data to markdown-formatted text."""
    md = MarkItDown()
    file_obj = BytesIO(binary_data)
    stream_info = StreamInfo(extension=file_type)
    result = md.convert(file_obj, stream_info=stream_info)
    return result.text_content


def document_path_to_markdown(
    path: str | Path = Field(
        description="Path to a PDF or DOCX file on the local filesystem. "
        "Accepts either a string path or a pathlib.Path."
    ),
) -> str:
    """Read a PDF or DOCX file from disk and convert its contents to markdown.

    Opens the file at the given path, reads its binary contents, and converts
    them to markdown-formatted text. Only PDF (.pdf) and DOCX (.docx) files are
    supported; the file type is determined by the path's extension
    (case-insensitive).

    On any failure -- the file does not exist, is a directory, cannot be read,
    has an unsupported extension, or cannot be parsed -- this returns a string
    beginning with "Error:" describing the problem rather than raising an
    exception, so the caller always receives a readable result.

    When to use:
    - When you have a file path (rather than raw bytes) to a PDF or DOCX
      document and want its contents as markdown text.

    When not to use:
    - When you already hold the document's bytes; use
      binary_document_to_markdown instead.

    Examples:
    >>> document_path_to_markdown("docs/report.pdf")
    '# Report\\n\\n...'
    >>> document_path_to_markdown("missing.pdf")
    'Error: file not found: missing.pdf'
    """
    file_path = Path(path)

    if not file_path.exists():
        return f"Error: file not found: {file_path}"

    if file_path.is_dir():
        return f"Error: path is a directory, not a file: {file_path}"

    extension = file_path.suffix.lstrip(".").lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return (
            f"Error: unsupported file type '{file_path.suffix or '(none)'}' for "
            f"'{file_path}'. Supported types: {supported}."
        )

    try:
        binary_data = file_path.read_bytes()
    except OSError as exc:
        return f"Error: could not read file '{file_path}': {exc}"

    try:
        return binary_document_to_markdown(binary_data, extension)
    except Exception as exc:
        return f"Error: could not convert '{file_path}' to markdown: {exc}"
