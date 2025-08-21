"""
Unit tests for ConceptMapper processor
"""
import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from processors.concept_mapper import ConceptMapper


class TestConceptMapper(unittest.TestCase):
    """Test cases for ConceptMapper class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.concept_mapper = ConceptMapper(str(self.test_dir))
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test ConceptMapper initialization"""
        self.assertIsInstance(self.concept_mapper, ConceptMapper)
        self.assertEqual(self.concept_mapper.output_dir, self.test_dir)
        self.assertTrue(self.concept_mapper.concepts_dir.exists())
        
        # Check predefined categories exist
        self.assertIn('api', self.concept_mapper.concept_categories)
        self.assertIn('security', self.concept_mapper.concept_categories)
        self.assertIn('http', self.concept_mapper.concept_categories)
    
    def test_extract_technical_terms(self):
        """Test technical term extraction"""
        content = """
        This document describes the REST API endpoints for user authentication.
        The API uses OAuth 2.0 for security and returns JSON responses.
        Each endpoint requires an API key for authorization.
        The database stores user credentials securely using encryption.
        """
        
        terms = self.concept_mapper.extract_technical_terms(content)
        
        # Should extract key technical terms
        term_list = [term.lower() for term in terms]
        self.assertIn('api', term_list)
        self.assertIn('oauth', term_list)
        self.assertIn('json', term_list)
        self.assertIn('authentication', term_list)
        self.assertIn('database', term_list)
        self.assertIn('encryption', term_list)
    
    def test_categorize_term(self):
        """Test term categorization"""
        # API terms
        self.assertEqual(self.concept_mapper.categorize_term('api'), 'api')
        self.assertEqual(self.concept_mapper.categorize_term('endpoint'), 'api')
        self.assertEqual(self.concept_mapper.categorize_term('rest'), 'api')
        
        # Security terms
        self.assertEqual(self.concept_mapper.categorize_term('oauth'), 'security')
        self.assertEqual(self.concept_mapper.categorize_term('authentication'), 'security')
        self.assertEqual(self.concept_mapper.categorize_term('encryption'), 'security')
        
        # HTTP terms
        self.assertEqual(self.concept_mapper.categorize_term('http'), 'http')
        self.assertEqual(self.concept_mapper.categorize_term('https'), 'http')
        self.assertEqual(self.concept_mapper.categorize_term('post'), 'http')
        
        # Database terms
        self.assertEqual(self.concept_mapper.categorize_term('database'), 'database')
        self.assertEqual(self.concept_mapper.categorize_term('sql'), 'database')
        self.assertEqual(self.concept_mapper.categorize_term('query'), 'database')
        
        # Framework terms
        self.assertEqual(self.concept_mapper.categorize_term('framework'), 'framework')
        self.assertEqual(self.concept_mapper.categorize_term('library'), 'framework')
        
        # Unknown terms
        self.assertEqual(self.concept_mapper.categorize_term('randomword'), 'general')
    
    def test_extract_definitions_from_context(self):
        """Test definition extraction from context"""
        content = """
        OAuth 2.0 is an authorization framework that enables applications 
        to obtain limited access to user accounts.
        
        An API key is a unique identifier used to authenticate a user, 
        developer, or calling program to an API.
        
        JSON (JavaScript Object Notation) is a lightweight data-interchange format.
        """
        
        # Test OAuth definition
        oauth_def = self.concept_mapper.extract_definitions_from_context('oauth', content)
        self.assertIn('authorization framework', oauth_def.lower())
        
        # Test API key definition
        api_key_def = self.concept_mapper.extract_definitions_from_context('api key', content)
        self.assertIn('unique identifier', api_key_def.lower())
        
        # Test JSON definition
        json_def = self.concept_mapper.extract_definitions_from_context('json', content)
        self.assertIn('data-interchange format', json_def.lower())
        
        # Test non-existent term
        missing_def = self.concept_mapper.extract_definitions_from_context('nonexistent', content)
        self.assertEqual(missing_def, '')
    
    def test_analyze_term_usage(self):
        """Test term usage analysis"""
        sections = [
            {
                'title': 'Authentication',
                'content': 'The API uses OAuth for authentication. OAuth is secure.'
            },
            {
                'title': 'Endpoints',
                'content': 'API endpoints return JSON. The API is RESTful.'
            },
            {
                'title': 'Security',
                'content': 'OAuth provides security. Use HTTPS for secure connections.'
            }
        ]
        
        usage = self.concept_mapper.analyze_term_usage('oauth', sections)
        
        self.assertEqual(usage['frequency'], 3)  # Appears 3 times
        self.assertEqual(len(usage['sections']), 2)  # In 2 sections
        self.assertIn('Authentication', [s['title'] for s in usage['sections']])
        self.assertIn('Security', [s['title'] for s in usage['sections']])
        
        # Test case insensitive
        usage_api = self.concept_mapper.analyze_term_usage('api', sections)
        self.assertGreater(usage_api['frequency'], 0)
    
    def test_build_concept_relationships(self):
        """Test concept relationship building"""
        concepts = {
            'oauth': {
                'category': 'security',
                'definition': 'Authorization framework',
                'frequency': 5
            },
            'api': {
                'category': 'api',
                'definition': 'Application Programming Interface',
                'frequency': 10
            },
            'authentication': {
                'category': 'security',
                'definition': 'Process of verifying identity',
                'frequency': 3
            }
        }
        
        relationships = self.concept_mapper.build_concept_relationships(concepts)
        
        # Should find relationships between security terms
        oauth_rels = relationships.get('oauth', [])
        auth_found = any(rel['term'] == 'authentication' for rel in oauth_rels)
        self.assertTrue(auth_found)
        
        # Check relationship strength
        for term, rels in relationships.items():
            for rel in rels:
                self.assertIn('strength', rel)
                self.assertGreater(rel['strength'], 0)
                self.assertLessEqual(rel['strength'], 1)
    
    def test_generate_glossary_content(self):
        """Test glossary content generation"""
        concepts = {
            'api': {
                'category': 'api',
                'definition': 'Application Programming Interface',
                'frequency': 10,
                'sections': ['Introduction', 'Reference']
            },
            'oauth': {
                'category': 'security',
                'definition': 'Open Authorization framework',
                'frequency': 5,
                'sections': ['Security']
            }
        }
        
        glossary = self.concept_mapper.generate_glossary_content(concepts)
        
        # Check structure
        self.assertIn('# Concept Glossary', glossary)
        self.assertIn('## Summary', glossary)
        self.assertIn('Total Terms: 2', glossary)
        
        # Check categories
        self.assertIn('## API (1 terms)', glossary)
        self.assertIn('## Security (1 terms)', glossary)
        
        # Check individual terms
        self.assertIn('### API', glossary)
        self.assertIn('Application Programming Interface', glossary)
        self.assertIn('### OAuth', glossary)
        self.assertIn('Open Authorization framework', glossary)
        
        # Check metadata
        self.assertIn('Frequency: 10', glossary)
        self.assertIn('Frequency: 5', glossary)
    
    def test_create_concept_files(self):
        """Test concept file creation"""
        concepts = {
            'api': {
                'category': 'api',
                'definition': 'Application Programming Interface',
                'frequency': 10
            }
        }
        
        relationships = {
            'api': [
                {'term': 'endpoint', 'strength': 0.8, 'reason': 'same_category'}
            ]
        }
        
        files = self.concept_mapper.create_concept_files(concepts, relationships)
        
        self.assertGreater(len(files), 0)
        
        # Check files were created
        for file_path in files:
            file_obj = Path(file_path)
            self.assertTrue(file_obj.exists())
            
            content = file_obj.read_text()
            self.assertGreater(len(content), 0)
        
        # Should include glossary file
        glossary_files = [f for f in files if 'glossary' in f]
        self.assertGreater(len(glossary_files), 0)
    
    def test_extract_and_map_concepts_integration(self):
        """Test end-to-end concept extraction and mapping"""
        sections = [
            {
                'title': 'API Overview',
                'content': '''
                This REST API provides endpoints for user management.
                All endpoints use JSON for data exchange and require authentication.
                The API supports OAuth 2.0 for secure access.
                '''
            },
            {
                'title': 'Authentication',
                'content': '''
                OAuth 2.0 is an authorization framework that enables applications
                to obtain limited access to user accounts. The API uses Bearer tokens
                for authentication. HTTPS is required for all requests.
                '''
            },
            {
                'title': 'Database Schema',
                'content': '''
                The database stores user information in PostgreSQL.
                All queries are performed using SQL with proper indexing.
                The schema includes tables for users and permissions.
                '''
            }
        ]
        
        results = self.concept_mapper.extract_and_map_concepts(sections)
        
        # Check structure
        self.assertIn('terms', results)
        self.assertIn('relationships', results)
        self.assertIn('categories', results)
        self.assertIn('concept_files', results)
        self.assertIn('stats', results)
        
        # Check terms were extracted
        terms = results['terms']
        self.assertGreater(len(terms), 0)
        
        # Check for expected terms
        term_names = [name.lower() for name in terms.keys()]
        self.assertIn('api', term_names)
        self.assertIn('oauth', term_names)
        self.assertIn('json', term_names)
        
        # Check term structure
        for term_name, term_data in terms.items():
            self.assertIn('category', term_data)
            self.assertIn('frequency', term_data)
            self.assertIn('sections', term_data)
        
        # Check categories
        categories = results['categories']
        self.assertGreater(len(categories), 0)
        
        # Check files were created
        concept_files = results['concept_files']
        self.assertGreater(len(concept_files), 0)
        
        # Check stats
        stats = results['stats']
        self.assertIn('total_terms', stats)
        self.assertIn('total_categories', stats)
        self.assertIn('total_relationships', stats)
        self.assertGreater(stats['total_terms'], 0)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Empty sections
        empty_results = self.concept_mapper.extract_and_map_concepts([])
        self.assertEqual(empty_results['terms'], {})
        self.assertEqual(empty_results['relationships'], {})
        
        # Sections with no technical content
        non_technical = [
            {
                'title': 'Introduction',
                'content': 'This is a simple introduction with no technical terms.'
            }
        ]
        
        results = self.concept_mapper.extract_and_map_concepts(non_technical)
        # Should handle gracefully, might have minimal terms
        self.assertIsInstance(results['terms'], dict)
        
        # Section with only punctuation
        punctuation_only = [
            {
                'title': 'Special',
                'content': '!@#$%^&*(){}[]|;:,.<>?'
            }
        ]
        
        results = self.concept_mapper.extract_and_map_concepts(punctuation_only)
        self.assertIsInstance(results['terms'], dict)
    
    def test_frequency_counting(self):
        """Test accurate frequency counting"""
        sections = [
            {
                'title': 'Section 1',
                'content': 'The API uses JSON. API endpoints return JSON data.'
            },
            {
                'title': 'Section 2', 
                'content': 'JSON is lightweight. The API supports JSON and XML.'
            }
        ]
        
        results = self.concept_mapper.extract_and_map_concepts(sections)
        terms = results['terms']
        
        # API should appear 3 times
        if 'api' in terms:
            self.assertEqual(terms['api']['frequency'], 3)
        
        # JSON should appear 4 times  
        if 'json' in terms:
            self.assertEqual(terms['json']['frequency'], 4)


if __name__ == '__main__':
    unittest.main()