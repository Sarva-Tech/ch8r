import pytest
from unittest.mock import Mock, patch, mock_open
import os

from core.services.file_extractors import (
    extract_text_from_file,
    extract_pdf,
    extract_docx,
    extract_txt
)


@pytest.mark.unit
class TestExtractTextFromFile:
    @patch('core.services.file_extractors.default_storage')
    @patch('core.services.file_extractors.extract_pdf')
    def test_extract_text_from_file_pdf(self, mock_extract_pdf, mock_storage):
        mock_storage.path.return_value = '/path/to/file.pdf'
        mock_extract_pdf.return_value = 'pdf content'
        
        result = extract_text_from_file('file.pdf')
        
        mock_extract_pdf.assert_called_once_with('/path/to/file.pdf')
        assert result == 'pdf content'

    @patch('core.services.file_extractors.default_storage')
    @patch('core.services.file_extractors.extract_docx')
    def test_extract_text_from_file_docx(self, mock_extract_docx, mock_storage):
        mock_storage.path.return_value = '/path/to/file.docx'
        mock_extract_docx.return_value = 'docx content'
        
        result = extract_text_from_file('file.docx')
        
        mock_extract_docx.assert_called_once_with('/path/to/file.docx')
        assert result == 'docx content'

    @patch('core.services.file_extractors.default_storage')
    @patch('core.services.file_extractors.extract_txt')
    def test_extract_text_from_file_txt(self, mock_extract_txt, mock_storage):
        mock_storage.path.return_value = '/path/to/file.txt'
        mock_extract_txt.return_value = 'txt content'
        
        result = extract_text_from_file('file.txt')
        
        mock_extract_txt.assert_called_once_with('/path/to/file.txt')
        assert result == 'txt content'

    @patch('core.services.file_extractors.default_storage')
    @patch('core.services.file_extractors.extract_txt')
    def test_extract_text_from_file_md(self, mock_extract_txt, mock_storage):
        mock_storage.path.return_value = '/path/to/file.md'
        mock_extract_txt.return_value = 'md content'
        
        result = extract_text_from_file('file.md')
        
        mock_extract_txt.assert_called_once_with('/path/to/file.md')
        assert result == 'md content'

    @patch('core.services.file_extractors.default_storage')
    def test_extract_text_from_file_unsupported_type(self, mock_storage):
        mock_storage.path.return_value = '/path/to/file.xyz'
        
        with pytest.raises(ValueError, match="Unsupported file type: .xyz"):
            extract_text_from_file('file.xyz')

    @patch('core.services.file_extractors.default_storage')
    @patch('core.services.file_extractors.extract_pdf')
    def test_extract_text_from_file_uppercase_extension(self, mock_extract_pdf, mock_storage):
        mock_storage.path.return_value = '/path/to/file.PDF'
        mock_extract_pdf.return_value = 'pdf content'
        
        result = extract_text_from_file('file.PDF')
        
        mock_extract_pdf.assert_called_once_with('/path/to/file.PDF')
        assert result == 'pdf content'


@pytest.mark.unit
class TestExtractPdf:
    @patch('core.services.file_extractors.PdfReader')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_pdf_success(self, mock_quality_filter, mock_pdf_reader):
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = 'Page 1 content'
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = 'Page 2 content'
        
        mock_pdf_reader.return_value.pages = [mock_page1, mock_page2]
        mock_quality_filter.remove_emojis.return_value = 'Page 1 content\nPage 2 content'
        
        result = extract_pdf('/path/to/file.pdf')
        
        assert result == 'Page 1 content\nPage 2 content'
        mock_quality_filter.remove_emojis.assert_called_once()

    @patch('core.services.file_extractors.PdfReader')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_pdf_empty_page(self, mock_quality_filter, mock_pdf_reader):
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        
        mock_pdf_reader.return_value.pages = [mock_page]
        mock_quality_filter.remove_emojis.return_value = ''
        
        result = extract_pdf('/path/to/file.pdf')
        
        assert result == ''

    @patch('core.services.file_extractors.PdfReader')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_pdf_single_page(self, mock_quality_filter, mock_pdf_reader):
        mock_page = Mock()
        mock_page.extract_text.return_value = 'Single page content'
        
        mock_pdf_reader.return_value.pages = [mock_page]
        mock_quality_filter.remove_emojis.return_value = 'Single page content'
        
        result = extract_pdf('/path/to/file.pdf')
        
        assert result == 'Single page content'

    @patch('core.services.file_extractors.PdfReader')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_pdf_with_emojis(self, mock_quality_filter, mock_pdf_reader):
        mock_page = Mock()
        mock_page.extract_text.return_value = 'Content with 👍 emoji'
        
        mock_pdf_reader.return_value.pages = [mock_page]
        mock_quality_filter.remove_emojis.return_value = 'Content with emoji'
        
        result = extract_pdf('/path/to/file.pdf')
        
        assert result == 'Content with emoji'
        mock_quality_filter.remove_emojis.assert_called_once_with('Content with 👍 emoji')


