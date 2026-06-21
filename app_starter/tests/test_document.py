import os
import shutil
from pathlib import Path

import pytest

from tools.document import binary_document_to_markdown, document_path_to_markdown


class TestBinaryDocumentToMarkdown:
    # Define fixture paths
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    def test_fixture_files_exist(self):
        """Verify test fixtures exist."""
        assert os.path.exists(self.DOCX_FIXTURE), (
            f"DOCX fixture not found at {self.DOCX_FIXTURE}"
        )
        assert os.path.exists(self.PDF_FIXTURE), (
            f"PDF fixture not found at {self.PDF_FIXTURE}"
        )

    def test_binary_document_to_markdown_with_docx(self):
        """Test converting a DOCX document to markdown."""
        # Read binary content from the fixture
        with open(self.DOCX_FIXTURE, "rb") as f:
            docx_data = f.read()

        # Call function
        result = binary_document_to_markdown(docx_data, "docx")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result

    def test_binary_document_to_markdown_with_pdf(self):
        """Test converting a PDF document to markdown."""
        # Read binary content from the fixture
        with open(self.PDF_FIXTURE, "rb") as f:
            pdf_data = f.read()

        # Call function
        result = binary_document_to_markdown(pdf_data, "pdf")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result


class TestDocumentPathToMarkdown:
    """Tests for document_path_to_markdown.

    Contract:
    - Accepts the path to a PDF or DOCX file as either a str or a pathlib.Path.
    - Reads the file and returns its contents converted to markdown.
    - On any failure (missing file, unreadable file, unsupported type,
      unparseable content) it RETURNS an error string rather than raising.
      Error strings are identified by containing "error" (case-insensitive).
    """

    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    @staticmethod
    def _is_error(result) -> bool:
        return isinstance(result, str) and "error" in result.lower()

    @staticmethod
    def _looks_like_markdown(result) -> bool:
        return (
            isinstance(result, str)
            and len(result) > 0
            and ("#" in result or "-" in result or "*" in result)
        )

    # --- Happy path: str input ---------------------------------------------

    def test_docx_path_as_str(self):
        """A DOCX path given as a str converts to non-empty markdown."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)
        assert not self._is_error(result)
        assert self._looks_like_markdown(result)

    def test_pdf_path_as_str(self):
        """A PDF path given as a str converts to non-empty markdown."""
        result = document_path_to_markdown(self.PDF_FIXTURE)
        assert not self._is_error(result)
        assert self._looks_like_markdown(result)

    # --- Happy path: pathlib.Path input ------------------------------------

    def test_docx_path_as_pathlib(self):
        """A DOCX path given as a pathlib.Path converts to non-empty markdown."""
        result = document_path_to_markdown(Path(self.DOCX_FIXTURE))
        assert not self._is_error(result)
        assert self._looks_like_markdown(result)

    def test_pdf_path_as_pathlib(self):
        """A PDF path given as a pathlib.Path converts to non-empty markdown."""
        result = document_path_to_markdown(Path(self.PDF_FIXTURE))
        assert not self._is_error(result)
        assert self._looks_like_markdown(result)

    def test_str_and_pathlib_produce_same_output(self):
        """str and Path inputs for the same file yield identical markdown."""
        from_str = document_path_to_markdown(self.PDF_FIXTURE)
        from_path = document_path_to_markdown(Path(self.PDF_FIXTURE))
        assert from_str == from_path

    # --- Equivalence with the binary converter -----------------------------

    def test_matches_binary_converter_docx(self):
        """Path conversion matches reading bytes + binary_document_to_markdown."""
        with open(self.DOCX_FIXTURE, "rb") as f:
            expected = binary_document_to_markdown(f.read(), "docx")
        assert document_path_to_markdown(self.DOCX_FIXTURE) == expected

    def test_matches_binary_converter_pdf(self):
        """Path conversion matches reading bytes + binary_document_to_markdown."""
        with open(self.PDF_FIXTURE, "rb") as f:
            expected = binary_document_to_markdown(f.read(), "pdf")
        assert document_path_to_markdown(self.PDF_FIXTURE) == expected

    # --- File-type handling ------------------------------------------------

    def test_uppercase_extension_is_accepted(self):
        """Extension matching is case-insensitive (e.g. .PDF)."""
        dest = Path(self.FIXTURES_DIR).parent / "tmp_upper.PDF"
        shutil.copy(self.PDF_FIXTURE, dest)
        try:
            result = document_path_to_markdown(dest)
            assert not self._is_error(result)
            assert self._looks_like_markdown(result)
        finally:
            dest.unlink(missing_ok=True)

    def test_unsupported_extension_returns_error(self, tmp_path):
        """A non-PDF/DOCX file (e.g. .txt) returns an error string."""
        bad = tmp_path / "notes.txt"
        bad.write_text("just some plain text")
        assert self._is_error(document_path_to_markdown(bad))

    def test_missing_extension_returns_error(self, tmp_path):
        """A file with no extension returns an error string."""
        bad = tmp_path / "noextension"
        bad.write_bytes(b"%PDF-1.4 not really")
        assert self._is_error(document_path_to_markdown(bad))

    # --- Error handling: returns a string, never raises --------------------

    def test_nonexistent_path_returns_error(self, tmp_path):
        """A path that does not exist returns an error string (no exception)."""
        missing = tmp_path / "does_not_exist.pdf"
        result = document_path_to_markdown(missing)
        assert self._is_error(result)

    def test_directory_path_returns_error(self, tmp_path):
        """Passing a directory instead of a file returns an error string."""
        result = document_path_to_markdown(tmp_path)
        assert self._is_error(result)

    def test_empty_file_returns_error(self, tmp_path):
        """A zero-byte file with a valid extension returns an error string."""
        empty = tmp_path / "empty.pdf"
        empty.write_bytes(b"")
        assert self._is_error(document_path_to_markdown(empty))

    def test_corrupted_file_returns_error(self, tmp_path):
        """A .pdf containing non-document bytes returns an error string."""
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_bytes(b"\x00\x01\x02 this is not a real pdf \xff\xfe")
        assert self._is_error(document_path_to_markdown(corrupt))

    def test_unreadable_file_returns_error(self, tmp_path):
        """A file without read permission returns an error string."""
        locked = tmp_path / "locked.pdf"
        shutil.copy(self.PDF_FIXTURE, locked)
        locked.chmod(0o000)
        try:
            result = document_path_to_markdown(locked)
            assert self._is_error(result)
        finally:
            locked.chmod(0o644)  # restore so tmp cleanup can remove it

    # --- Path edge cases ---------------------------------------------------

    def test_relative_path(self):
        """A relative path (resolved against cwd) converts successfully."""
        relative = os.path.relpath(self.PDF_FIXTURE, os.getcwd())
        result = document_path_to_markdown(relative)
        assert not self._is_error(result)
        assert self._looks_like_markdown(result)

    def test_path_with_spaces(self, tmp_path):
        """A path containing spaces in the filename converts successfully."""
        spaced = tmp_path / "my report copy.pdf"
        shutil.copy(self.PDF_FIXTURE, spaced)
        result = document_path_to_markdown(spaced)
        assert not self._is_error(result)
        assert self._looks_like_markdown(result)
