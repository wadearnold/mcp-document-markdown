"""
Concept mapping and glossary generation
"""
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
import re
from collections import Counter, defaultdict

from ..utils.text_utils import TextUtils
from ..utils.file_utils import FileUtils
from ..utils.token_counter import TokenCounter

class ConceptMapper:
    """Handles concept map and glossary generation with relationship analysis"""
    
    def __init__(self, output_dir: str, token_counter: TokenCounter):
        """
        Initialize concept mapper
        
        Args:
            output_dir: Output directory for concept maps and glossaries
            token_counter: Token counter for optimization
        """
        self.output_dir = Path(output_dir)
        self.token_counter = token_counter
        self.concepts_dir = self.output_dir / "concepts"
        FileUtils.ensure_directory(self.concepts_dir)
        
        # Categories for concept classification
        self.concept_categories = {
            'api_concepts': ['endpoint', 'method', 'parameter', 'response', 'request', 'header', 'authentication'],
            'http_concepts': ['get', 'post', 'put', 'delete', 'patch', 'status', 'code', 'protocol'],
            'security_concepts': ['authentication', 'authorization', 'token', 'key', 'certificate', 'oauth', 'jwt'],
            'database_concepts': ['query', 'table', 'index', 'schema', 'migration', 'transaction', 'sql'],
            'programming_concepts': ['function', 'class', 'method', 'variable', 'array', 'object', 'loop'],
            'network_concepts': ['url', 'domain', 'port', 'protocol', 'tcp', 'udp', 'ip', 'dns'],
            'architecture_concepts': ['service', 'microservice', 'container', 'deployment', 'scaling', 'load'],
            'business_concepts': ['user', 'customer', 'product', 'order', 'payment', 'subscription'],
            'data_concepts': ['json', 'xml', 'csv', 'format', 'encoding', 'parsing', 'validation'],
            'process_concepts': ['workflow', 'pipeline', 'automation', 'integration', 'synchronization']
        }
    
    def generate_concept_map_and_glossary(self, sections: List[Dict[str, Any]]) -> List[str]:
        """
        Generate comprehensive concept map and glossary
        
        Args:
            sections: List of document sections
            
        Returns:
            List of paths to created files
        """
        if not sections:
            return []
        
        # Extract comprehensive term information
        terms_data = self.extract_comprehensive_terms(sections)
        
        # Extract concept definitions
        concepts_data = self.extract_concept_definitions(sections)
        
        # Build concept relationships
        relationships = self.build_concept_relationships(terms_data, concepts_data, sections)
        
        # Generate all output files
        created_files = []
        
        # Human-readable glossary
        glossary_file = self.create_human_glossary(terms_data, concepts_data)
        created_files.append(str(glossary_file))
        
        # Concept map documentation
        concept_map_file = self.create_concept_map_documentation(relationships, terms_data)
        created_files.append(str(concept_map_file))
        
        # Machine-readable formats
        json_files = self.create_machine_readable_formats(terms_data, concepts_data, relationships)
        created_files.extend(str(f) for f in json_files)
        
        # Category-specific glossaries
        category_files = self.create_category_glossaries(terms_data)
        created_files.extend(str(f) for f in category_files)
        
        return created_files
    
    def extract_comprehensive_terms(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract comprehensive term information with frequency and context"""
        term_data = defaultdict(lambda: {
            'frequency': 0,
            'contexts': [],
            'sections': set(),
            'category': 'general',
            'importance_score': 0,
            'definitions': []
        })
        
        for section_idx, section in enumerate(sections):
            content = section.get('content', '')
            section_title = section.get('title', f'Section {section_idx + 1}')
            section_type = section.get('section_type', 'content')
            
            # Extract technical terms using multiple approaches
            terms = self.extract_terms_from_content(content)
            
            for term in terms:
                term_lower = term.lower()
                term_data[term_lower]['frequency'] += 1
                term_data[term_lower]['sections'].add(section_title)
                
                # Categorize term
                category = self.categorize_term(term_lower)
                if category != 'general':
                    term_data[term_lower]['category'] = category
                
                # Extract context around term
                context = self.extract_term_context(content, term)
                if context and context not in term_data[term_lower]['contexts']:
                    term_data[term_lower]['contexts'].append(context)
                
                # Look for definitions
                definition = self.extract_term_definition(content, term)
                if definition and definition not in term_data[term_lower]['definitions']:
                    term_data[term_lower]['definitions'].append(definition)
        
        # Calculate importance scores
        for term, data in term_data.items():
            data['sections'] = list(data['sections'])
            data['importance_score'] = self.calculate_importance_score(data)
        
        # Filter out low-importance terms
        filtered_terms = {
            term: data for term, data in term_data.items()
            if data['importance_score'] > 2 or data['frequency'] > 1
        }
        
        return dict(filtered_terms)
    
    def extract_terms_from_content(self, content: str) -> List[str]:
        """Extract technical terms from content using multiple patterns"""
        terms = set()
        
        # Capitalized terms (likely proper nouns/technical terms)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        terms.update(term for term in capitalized if len(term) > 2)
        
        # Acronyms (2+ capital letters)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', content)
        terms.update(acronyms)
        
        # Technical patterns
        tech_patterns = [
            r'\b\w+(?:API|api)\b',           # API-related terms
            r'\b\w*(?:HTTP|http)\w*\b',      # HTTP-related terms
            r'\b\w*(?:JSON|json|XML|xml)\w*\b',  # Data format terms
            r'\b\w+(?:Service|service)\b',    # Service terms
            r'\b\w+(?:Token|token)\b',        # Token-related terms
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content)
            terms.update(matches)
        
        # Code-like terms (camelCase, snake_case)
        code_terms = re.findall(r'\b[a-z]+[A-Z]\w*\b|\b\w+_\w+\b', content)
        terms.update(term for term in code_terms if len(term) > 3)
        
        return list(terms)
    
    def categorize_term(self, term: str) -> str:
        """Categorize a term based on predefined categories"""
        term_lower = term.lower()
        
        for category, keywords in self.concept_categories.items():
            if any(keyword in term_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def extract_term_context(self, content: str, term: str, context_size: int = 50) -> str:
        """Extract context around a term"""
        # Find term in content (case-insensitive)
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        match = pattern.search(content)
        
        if match:
            start = max(0, match.start() - context_size)
            end = min(len(content), match.end() + context_size)
            context = content[start:end].strip()
            
            # Clean up context
            context = re.sub(r'\s+', ' ', context)
            return context
        
        return ""
    
    def extract_term_definition(self, content: str, term: str) -> str:
        """Look for definitions of terms in content"""
        # Common definition patterns
        patterns = [
            rf'{re.escape(term)}\s+is\s+(.+?)\.', 
            rf'{re.escape(term)}\s*:\s*(.+?)\.', 
            rf'{re.escape(term)}\s*-\s*(.+?)\.', 
            rf'{re.escape(term)}\s+refers to\s+(.+?)\.',
            rf'{re.escape(term)}\s+means\s+(.+?)\.'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Return the first definition found
                definition = matches[0].strip()
                if len(definition) > 10 and len(definition) < 200:
                    return definition
        
        return ""
    
    def calculate_importance_score(self, term_data: Dict[str, Any]) -> float:
        """Calculate importance score for a term"""
        score = 0
        
        # Frequency contribution
        score += min(term_data['frequency'] * 0.5, 5)
        
        # Section spread contribution
        score += min(len(term_data['sections']) * 1.0, 5)
        
        # Category contribution
        if term_data['category'] in ['api_concepts', 'security_concepts', 'http_concepts']:
            score += 3
        elif term_data['category'] != 'general':
            score += 1
        
        # Definition contribution
        if term_data['definitions']:
            score += 2
        
        # Context quality contribution
        if len(term_data['contexts']) > 1:
            score += 1
        
        return score
    
    def extract_concept_definitions(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract concept definitions and explanations"""
        concepts = {}
        
        for section_idx, section in enumerate(sections):
            content = section.get('content', '')
            section_title = section.get('title', f'Section {section_idx + 1}')
            
            # Look for definition patterns
            definition_patterns = [
                r'## ([^#\n]+)\n\n([^#]+?)(?=\n##|\n#|\Z)',  # Headers with content
                r'\*\*([^*]+)\*\*[:\s]*([^.\n]+\.)',        # Bold terms with definitions
                r'`([^`]+)`[:\s]*([^.\n]+\.)',              # Code terms with definitions
            ]
            
            for pattern in definition_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    concept_name = match[0].strip()
                    definition = match[1].strip()
                    
                    if len(concept_name) < 50 and len(definition) > 10:
                        concepts[concept_name.lower()] = {
                            'name': concept_name,
                            'definition': definition[:500],  # Limit definition length
                            'source_section': section_title,
                            'category': self.categorize_term(concept_name.lower())
                        }
        
        return concepts
    
    def build_concept_relationships(self, terms_data: Dict, concepts_data: Dict, 
                                  sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build relationships between concepts"""
        relationships = {
            'term_cooccurrence': defaultdict(lambda: defaultdict(int)),
            'category_relationships': defaultdict(set),
            'definition_links': defaultdict(set),
            'section_clustering': defaultdict(set)
        }
        
        # Build co-occurrence matrix
        for section in sections:
            content = section.get('content', '').lower()
            section_terms = [term for term in terms_data.keys() if term in content]
            
            # Record co-occurrences
            for i, term1 in enumerate(section_terms):
                for term2 in section_terms[i+1:]:
                    relationships['term_cooccurrence'][term1][term2] += 1
                    relationships['term_cooccurrence'][term2][term1] += 1
        
        # Build category relationships
        for term, data in terms_data.items():
            category = data['category']
            relationships['category_relationships'][category].add(term)
        
        # Build definition links
        for concept_name, concept_data in concepts_data.items():
            definition = concept_data['definition'].lower()
            for term in terms_data.keys():
                if term != concept_name and term in definition:
                    relationships['definition_links'][concept_name].add(term)
        
        # Build section clustering
        for term, data in terms_data.items():
            for section in data['sections']:
                relationships['section_clustering'][section].add(term)
        
        return dict(relationships)
    
    def create_human_glossary(self, terms_data: Dict, concepts_data: Dict) -> Path:
        """Create human-readable glossary"""
        # Sort terms by importance score
        sorted_terms = sorted(
            terms_data.items(),
            key=lambda x: x[1]['importance_score'],
            reverse=True
        )
        
        glossary_content = f"""# Technical Glossary

**Generated**: {datetime.now().isoformat()}  
**Total Terms**: {len(terms_data)}  
**Categories**: {len(set(data['category'] for data in terms_data.values()))}  

## High-Importance Terms

"""
        
        # Add high-importance terms
        high_importance = [(term, data) for term, data in sorted_terms if data['importance_score'] >= 5]
        
        for term, data in high_importance[:20]:  # Top 20 high-importance terms
            glossary_content += f"### {term.title()}\n"
            glossary_content += f"**Category**: {data['category'].replace('_', ' ').title()}  \n"
            glossary_content += f"**Frequency**: {data['frequency']} occurrences  \n"
            glossary_content += f"**Sections**: {', '.join(data['sections'])}  \n"
            
            if data['definitions']:
                glossary_content += f"**Definition**: {data['definitions'][0]}  \n"
            
            if data['contexts']:
                best_context = min(data['contexts'], key=len)  # Shortest context
                glossary_content += f"**Context**: ...{best_context}...  \n"
            
            glossary_content += "\n"
        
        # Add terms by category
        categories = defaultdict(list)
        for term, data in terms_data.items():
            categories[data['category']].append((term, data))
        
        for category, category_terms in categories.items():
            if category == 'general':
                continue
                
            category_terms.sort(key=lambda x: x[1]['frequency'], reverse=True)
            
            glossary_content += f"## {category.replace('_', ' ').title()} Terms\n\n"
            
            for term, data in category_terms[:10]:  # Top 10 per category
                glossary_content += f"- **{term.title()}** ({data['frequency']}x)"
                if data['definitions']:
                    glossary_content += f": {data['definitions'][0][:100]}..."
                glossary_content += "\n"
            
            glossary_content += "\n"
        
        glossary_file = self.concepts_dir / "glossary.md"
        FileUtils.write_markdown(glossary_content, glossary_file)
        return glossary_file
    
    def create_concept_map_documentation(self, relationships: Dict, terms_data: Dict) -> Path:
        """Create concept map documentation"""
        content = f"""# Concept Map Analysis

**Generated**: {datetime.now().isoformat()}  
**Total Terms**: {len(terms_data)}  
**Relationships Analyzed**: {sum(len(cooc) for cooc in relationships['term_cooccurrence'].values())}  

## Network Analysis

### Most Connected Terms
"""
        
        # Find most connected terms
        connection_counts = {}
        for term, connections in relationships['term_cooccurrence'].items():
            connection_counts[term] = len(connections)
        
        top_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for term, count in top_connected:
            content += f"- **{term.title()}**: {count} connections\n"
        
        content += "\n## Category Clusters\n\n"
        
        # Show category relationships
        for category, terms in relationships['category_relationships'].items():
            if len(terms) > 1:
                content += f"### {category.replace('_', ' ').title()}\n"
                content += f"**Terms**: {len(terms)}  \n"
                content += f"**Key Terms**: {', '.join(list(terms)[:5])}  \n"
                content += "\n"
        
        content += "## Strong Relationships\n\n"
        
        # Show strongest co-occurrences
        all_relationships = []
        for term1, connections in relationships['term_cooccurrence'].items():
            for term2, strength in connections.items():
                if strength > 2:  # Only strong relationships
                    all_relationships.append((term1, term2, strength))
        
        all_relationships.sort(key=lambda x: x[2], reverse=True)
        
        for term1, term2, strength in all_relationships[:15]:
            content += f"- **{term1.title()}** ↔ **{term2.title()}** (co-occurs {strength} times)\n"
        
        concept_map_file = self.concepts_dir / "concept-map.md"
        FileUtils.write_markdown(content, concept_map_file)
        return concept_map_file
    
    def create_machine_readable_formats(self, terms_data: Dict, concepts_data: Dict, 
                                      relationships: Dict) -> List[Path]:
        """Create machine-readable JSON formats"""
        files_created = []
        
        # Structured glossary JSON
        glossary_json = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_terms': len(terms_data),
                'total_concepts': len(concepts_data)
            },
            'terms': terms_data,
            'concepts': concepts_data
        }
        
        glossary_file = self.concepts_dir / "glossary.json"
        FileUtils.write_json(glossary_json, glossary_file)
        files_created.append(glossary_file)
        
        # Concept map JSON (for visualization)
        concept_map_json = {
            'nodes': [],
            'edges': [],
            'categories': list(set(data['category'] for data in terms_data.values()))
        }
        
        # Create nodes
        node_id = 0
        term_to_id = {}
        for term, data in terms_data.items():
            concept_map_json['nodes'].append({
                'id': node_id,
                'label': term.title(),
                'category': data['category'],
                'importance': data['importance_score'],
                'frequency': data['frequency']
            })
            term_to_id[term] = node_id
            node_id += 1
        
        # Create edges
        for term1, connections in relationships['term_cooccurrence'].items():
            if term1 in term_to_id:
                for term2, weight in connections.items():
                    if term2 in term_to_id and weight > 1:
                        concept_map_json['edges'].append({
                            'source': term_to_id[term1],
                            'target': term_to_id[term2],
                            'weight': weight
                        })
        
        concept_map_file = self.concepts_dir / "concept-map.json"
        FileUtils.write_json(concept_map_json, concept_map_file)
        files_created.append(concept_map_file)
        
        # Visualization data for graph tools
        viz_data = {
            'graph': {
                'nodes': concept_map_json['nodes'],
                'links': [
                    {'source': edge['source'], 'target': edge['target'], 'value': edge['weight']}
                    for edge in concept_map_json['edges']
                ]
            },
            'layout_suggestions': {
                'force_directed': True,
                'cluster_by_category': True,
                'node_size_by_importance': True
            }
        }
        
        viz_file = self.concepts_dir / "visualization-data.json"
        FileUtils.write_json(viz_data, viz_file)
        files_created.append(viz_file)
        
        return files_created
    
    def create_category_glossaries(self, terms_data: Dict) -> List[Path]:
        """Create category-specific glossaries"""
        categories_dir = self.concepts_dir / "categories"
        FileUtils.ensure_directory(categories_dir)
        
        files_created = []
        
        # Group terms by category
        categories = defaultdict(list)
        for term, data in terms_data.items():
            categories[data['category']].append((term, data))
        
        # Create category index
        index_items = []
        
        for category, category_terms in categories.items():
            if len(category_terms) < 3:  # Skip categories with too few terms
                continue
                
            category_terms.sort(key=lambda x: x[1]['importance_score'], reverse=True)
            
            # Create category-specific glossary
            category_content = f"""# {category.replace('_', ' ').title()} Glossary

**Generated**: {datetime.now().isoformat()}  
**Terms in Category**: {len(category_terms)}  

## Terms

"""
            
            for term, data in category_terms:
                category_content += f"### {term.title()}\n"
                category_content += f"**Frequency**: {data['frequency']}  \n"
                category_content += f"**Importance Score**: {data['importance_score']:.1f}  \n"
                
                if data['definitions']:
                    category_content += f"**Definition**: {data['definitions'][0]}  \n"
                
                if data['contexts']:
                    category_content += f"**Context**: {data['contexts'][0][:100]}...  \n"
                
                category_content += "\n"
            
            # Save category glossary
            safe_category = FileUtils.safe_filename(category)
            category_file = categories_dir / f"{safe_category}-glossary.md"
            FileUtils.write_markdown(category_content, category_file)
            files_created.append(category_file)
            
            # Add to index
            index_items.append({
                'name': f"{category.replace('_', ' ').title()} Glossary",
                'description': f"{len(category_terms)} terms related to {category.replace('_', ' ')}",
                'file': f"{safe_category}-glossary.md"
            })
        
        # Create category index
        if index_items:
            index_file = FileUtils.create_index_file(
                categories_dir, "Category-Specific Glossaries", index_items
            )
            files_created.append(index_file)
        
        return files_created