@pytest.mark.unit
class TestExtractDocx:
    @patch('core.services.file_extractors.Document')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_docx_success(self, mock_quality_filter, mock_document):
        mock_para1 = Mock()
        mock_para1.text = 'Paragraph 1'
        mock_para2 = Mock()
        mock_para2.text = 'Paragraph 2'
        
        mock_document.return_value.paragraphs = [mock_para1, mock_para2]
        mock_quality_filter.remove_emojis.return_value = 'Paragraph 1\nParagraph 2'
        
        result = extract_docx('/path/to/file.docx')
        
        assert result == 'Paragraph 1\nParagraph 2'
        mock_document.assert_called_once_with('/path/to/file.docx')

    @patch('core.services.file_extractors.Document')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_docx_empty_document(self, mock_quality_filter, mock_document):
        mock_document.return_value.paragraphs = []
        mock_quality_filter.remove_emojis.return_value = ''
        
        result = extract_docx('/path/to/file.docx')
        
        assert result == ''

    @patch('core.services.file_extractors.Document')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_docx_single_paragraph(self, mock_quality_filter, mock_document):
        mock_para = Mock()
        mock_para.text = 'Single paragraph'
        
        mock_document.return_value.paragraphs = [mock_para]
        mock_quality_filter.remove_emojis.return_value = 'Single paragraph'
        
        result = extract_docx('/path/to/file.docx')
        
        assert result == 'Single paragraph'

    @patch('core.services.file_extractors.Document')
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_docx_with_emojis(self, mock_quality_filter, mock_document):
        mock_para = Mock()
        mock_para.text = 'Text with 🎉 emoji'
        
        mock_document.return_value.paragraphs = [mock_para]
        mock_quality_filter.remove_emojis.return_value = 'Text with emoji'
        
        result = extract_docx('/path/to/file.docx')
        
        assert result == 'Text with emoji'
        mock_quality_filter.remove_emojis.assert_called_once_with('Text with 🎉 emoji')


@pytest.mark.unit
class TestExtractTxt:
    @patch('core.services.file_extractors._quality_filter')
    def test_extract_txt_success(self, mock_quality_filter):
        with patch('builtins.open', mock_open(read_data='File content')):
            mock_quality_filter.remove_emojis.return_value = 'File content'
            
            result = extract_txt('/path/to/file.txt')
            
            assert result == 'File content'
            mock_quality_filter.remove_emojis.assert_called_once_with('File content')

    @patch('core.services.file_extractors._quality_filter')
    def test_extract_txt_empty_file(self, mock_quality_filter):
        with patch('builtins.open', mock_open(read_data='')):
            mock_quality_filter.remove_emojis.return_value = ''
            
            result = extract_txt('/path/to/file.txt')
            
            assert result == ''

    @patch('core.services.file_extractors._quality_filter')
    def test_extract_txt_multiline(self, mock_quality_filter):
        content = 'Line 1\nLine 2\nLine 3'
        with patch('builtins.open', mock_open(read_data=content)):
            mock_quality_filter.remove_emojis.return_value = content
            
            result = extract_txt('/path/to/file.txt')
            
            assert result == content

    @patch('core.services.file_extractors._quality_filter')
    def test_extract_txt_with_emojis(self, mock_quality_filter):
        content = 'Text with 😊 emoji'
        with patch('builtins.open', mock_open(read_data=content)):
            mock_quality_filter.remove_emojis.return_value = 'Text with emoji'
            
            result = extract_txt('/path/to/file.txt')
            
            assert result == 'Text with emoji'
            mock_quality_filter.remove_emojis.assert_called_once_with('Text with 😊 emoji')

    @patch('core.services.file_extractors._quality_filter')
    def test_extract_txt_utf8_encoding(self, mock_quality_filter):
        content = 'Unicode content: 你好世界'
        with patch('builtins.open', mock_open(read_data=content)):
            mock_quality_filter.remove_emojis.return_value = content
            
            result = extract_txt('/path/to/file.txt')
            
            assert result == content
