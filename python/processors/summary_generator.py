"""
Multi-level summary generation
"""
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from collections import Counter

from ..utils.token_counter import TokenCounter
from ..utils.text_utils import TextUtils
from ..utils.file_utils import FileUtils

class SummaryGenerator:
    """Handles generation of multi-level summaries for different use cases"""
    
    def __init__(self, output_dir: str, token_counter: TokenCounter):
        """
        Initialize summary generator
        
        Args:
            output_dir: Output directory for summary files
            token_counter: Token counter for optimization
        """
        self.output_dir = Path(output_dir)
        self.token_counter = token_counter
        self.summaries_dir = self.output_dir / "summaries"
        FileUtils.ensure_directory(self.summaries_dir)
        
        # Summary target lengths (in tokens)
        self.summary_lengths = {
            'executive': 500,    # High-level overview
            'detailed': 2000,    # Section-by-section breakdown
            'complete': 8000,    # Comprehensive summary
            'technical': 3000    # Technical focus
        }
    
    def generate_all_summaries(self, sections: List[Dict[str, Any]], 
                              concepts: Dict[str, Any],
                              tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate all types of summaries
        
        Args:
            sections: List of document sections
            concepts: Extracted concepts and terms
            tables: Extracted tables
            
        Returns:
            Summary generation results
        """
        if not sections:
            return {}
        
        # Analyze content for summary planning
        content_analysis = self.analyze_content_for_summaries(sections, concepts, tables)
        
        # Generate different summary types
        executive_summary = self.generate_executive_summary(sections, content_analysis)
        detailed_summary = self.generate_detailed_summary(sections, content_analysis)
        complete_summary = self.generate_complete_summary(sections, content_analysis)
        technical_summary = self.generate_technical_summary(sections, content_analysis, concepts)
        
        # Generate specialized summaries
        api_summary = self.generate_api_summary(sections, content_analysis)
        security_summary = self.generate_security_summary(sections, content_analysis)
        integration_summary = self.generate_integration_summary(sections, content_analysis)
        
        # Create summary files
        summary_files = self.create_summary_files({
            'executive': executive_summary,
            'detailed': detailed_summary,
            'complete': complete_summary,
            'technical': technical_summary,
            'api': api_summary,
            'security': security_summary,
            'integration': integration_summary
        })
        
        # Generate summary index
        index_file = self.create_summary_index(summary_files)
        
        return {
            'summaries': {
                'executive': executive_summary,
                'detailed': detailed_summary,
                'complete': complete_summary,
                'technical': technical_summary,
                'api': api_summary,
                'security': security_summary,
                'integration': integration_summary
            },
            'summary_files': summary_files,
            'index_file': str(index_file),
            'content_analysis': content_analysis,
            'stats': {
                'total_sections_analyzed': len(sections),
                'executive_tokens': self.token_counter.count_tokens(executive_summary['content']),
                'detailed_tokens': self.token_counter.count_tokens(detailed_summary['content']),
                'complete_tokens': self.token_counter.count_tokens(complete_summary['content'])
            }
        }
    
    def analyze_content_for_summaries(self, sections: List[Dict[str, Any]], 
                                    concepts: Dict[str, Any],
                                    tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content to plan summary generation"""
        analysis = {
            'document_type': self.classify_document_type(sections),
            'key_sections': self.identify_key_sections(sections),
            'priority_concepts': self.identify_priority_concepts(concepts),
            'important_tables': self.identify_important_tables(tables),
            'content_themes': self.extract_content_themes(sections),
            'technical_depth': self.assess_technical_depth(sections),
            'structure_type': self.identify_structure_type(sections)
        }
        
        return analysis
    
    def classify_document_type(self, sections: List[Dict[str, Any]]) -> str:
        """Classify the type of document for appropriate summarization"""
        content_indicators = defaultdict(int)
        
        for section in sections:
            content = section.get('content', '').lower()
            title = section.get('title', '').lower()
            
            # API documentation indicators
            if any(term in content + title for term in ['api', 'endpoint', 'request', 'response', 'authentication']):
                content_indicators['api_documentation'] += 1
            
            # Technical manual indicators
            if any(term in content + title for term in ['configuration', 'installation', 'setup', 'deployment']):
                content_indicators['technical_manual'] += 1
            
            # User guide indicators
            if any(term in content + title for term in ['how to', 'tutorial', 'guide', 'step', 'getting started']):
                content_indicators['user_guide'] += 1
            
            # Reference documentation indicators
            if any(term in content + title for term in ['reference', 'specification', 'schema', 'format']):
                content_indicators['reference'] += 1
            
            # Business document indicators
            if any(term in content + title for term in ['policy', 'procedure', 'process', 'requirements']):
                content_indicators['business_document'] += 1
        
        # Return the most common type
        if content_indicators:
            return max(content_indicators.items(), key=lambda x: x[1])[0]
        return 'general_document'
    
    def identify_key_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify the most important sections for summarization"""
        key_sections = []
        
        for i, section in enumerate(sections):
            title = section.get('title', '').lower()
            content = section.get('content', '')
            section_type = section.get('section_type', 'content')
            
            # Calculate importance score
            importance_score = 0
            
            # Title-based scoring
            if any(term in title for term in ['introduction', 'overview', 'summary', 'conclusion']):
                importance_score += 10
            if any(term in title for term in ['authentication', 'security', 'api', 'getting started']):
                importance_score += 8
            if any(term in title for term in ['example', 'tutorial', 'guide']):
                importance_score += 6
            
            # Section type scoring
            type_scores = {
                'introduction': 10,
                'summary': 10,
                'authentication': 9,
                'api_endpoint': 8,
                'examples': 7,
                'error_handling': 6,
                'reference': 4
            }
            importance_score += type_scores.get(section_type, 3)
            
            # Content length scoring (moderate length preferred)
            content_length = len(content)
            if 500 <= content_length <= 3000:
                importance_score += 3
            elif content_length > 100:
                importance_score += 1
            
            # Position scoring (early sections often more important)
            if i < len(sections) * 0.3:  # First 30% of sections
                importance_score += 2
            
            key_sections.append({
                'index': i,
                'section': section,
                'importance_score': importance_score
            })
        
        # Sort by importance and return top sections
        key_sections.sort(key=lambda x: x['importance_score'], reverse=True)
        return key_sections[:min(10, len(key_sections))]  # Top 10 or all if fewer
    
    def identify_priority_concepts(self, concepts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify the most important concepts for summary inclusion"""
        if not concepts or 'terms' not in concepts:
            return []
        
        priority_concepts = []
        terms = concepts['terms']
        
        for term, info in terms.items():
            priority_score = 0
            
            # Frequency scoring
            frequency = info.get('frequency', 0)
            priority_score += min(frequency * 2, 20)  # Cap at 20 points
            
            # Category scoring
            category_scores = {
                'api': 10,
                'security': 10,
                'authentication': 9,
                'http': 8,
                'database': 7,
                'framework': 6,
                'general': 3
            }
            category = info.get('category', 'general')
            priority_score += category_scores.get(category, 3)
            
            # Definition quality scoring
            definition = info.get('definition', '')
            if len(definition) > 50:
                priority_score += 5
            elif len(definition) > 20:
                priority_score += 2
            
            priority_concepts.append({
                'term': term,
                'info': info,
                'priority_score': priority_score
            })
        
        # Sort by priority and return top concepts
        priority_concepts.sort(key=lambda x: x['priority_score'], reverse=True)
        return priority_concepts[:15]  # Top 15 concepts
    
    def identify_important_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify tables that should be highlighted in summaries"""
        if not tables:
            return []
        
        important_tables = []
        
        for table in tables:
            importance_score = 0
            
            # Size scoring (moderate size preferred for summaries)
            rows = table.get('rows', 0)
            cols = table.get('cols', 0)
            
            if 3 <= rows <= 10 and 2 <= cols <= 6:
                importance_score += 8
            elif rows > 0 and cols > 0:
                importance_score += 3
            
            # Content analysis (look for key information)
            markdown = table.get('markdown', '')
            if any(term in markdown.lower() for term in ['parameter', 'endpoint', 'response', 'error', 'status']):
                importance_score += 6
            
            important_tables.append({
                'table': table,
                'importance_score': importance_score
            })
        
        # Sort by importance
        important_tables.sort(key=lambda x: x['importance_score'], reverse=True)
        return important_tables[:5]  # Top 5 tables
    
    def extract_content_themes(self, sections: List[Dict[str, Any]]) -> List[str]:
        """Extract main themes from document content"""
        theme_keywords = []
        
        for section in sections:
            content = section.get('content', '').lower()
            title = section.get('title', '').lower()
            
            # Extract key phrases and terms
            combined_text = content + ' ' + title
            
            # Common technical themes
            themes = {
                'API Integration': ['api', 'endpoint', 'integration', 'webhook'],
                'Authentication': ['authentication', 'oauth', 'token', 'login', 'auth'],
                'Data Management': ['database', 'data', 'storage', 'query', 'schema'],
                'Security': ['security', 'encryption', 'ssl', 'https', 'secure'],
                'Configuration': ['config', 'setup', 'installation', 'deployment'],
                'Error Handling': ['error', 'exception', 'troubleshooting', 'debug'],
                'Performance': ['performance', 'optimization', 'cache', 'speed'],
                'Development': ['development', 'coding', 'programming', 'framework']
            }
            
            for theme, keywords in themes.items():
                if any(keyword in combined_text for keyword in keywords):
                    theme_keywords.append(theme)
        
        # Return unique themes sorted by frequency
        theme_counts = Counter(theme_keywords)
        return [theme for theme, count in theme_counts.most_common(5)]
    
    def assess_technical_depth(self, sections: List[Dict[str, Any]]) -> str:
        """Assess the technical depth of the document"""
        technical_indicators = 0
        total_content = 0
        
        for section in sections:
            content = section.get('content', '')
            total_content += len(content)
            
            # Count technical indicators
            technical_terms = ['function', 'class', 'method', 'parameter', 'return', 'variable',
                             'object', 'array', 'string', 'integer', 'boolean', 'null',
                             'json', 'xml', 'http', 'api', 'endpoint', 'request', 'response']
            
            for term in technical_terms:
                technical_indicators += content.lower().count(term)
        
        if total_content == 0:
            return 'unknown'
        
        # Calculate technical density
        technical_density = technical_indicators / (total_content / 1000)  # Per 1000 characters
        
        if technical_density > 10:
            return 'highly_technical'
        elif technical_density > 5:
            return 'moderately_technical'
        elif technical_density > 2:
            return 'somewhat_technical'
        else:
            return 'non_technical'
    
    def identify_structure_type(self, sections: List[Dict[str, Any]]) -> str:
        """Identify the structural pattern of the document"""
        section_types = [section.get('section_type', 'content') for section in sections]
        titles = [section.get('title', '').lower() for section in sections]
        
        # Check for common patterns
        if any('getting started' in title for title in titles) and any('api' in title for title in titles):
            return 'tutorial_with_reference'
        elif section_types.count('api_endpoint') > len(sections) * 0.4:
            return 'api_reference'
        elif any(term in ' '.join(titles) for term in ['install', 'setup', 'config']):
            return 'installation_guide'
        elif any(term in ' '.join(titles) for term in ['tutorial', 'how to', 'step']):
            return 'tutorial'
        else:
            return 'general_documentation'
    
    def generate_executive_summary(self, sections: List[Dict[str, Any]], 
                                 analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a high-level executive summary"""
        target_tokens = self.summary_lengths['executive']
        
        # Build executive summary content
        summary_parts = []
        
        # Document overview
        doc_type = analysis['document_type'].replace('_', ' ').title()
        summary_parts.append(f"## Document Overview\n\nThis is a {doc_type} ")
        
        # Main themes
        themes = analysis.get('content_themes', [])
        if themes:
            themes_text = ', '.join(themes[:3])
            summary_parts.append(f"covering {themes_text}.")
        else:
            summary_parts.append("containing technical documentation.")
        
        # Key sections highlight
        key_sections = analysis.get('key_sections', [])[:3]
        if key_sections:
            summary_parts.append(f"\n\n## Key Areas\n\n")
            for key_section in key_sections:
                section = key_section['section']
                title = section.get('title', 'Untitled Section')
                # Extract first sentence or key points
                content = section.get('content', '')
                preview = self.extract_key_sentence(content)
                summary_parts.append(f"- **{title}**: {preview}\n")
        
        # Technical depth indication
        tech_depth = analysis.get('technical_depth', 'unknown')
        if tech_depth != 'unknown':
            depth_desc = {
                'highly_technical': 'highly technical with detailed implementation details',
                'moderately_technical': 'moderately technical with code examples and API details',
                'somewhat_technical': 'includes some technical concepts and examples',
                'non_technical': 'primarily non-technical with general information'
            }
            summary_parts.append(f"\n\n## Technical Level\n\nThis document is {depth_desc.get(tech_depth, 'technical')}.")
        
        # Priority concepts
        priority_concepts = analysis.get('priority_concepts', [])[:5]
        if priority_concepts:
            summary_parts.append(f"\n\n## Key Concepts\n\n")
            for concept in priority_concepts:
                term = concept['term']
                definition = concept['info'].get('definition', '')
                if definition:
                    short_def = definition[:100] + "..." if len(definition) > 100 else definition
                    summary_parts.append(f"- **{term}**: {short_def}\n")
                else:
                    summary_parts.append(f"- **{term}**\n")
        
        content = ''.join(summary_parts)
        
        # Trim to target length if needed
        if self.token_counter.count_tokens(content) > target_tokens:
            content = self.trim_content_to_tokens(content, target_tokens)
        
        return {
            'type': 'executive',
            'title': 'Executive Summary',
            'content': content,
            'token_count': self.token_counter.count_tokens(content),
            'sections_covered': len(key_sections),
            'concepts_covered': len(priority_concepts)
        }
    
    def generate_detailed_summary(self, sections: List[Dict[str, Any]], 
                                analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed section-by-section summary"""
        target_tokens = self.summary_lengths['detailed']
        
        summary_parts = []
        summary_parts.append("# Detailed Summary\n\n")
        
        # Document overview
        doc_type = analysis['document_type'].replace('_', ' ').title()
        structure_type = analysis['structure_type'].replace('_', ' ').title()
        summary_parts.append(f"This {doc_type} follows a {structure_type} structure with {len(sections)} main sections.\n\n")
        
        # Section-by-section breakdown
        summary_parts.append("## Section Breakdown\n\n")
        
        tokens_used = self.token_counter.count_tokens(''.join(summary_parts))
        tokens_per_section = min(200, (target_tokens - tokens_used) // len(sections))
        
        for i, section in enumerate(sections):
            title = section.get('title', f'Section {i+1}')
            content = section.get('content', '')
            section_type = section.get('section_type', 'content')
            
            summary_parts.append(f"### {i+1}. {title}\n\n")
            
            # Generate section summary
            section_summary = self.summarize_section_content(content, tokens_per_section)
            summary_parts.append(f"{section_summary}\n\n")
            
            # Add section metadata
            if section_type != 'content':
                type_desc = section_type.replace('_', ' ').title()
                summary_parts.append(f"*Section Type: {type_desc}*\n\n")
        
        content = ''.join(summary_parts)
        
        # Trim if over target
        if self.token_counter.count_tokens(content) > target_tokens:
            content = self.trim_content_to_tokens(content, target_tokens)
        
        return {
            'type': 'detailed',
            'title': 'Detailed Summary',
            'content': content,
            'token_count': self.token_counter.count_tokens(content),
            'sections_covered': len(sections),
            'average_section_tokens': tokens_per_section
        }
    
    def generate_complete_summary(self, sections: List[Dict[str, Any]], 
                                analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary with full context"""
        target_tokens = self.summary_lengths['complete']
        
        summary_parts = []
        summary_parts.append("# Complete Summary\n\n")
        
        # Full document analysis
        doc_type = analysis['document_type'].replace('_', ' ').title()
        themes = analysis.get('content_themes', [])
        tech_depth = analysis.get('technical_depth', 'unknown')
        
        summary_parts.append(f"## Document Analysis\n\n")
        summary_parts.append(f"**Type**: {doc_type}\n")
        summary_parts.append(f"**Technical Depth**: {tech_depth.replace('_', ' ').title()}\n")
        summary_parts.append(f"**Main Themes**: {', '.join(themes)}\n")
        summary_parts.append(f"**Total Sections**: {len(sections)}\n\n")
        
        # Complete section coverage
        summary_parts.append("## Complete Section Analysis\n\n")
        
        tokens_used = self.token_counter.count_tokens(''.join(summary_parts))
        remaining_tokens = target_tokens - tokens_used
        tokens_per_section = remaining_tokens // len(sections) if sections else 0
        
        for i, section in enumerate(sections):
            title = section.get('title', f'Section {i+1}')
            content = section.get('content', '')
            section_type = section.get('section_type', 'content')
            
            summary_parts.append(f"### {i+1}. {title}\n\n")
            
            # More comprehensive section summary
            section_summary = self.summarize_section_content(content, tokens_per_section, detailed=True)
            summary_parts.append(f"{section_summary}\n\n")
            
            # Include key examples or code if present
            examples = self.extract_examples_from_section(content)
            if examples:
                summary_parts.append("**Key Examples:**\n")
                for example in examples[:2]:  # Limit to 2 examples per section
                    summary_parts.append(f"- {example}\n")
                summary_parts.append("\n")
        
        # Include important tables
        important_tables = analysis.get('important_tables', [])
        if important_tables:
            summary_parts.append("## Important Tables\n\n")
            for table_info in important_tables[:3]:
                table = table_info['table']
                page = table.get('page', 'Unknown')
                rows = table.get('rows', 0)
                summary_parts.append(f"**Table from Page {page}** ({rows} rows)\n")
                markdown = table.get('markdown', '')[:500]  # Limit table size
                summary_parts.append(f"{markdown}...\n\n" if len(table.get('markdown', '')) > 500 else f"{markdown}\n\n")
        
        content = ''.join(summary_parts)
        
        return {
            'type': 'complete',
            'title': 'Complete Summary',
            'content': content,
            'token_count': self.token_counter.count_tokens(content),
            'sections_covered': len(sections),
            'tables_included': len(important_tables)
        }
    
    def generate_technical_summary(self, sections: List[Dict[str, Any]], 
                                 analysis: Dict[str, Any],
                                 concepts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a technical-focused summary"""
        target_tokens = self.summary_lengths['technical']
        
        summary_parts = []
        summary_parts.append("# Technical Summary\n\n")
        
        # Technical overview
        tech_depth = analysis.get('technical_depth', 'unknown')
        summary_parts.append(f"## Technical Overview\n\n")
        summary_parts.append(f"**Technical Complexity**: {tech_depth.replace('_', ' ').title()}\n\n")
        
        # Key technical concepts
        priority_concepts = analysis.get('priority_concepts', [])
        technical_concepts = [c for c in priority_concepts if c['info'].get('category') in 
                            ['api', 'security', 'authentication', 'http', 'database', 'framework']]
        
        if technical_concepts:
            summary_parts.append("## Key Technical Concepts\n\n")
            for concept in technical_concepts[:10]:
                term = concept['term']
                info = concept['info']
                category = info.get('category', 'general').upper()
                definition = info.get('definition', '')
                frequency = info.get('frequency', 0)
                
                summary_parts.append(f"### {term} ({category})\n")
                if definition:
                    summary_parts.append(f"{definition}\n")
                summary_parts.append(f"*Frequency: {frequency} occurrences*\n\n")
        
        # Technical sections
        technical_sections = [s for s in sections if s.get('section_type') in 
                            ['api_endpoint', 'code_example', 'authentication', 'error_handling']]
        
        if technical_sections:
            summary_parts.append("## Technical Sections\n\n")
            for section in technical_sections:
                title = section.get('title', 'Untitled')
                content = section.get('content', '')
                section_type = section.get('section_type', '')
                
                summary_parts.append(f"### {title}\n")
                summary_parts.append(f"**Type**: {section_type.replace('_', ' ').title()}\n")
                
                # Extract technical details
                tech_summary = self.extract_technical_details(content)
                summary_parts.append(f"{tech_summary}\n\n")
        
        content = ''.join(summary_parts)
        
        # Trim to target length
        if self.token_counter.count_tokens(content) > target_tokens:
            content = self.trim_content_to_tokens(content, target_tokens)
        
        return {
            'type': 'technical',
            'title': 'Technical Summary',
            'content': content,
            'token_count': self.token_counter.count_tokens(content),
            'technical_concepts': len(technical_concepts),
            'technical_sections': len(technical_sections)
        }
    
    def generate_api_summary(self, sections: List[Dict[str, Any]], 
                           analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API-focused summary"""
        api_sections = [s for s in sections if 'api' in s.get('title', '').lower() or 
                       s.get('section_type') == 'api_endpoint']
        
        if not api_sections:
            return {
                'type': 'api',
                'title': 'API Summary',
                'content': "No API-specific content found in this document.",
                'token_count': 0,
                'endpoints_found': 0
            }
        
        summary_parts = []
        summary_parts.append("# API Summary\n\n")
        
        # Extract endpoints
        endpoints = []
        for section in api_sections:
            content = section.get('content', '')
            section_endpoints = self.extract_api_endpoints(content)
            endpoints.extend(section_endpoints)
        
        if endpoints:
            summary_parts.append(f"## API Endpoints ({len(endpoints)})\n\n")
            summary_parts.append("| Method | Endpoint | Description |\n")
            summary_parts.append("|--------|----------|-------------|\n")
            
            for endpoint in endpoints[:20]:  # Limit to 20 endpoints
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '')
                description = endpoint.get('description', 'No description')[:100]
                summary_parts.append(f"| {method} | {path} | {description} |\n")
        
        summary_parts.append("\n")
        
        # API sections summary
        summary_parts.append("## API Documentation Sections\n\n")
        for section in api_sections:
            title = section.get('title', 'Untitled')
            content = section.get('content', '')
            summary = self.summarize_section_content(content, 150)
            summary_parts.append(f"### {title}\n{summary}\n\n")
        
        content = ''.join(summary_parts)
        
        return {
            'type': 'api',
            'title': 'API Summary',
            'content': content,
            'token_count': self.token_counter.count_tokens(content),
            'endpoints_found': len(endpoints),
            'api_sections': len(api_sections)
        }
    
    def generate_security_summary(self, sections: List[Dict[str, Any]], 
                                analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security-focused summary"""
        security_content = []
        
        for section in sections:
            title = section.get('title', '').lower()
            content = section.get('content', '')
            
            # Check for security-related content
            if any(term in title for term in ['security', 'auth', 'encryption', 'ssl', 'https']):
                security_content.append(section)
            elif any(term in content.lower() for term in ['security', 'authentication', 'authorization', 
                                                        'encryption', 'token', 'oauth', 'ssl', 'https']):
                # Extract security-relevant portions
                security_excerpt = self.extract_security_content(content)
                if security_excerpt:
                    security_content.append({
                        'title': title,
                        'content': security_excerpt,
                        'section_type': 'security_excerpt'
                    })
        
        if not security_content:
            return {
                'type': 'security',
                'title': 'Security Summary',
                'content': "No specific security content found in this document.",
                'token_count': 0,
                'security_sections': 0
            }
        
        summary_parts = []
        summary_parts.append("# Security Summary\n\n")
        summary_parts.append(f"Found {len(security_content)} sections with security-related content.\n\n")
        
        for section in security_content:
            title = section.get('title', 'Security Content')
            content = section.get('content', '')
            summary = self.summarize_section_content(content, 200)
            summary_parts.append(f"## {title}\n{summary}\n\n")
        
        content = ''.join(summary_parts)
        
        return {
            'type': 'security',
            'title': 'Security Summary',
            'content': content,
            'token_count': self.token_counter.count_tokens(content),
            'security_sections': len(security_content)
        }
    
    def generate_integration_summary(self, sections: List[Dict[str, Any]], 
                                   analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate integration and getting started summary"""
        integration_sections = []
        
        for section in sections:
            title = section.get('title', '').lower()
            content = section.get('content', '')
            
            if any(term in title for term in ['getting started', 'integration', 'setup', 'installation', 
                                            'quick start', 'tutorial', 'example']):
                integration_sections.append(section)
        
        if not integration_sections:
            return {
                'type': 'integration',
                'title': 'Integration Summary',
                'content': "No integration or getting started content found.",
                'token_count': 0,
                'integration_sections': 0
            }
        
        summary_parts = []
        summary_parts.append("# Integration Summary\n\n")
        
        for section in integration_sections:
            title = section.get('title', 'Integration Step')
            content = section.get('content', '')
            
            # Extract key steps and examples
            summary = self.extract_integration_steps(content)
            summary_parts.append(f"## {title}\n{summary}\n\n")
        
        content = ''.join(summary_parts)
        
        return {
            'type': 'integration',
            'title': 'Integration Summary',
            'content': content,
            'token_count': self.token_counter.count_tokens(content),
            'integration_sections': len(integration_sections)
        }
    
    def create_summary_files(self, summaries: Dict[str, Dict[str, Any]]) -> List[str]:
        """Create markdown files for each summary type"""
        created_files = []
        
        for summary_type, summary_data in summaries.items():
            if summary_data and summary_data.get('content'):
                filename = f"{summary_type}-summary.md"
                file_path = self.summaries_dir / filename
                
                # Create full markdown content with metadata
                full_content = self.format_summary_file(summary_data)
                
                FileUtils.write_markdown(full_content, file_path)
                created_files.append(str(file_path))
        
        return created_files
    
    def format_summary_file(self, summary_data: Dict[str, Any]) -> str:
        """Format summary data into complete markdown file"""
        title = summary_data.get('title', 'Summary')
        content = summary_data.get('content', '')
        token_count = summary_data.get('token_count', 0)
        summary_type = summary_data.get('type', 'unknown')
        
        # Add metadata header
        metadata = f"""---
title: {title}
type: {summary_type}
generated: {datetime.now().isoformat()}
token_count: {token_count}
---

"""
        
        return metadata + content
    
    def create_summary_index(self, summary_files: List[str]) -> Path:
        """Create an index of all summaries"""
        index_content = f"""# Summary Index

**Generated**: {datetime.now().isoformat()}

This document provides an index of all generated summaries.

## Available Summaries

"""
        
        summary_descriptions = {
            'executive': 'High-level overview and key points',
            'detailed': 'Section-by-section breakdown',
            'complete': 'Comprehensive summary with full context',
            'technical': 'Technical concepts and implementation details',
            'api': 'API endpoints and integration information',
            'security': 'Security-related content and considerations',
            'integration': 'Getting started and integration guidance'
        }
        
        for file_path in summary_files:
            file_path_obj = Path(file_path)
            filename = file_path_obj.name
            summary_type = filename.replace('-summary.md', '')
            
            description = summary_descriptions.get(summary_type, 'General summary')
            relative_path = file_path_obj.name
            
            index_content += f"- [{summary_type.title()} Summary]({relative_path}) - {description}\n"
        
        index_content += f"""

## Usage Guidelines

- **Executive Summary**: Best for quick overview and decision-making
- **Detailed Summary**: Good for understanding document structure
- **Complete Summary**: Use when you need full context and comprehensive coverage
- **Technical Summary**: Focus on implementation details and technical concepts
- **API Summary**: Essential for developers integrating with APIs
- **Security Summary**: Important for security reviews and compliance
- **Integration Summary**: Start here for implementation and getting started

"""
        
        index_file = self.summaries_dir / "README.md"
        FileUtils.write_markdown(index_content, index_file)
        return index_file
    
    # Helper methods
    
    def extract_key_sentence(self, content: str) -> str:
        """Extract the most informative sentence from content"""
        sentences = TextUtils.split_into_sentences(content)
        if not sentences:
            return "No content available."
        
        # Score sentences by information content
        scored_sentences = []
        for sentence in sentences[:10]:  # Only check first 10 sentences
            score = 0
            sentence_lower = sentence.lower()
            
            # Prefer sentences with key terms
            key_terms = ['api', 'authentication', 'configuration', 'example', 'method', 'endpoint']
            score += sum(1 for term in key_terms if term in sentence_lower)
            
            # Prefer sentences of moderate length
            if 50 <= len(sentence) <= 200:
                score += 2
            elif 20 <= len(sentence) <= 300:
                score += 1
            
            # Avoid sentences that are too generic
            generic_starters = ['this', 'the', 'it', 'you can', 'there are']
            if not any(sentence_lower.startswith(starter) for starter in generic_starters):
                score += 1
            
            scored_sentences.append((sentence, score))
        
        # Return highest scoring sentence
        if scored_sentences:
            best_sentence = max(scored_sentences, key=lambda x: x[1])[0]
            return best_sentence[:200] + "..." if len(best_sentence) > 200 else best_sentence
        
        return sentences[0][:200] + "..." if len(sentences[0]) > 200 else sentences[0]
    
    def summarize_section_content(self, content: str, target_tokens: int, detailed: bool = False) -> str:
        """Create a summary of section content within token limit"""
        if not content:
            return "No content available."
        
        # Extract key sentences
        sentences = TextUtils.split_into_sentences(content)
        if not sentences:
            return "No content available."
        
        # For detailed summaries, include more context
        if detailed:
            # Take first few and last few sentences, plus any with key terms
            key_sentences = sentences[:3]  # First 3
            if len(sentences) > 6:
                key_sentences.extend(sentences[-2:])  # Last 2
            
            # Add sentences with important terms
            important_terms = ['important', 'note', 'example', 'required', 'must', 'should']
            for sentence in sentences[3:-2]:  # Middle sentences
                if any(term in sentence.lower() for term in important_terms):
                    key_sentences.append(sentence)
                    if len(key_sentences) >= 8:  # Limit total sentences
                        break
        else:
            # Take first few sentences and key sentences
            key_sentences = sentences[:2]
            if len(sentences) > 3:
                # Look for sentences with key information
                for sentence in sentences[2:6]:
                    sentence_lower = sentence.lower()
                    if any(term in sentence_lower for term in ['api', 'method', 'parameter', 'example', 'required']):
                        key_sentences.append(sentence)
                        break
        
        # Join and trim to token limit
        summary = ' '.join(key_sentences)
        
        if self.token_counter.count_tokens(summary) > target_tokens:
            summary = self.trim_content_to_tokens(summary, target_tokens)
        
        return summary
    
    def trim_content_to_tokens(self, content: str, target_tokens: int) -> str:
        """Trim content to fit within token limit"""
        current_tokens = self.token_counter.count_tokens(content)
        if current_tokens <= target_tokens:
            return content
        
        # Estimate character ratio
        char_ratio = len(content) / current_tokens
        target_chars = int(target_tokens * char_ratio * 0.9)  # 90% to be safe
        
        # Trim at sentence boundary if possible
        trimmed = content[:target_chars]
        last_period = trimmed.rfind('.')
        if last_period > target_chars * 0.8:  # If we can trim at sentence boundary
            trimmed = trimmed[:last_period + 1]
        
        # Add ellipsis if we trimmed
        if len(trimmed) < len(content):
            trimmed += "..."
        
        return trimmed
    
    def extract_examples_from_section(self, content: str) -> List[str]:
        """Extract code examples or important examples from section"""
        examples = []
        
        # Look for code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        for block in code_blocks[:2]:  # Limit to 2 code blocks
            # Extract just the code content
            lines = block.split('\n')[1:-1]  # Remove ``` lines
            if lines:
                code_content = '\n'.join(lines)[:200]  # Limit length
                examples.append(f"Code example: {code_content}...")
        
        # Look for example sections
        example_patterns = [
            r'(?i)example[:\s]+(.*?)(?:\n\n|\n[A-Z])',
            r'(?i)for example[:\s,]+(.*?)(?:\n\n|\n[A-Z])',
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches[:2]:  # Limit examples
                clean_match = match.strip()[:150]  # Limit length
                examples.append(f"Example: {clean_match}...")
        
        return examples
    
    def extract_technical_details(self, content: str) -> str:
        """Extract technical details from content"""
        # Look for technical patterns
        technical_snippets = []
        
        # HTTP methods and endpoints
        http_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}.:]+)'
        http_matches = re.findall(http_pattern, content, re.IGNORECASE)
        for method, endpoint in http_matches[:3]:
            technical_snippets.append(f"**{method}** `{endpoint}`")
        
        # Parameters
        param_pattern = r'(?i)parameter[s]?[:\s]+(.*?)(?:\n\n|\n[A-Z])'
        param_matches = re.findall(param_pattern, content, re.DOTALL)
        for match in param_matches[:2]:
            clean_match = match.strip()[:100]
            technical_snippets.append(f"Parameters: {clean_match}")
        
        # Response formats
        response_pattern = r'(?i)response[:\s]+(.*?)(?:\n\n|\n[A-Z])'
        response_matches = re.findall(response_pattern, content, re.DOTALL)
        for match in response_matches[:1]:
            clean_match = match.strip()[:100]
            technical_snippets.append(f"Response: {clean_match}")
        
        if technical_snippets:
            return '\n'.join(technical_snippets)
        else:
            # Fallback to first few sentences
            sentences = TextUtils.split_into_sentences(content)
            return ' '.join(sentences[:2]) if sentences else "No technical details found."
    
    def extract_api_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from content"""
        endpoints = []
        
        # Pattern for HTTP method + endpoint
        endpoint_pattern = r'(?i)(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}.:]+)'
        matches = re.finditer(endpoint_pattern, content)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            
            # Try to find description near the endpoint
            context_start = max(0, match.start() - 200)
            context_end = min(len(content), match.end() + 200)
            context = content[context_start:context_end]
            
            # Extract description (simple heuristic)
            description = "No description"
            sentences = TextUtils.split_into_sentences(context)
            for sentence in sentences:
                if len(sentence) > 20 and len(sentence) < 200:
                    description = sentence
                    break
            
            endpoints.append({
                'method': method,
                'path': path,
                'description': description
            })
        
        return endpoints
    
    def extract_security_content(self, content: str) -> str:
        """Extract security-related content from text"""
        security_keywords = ['security', 'authentication', 'authorization', 'encryption', 
                           'token', 'oauth', 'ssl', 'https', 'api key', 'secret']
        
        sentences = TextUtils.split_into_sentences(content)
        security_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in security_keywords):
                security_sentences.append(sentence)
                if len(security_sentences) >= 5:  # Limit to 5 sentences
                    break
        
        return ' '.join(security_sentences) if security_sentences else ""
    
    def extract_integration_steps(self, content: str) -> str:
        """Extract integration steps and examples"""
        # Look for numbered steps or bullet points
        step_patterns = [
            r'(?m)^\d+\.\s+(.+)',  # Numbered steps
            r'(?m)^[-*]\s+(.+)',   # Bullet points
            r'(?i)step\s+\d+[:\s]+(.+)'  # Step references
        ]
        
        steps = []
        for pattern in step_patterns:
            matches = re.findall(pattern, content)
            steps.extend(matches[:5])  # Limit to 5 steps per pattern
        
        if steps:
            formatted_steps = '\n'.join(f"- {step}" for step in steps[:8])  # Max 8 total steps
            return formatted_steps
        else:
            # Fallback to extracting key sentences
            sentences = TextUtils.split_into_sentences(content)
            key_sentences = [s for s in sentences[:5] if len(s) > 30]
            return '\n'.join(f"- {sentence}" for sentence in key_sentences[:4])

from collections import defaultdict