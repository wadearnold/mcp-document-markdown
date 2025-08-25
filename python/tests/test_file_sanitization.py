"""
Test file and folder name sanitization
"""
import unittest
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_utils import FileUtils

class TestFileSanitization(unittest.TestCase):
    """Test file and folder name sanitization functions"""
    
    def test_basic_pdf_name_sanitization(self):
        """Test basic PDF filename sanitization"""
        test_cases = [
            ("document.pdf", "document"),
            ("Document.PDF", "document"),
            ("My Document.pdf", "my_document"),
            ("my-document.pdf", "my-document"),
        ]
        
        for input_name, expected in test_cases:
            result = FileUtils.sanitize_folder_name(input_name)
            self.assertEqual(result, expected, f"Failed for input: {input_name}")
    
    def test_complex_pdf_name_sanitization(self):
        """Test complex PDF filename sanitization with special characters"""
        test_cases = [
            ("Visa_Token_Services_Issuer API_Specifications_REST_JSON_V37r25d03.pdf", 
             "visa_token_services_issuer_api_specifications_rest_json_v37r25d03"),
            ("AWS:Lambda*Guide|2024.pdf", "aws_lambda_guide_2024"),
            ("C:\\Users\\Documents\\file.pdf", "c_users_documents_file"),
            ("Price List $99.99 (Special).pdf", "price_list_99_99_special"),
            ("File/With/Slashes.pdf", "file_with_slashes"),
            ("File with   multiple    spaces.pdf", "file_with_multiple_spaces"),
            ("___Leading_underscores___.pdf", "leading_underscores"),
        ]
        
        for input_name, expected in test_cases:
            result = FileUtils.sanitize_folder_name(input_name)
            self.assertEqual(result, expected, f"Failed for input: {input_name}")
    
    def test_non_ascii_character_removal(self):
        """Test removal of non-ASCII characters"""
        test_cases = [
            ("Café_Menu_2024.pdf", "caf_menu_2024"),
            ("日本語ドキュメント.pdf", ""),  # Should default to "converted_pdf"
            ("Résumé_Template.pdf", "rsum_template"),
            ("Document™_©2024.pdf", "document_2024"),
        ]
        
        for input_name, expected in test_cases:
            result = FileUtils.sanitize_folder_name(input_name)
            if expected == "":
                self.assertEqual(result, "converted_pdf", f"Failed for input: {input_name}")
            else:
                self.assertEqual(result, expected, f"Failed for input: {input_name}")
    
    def test_length_limiting(self):
        """Test that very long filenames are truncated"""
        long_name = "a" * 250 + ".pdf"
        result = FileUtils.sanitize_folder_name(long_name)
        self.assertLessEqual(len(result), 200)
        self.assertTrue(result.startswith("a" * 190))  # Should preserve most of the name
    
    def test_empty_and_edge_cases(self):
        """Test edge cases and empty inputs"""
        test_cases = [
            (".pdf", "converted_pdf"),
            ("", "converted_pdf"),
            ("...", "converted_pdf"),
            ("___", "converted_pdf"),
            ("   .pdf", "converted_pdf"),
            (".hidden.pdf", "hidden"),
        ]
        
        for input_name, expected in test_cases:
            result = FileUtils.sanitize_folder_name(input_name)
            self.assertEqual(result, expected, f"Failed for input: '{input_name}'")
    
    def test_windows_reserved_names(self):
        """Test handling of Windows reserved names (for cross-platform compatibility)"""
        test_cases = [
            ("CON.pdf", "con"),
            ("PRN.pdf", "prn"),
            ("AUX.pdf", "aux"),
            ("NUL.pdf", "nul"),
            ("COM1.pdf", "com1"),
            ("LPT1.pdf", "lpt1"),
        ]
        
        for input_name, expected in test_cases:
            result = FileUtils.sanitize_folder_name(input_name)
            self.assertEqual(result, expected, f"Failed for input: {input_name}")
    
    def test_idempotency(self):
        """Test that sanitizing an already sanitized name doesn't change it"""
        names = [
            "my_document",
            "visa_token_api_v37",
            "aws_lambda_guide_2024",
        ]
        
        for name in names:
            first_pass = FileUtils.sanitize_folder_name(name)
            second_pass = FileUtils.sanitize_folder_name(first_pass)
            self.assertEqual(first_pass, second_pass, 
                           f"Sanitization not idempotent for: {name}")
    
    def test_real_world_examples(self):
        """Test with real-world PDF filenames"""
        test_cases = [
            ("2024-Q1-Financial Report (DRAFT).pdf", "2024-q1-financial_report_draft"),
            ("User's Guide v1.2.3 [FINAL].pdf", "users_guide_v1_2_3_final"),
            ("API Documentation - REST & GraphQL.pdf", "api_documentation_rest_graphql"),
            ("Invoice #12345 - January 2024.pdf", "invoice_12345_january_2024"),
            ("Meeting Notes 01/15/2024.pdf", "meeting_notes_01_15_2024"),
        ]
        
        for input_name, expected in test_cases:
            result = FileUtils.sanitize_folder_name(input_name)
            self.assertEqual(result, expected, f"Failed for input: {input_name}")

if __name__ == '__main__':
    unittest.main()