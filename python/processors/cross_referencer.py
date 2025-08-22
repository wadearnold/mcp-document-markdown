try:
    from ..utils.text_utils import TextUtils
    from ..utils.file_utils import FileUtils
except ImportError:
    # Handle running as script vs package
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.text_utils import TextUtils
    from utils.file_utils import FileUtils
"""
Cross-reference resolution and link creation
"""
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime


class CrossReferencer:
    """Handles cross-reference resolution and internal link creation"""
    
    def __init__(self, output_dir: str):
        """
        Initialize cross-referencer
        
        Args:
            output_dir: Output directory for cross-reference files
        """
        self.output_dir = Path(output_dir)
        self.references_dir = self.output_dir / "references"
        FileUtils.ensure_directory(self.references_dir)
        
        # Track references and links
        self.internal_refs = {}
        self.external_refs = {}
        self.section_refs = {}
        self.page_refs = {}
        self.figure_refs = {}
        self.table_refs = {}
        
    def resolve_cross_references(self, sections: List[Dict[str, Any]], 
                                concepts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve cross-references throughout the document
        
        Args:
            sections: List of document sections
            concepts: Extracted concepts and terms
            
        Returns:
            Cross-reference resolution results
        """
        if not sections:
            return {}
        
        # Build reference maps
        self.build_reference_maps(sections)
        
        # Extract and categorize references
        all_references = self.extract_all_references(sections)
        
        # Resolve internal references
        resolved_internal = self.resolve_internal_references(all_references, concepts)
        
        # Resolve external references
        resolved_external = self.resolve_external_references(all_references)
        
        # Create link mapping
        link_mapping = self.create_link_mapping(resolved_internal, resolved_external)
        
        # Generate cross-reference files
        xref_files = self.generate_cross_reference_files(
            resolved_internal, resolved_external, link_mapping
        )
        
        return {
            'internal_references': resolved_internal,
            'external_references': resolved_external,
            'link_mapping': link_mapping,
            'reference_files': xref_files,
            'stats': {
                'total_internal_refs': len(resolved_internal),
                'total_external_refs': len(resolved_external),
                'total_links_created': len(link_mapping),
                'broken_references': self.count_broken_references(resolved_internal)
            }
        }
    
    def build_reference_maps(self, sections: List[Dict[str, Any]]) -> None:
        """Build maps of sections, pages, figures, and tables for reference resolution"""
        for i, section in enumerate(sections):
            section_id = i + 1
            title = section.get('title', f'Section {section_id}')
            content = section.get('content', '')
            
            # Map section references
            self.section_refs[section_id] = {
                'title': title,
                'index': i,
                'anchor': self.create_anchor(title),
                'content_preview': content[:200] + "..." if len(content) > 200 else content
            }
            
            # Extract and map page references
            page_refs = self.extract_page_references(content)
            for page_num in page_refs:
                if page_num not in self.page_refs:
                    self.page_refs[page_num] = []
                self.page_refs[page_num].append(section_id)
            
            # Extract and map figure references
            figure_refs = self.extract_figure_references(content)
            for fig_ref in figure_refs:
                self.figure_refs[fig_ref['id']] = {
                    'section': section_id,
                    'caption': fig_ref.get('caption', ''),
                    'type': fig_ref.get('type', 'figure')
                }
            
            # Extract and map table references
            table_refs = self.extract_table_references(content)
            for table_ref in table_refs:
                self.table_refs[table_ref['id']] = {
                    'section': section_id,
                    'caption': table_ref.get('caption', ''),
                    'rows': table_ref.get('rows', 0)
                }
    
    def extract_all_references(self, sections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all types of references from sections"""
        all_refs = {
            'section_refs': [],
            'page_refs': [],
            'figure_refs': [],
            'table_refs': [],
            'url_refs': [],
            'api_refs': [],
            'concept_refs': []
        }
        
        for i, section in enumerate(sections):
            content = section.get('content', '')
            section_id = i + 1
            
            # Section references (e.g., "See Section 5", "Chapter 2")
            section_refs = self.find_section_references(content, section_id)
            all_refs['section_refs'].extend(section_refs)
            
            # Page references (e.g., "on page 10", "p. 25")
            page_refs = self.find_page_references(content, section_id)
            all_refs['page_refs'].extend(page_refs)
            
            # Figure references (e.g., "Figure 1", "Fig. 3")
            figure_refs = self.find_figure_references(content, section_id)
            all_refs['figure_refs'].extend(figure_refs)
            
            # Table references (e.g., "Table 2", "see table below")
            table_refs = self.find_table_references(content, section_id)
            all_refs['table_refs'].extend(table_refs)
            
            # URL references
            url_refs = self.find_url_references(content, section_id)
            all_refs['url_refs'].extend(url_refs)
            
            # API references (e.g., "/api/users", "GET /endpoint")
            api_refs = self.find_api_references(content, section_id)
            all_refs['api_refs'].extend(api_refs)
            
            # Concept references (terms that link to definitions)
            concept_refs = self.find_concept_references(content, section_id)
            all_refs['concept_refs'].extend(concept_refs)
        
        return all_refs
    
    def find_section_references(self, content: str, source_section: int) -> List[Dict[str, Any]]:
        """Find references to other sections"""
        refs = []
        
        # Patterns for section references
        patterns = [
            r'(?i)(?:see\s+)?(?:section|chapter|part)\s+(\d+)',
            r'(?i)(?:in\s+)?(?:section|chapter)\s+(\d+)',
            r'(?i)(?:refer\s+to\s+)?(?:section|chapter)\s+(\d+)',
            r'§\s*(\d+)',
            r'(?i)above\s+(?:in\s+)?(?:section|chapter)\s+(\d+)',
            r'(?i)below\s+(?:in\s+)?(?:section|chapter)\s+(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                target_section = int(match.group(1))
                refs.append({
                    'type': 'section',
                    'source_section': source_section,
                    'target_section': target_section,
                    'text': match.group(0),
                    'position': match.start(),
                    'context': self.get_context(content, match.start())
                })
        
        return refs
    
    def find_page_references(self, content: str, source_section: int) -> List[Dict[str, Any]]:
        """Find references to page numbers"""
        refs = []
        
        patterns = [
            r'(?i)(?:on\s+)?page\s+(\d+)',
            r'(?i)p\.\s*(\d+)',
            r'(?i)pp\.\s*(\d+)-(\d+)',
            r'(?i)(?:see\s+)?page\s+(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                page_num = int(match.group(1))
                refs.append({
                    'type': 'page',
                    'source_section': source_section,
                    'target_page': page_num,
                    'text': match.group(0),
                    'position': match.start(),
                    'context': self.get_context(content, match.start())
                })
        
        return refs
    
    def find_figure_references(self, content: str, source_section: int) -> List[Dict[str, Any]]:
        """Find references to figures"""
        refs = []
        
        patterns = [
            r'(?i)(?:see\s+)?figure\s+(\d+)',
            r'(?i)fig\.\s*(\d+)',
            r'(?i)(?:as\s+shown\s+in\s+)?figure\s+(\d+)',
            r'(?i)(?:the\s+)?diagram\s+(?:in\s+)?(?:figure\s+)?(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                figure_num = int(match.group(1))
                refs.append({
                    'type': 'figure',
                    'source_section': source_section,
                    'target_figure': figure_num,
                    'text': match.group(0),
                    'position': match.start(),
                    'context': self.get_context(content, match.start())
                })
        
        return refs
    
    def find_table_references(self, content: str, source_section: int) -> List[Dict[str, Any]]:
        """Find references to tables"""
        refs = []
        
        patterns = [
            r'(?i)(?:see\s+)?table\s+(\d+)',
            r'(?i)(?:in\s+)?table\s+(\d+)',
            r'(?i)(?:the\s+)?(?:following\s+)?table\s+(\d+)?',
            r'(?i)(?:as\s+shown\s+in\s+)?table\s+(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                table_num = match.group(1)
                if table_num:
                    table_num = int(table_num)
                else:
                    table_num = 0  # Generic table reference
                
                refs.append({
                    'type': 'table',
                    'source_section': source_section,
                    'target_table': table_num,
                    'text': match.group(0),
                    'position': match.start(),
                    'context': self.get_context(content, match.start())
                })
        
        return refs
    
    def find_url_references(self, content: str, source_section: int) -> List[Dict[str, Any]]:
        """Find URL references"""
        refs = []
        
        # URL pattern
        url_pattern = r'https?://[^\s<>"\'`|\\{}^[\]]+[^\s<>"\'`|\\{}^[\].,;:!?)]'
        
        matches = re.finditer(url_pattern, content)
        for match in matches:
            url = match.group(0)
            refs.append({
                'type': 'url',
                'source_section': source_section,
                'url': url,
                'domain': self.extract_domain(url),
                'text': url,
                'position': match.start(),
                'context': self.get_context(content, match.start())
            })
        
        return refs
    
    def find_api_references(self, content: str, source_section: int) -> List[Dict[str, Any]]:
        """Find API endpoint references"""
        refs = []
        
        patterns = [
            r'(?i)(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}.:]+)',
            r'(/api/[/\w\-{}.:]*)',
            r'(/v\d+/[/\w\-{}.:]*)',
            r'(?i)endpoint[:\s]+([/\w\-{}.:]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) >= 2:
                    method = match.group(1)
                    endpoint = match.group(2)
                else:
                    method = None
                    endpoint = match.group(1)
                
                refs.append({
                    'type': 'api',
                    'source_section': source_section,
                    'method': method,
                    'endpoint': endpoint,
                    'text': match.group(0),
                    'position': match.start(),
                    'context': self.get_context(content, match.start())
                })
        
        return refs
    
    def find_concept_references(self, content: str, source_section: int) -> List[Dict[str, Any]]:
        """Find references to concepts that could be linked to definitions"""
        refs = []
        
        # Technical terms that might have definitions
        concept_patterns = [
            r'(?i)\b(API|REST|HTTP|JSON|XML|OAuth|JWT|SSL|TLS|CRUD)\b',
            r'(?i)\b(authentication|authorization|endpoint|middleware|payload)\b',
            r'(?i)\b(database|query|schema|index|migration|transaction)\b',
            r'(?i)\b(framework|library|module|package|dependency)\b'
        ]
        
        for pattern in concept_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                concept = match.group(1).lower()
                refs.append({
                    'type': 'concept',
                    'source_section': source_section,
                    'concept': concept,
                    'text': match.group(0),
                    'position': match.start(),
                    'context': self.get_context(content, match.start())
                })
        
        return refs
    
    def resolve_internal_references(self, all_refs: Dict[str, List], 
                                  concepts: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve internal references to create links"""
        resolved = {
            'section_links': [],
            'page_links': [],
            'figure_links': [],
            'table_links': [],
            'concept_links': [],
            'broken_refs': []
        }
        
        # Resolve section references
        for ref in all_refs['section_refs']:
            target_section = ref['target_section']
            if target_section in self.section_refs:
                resolved['section_links'].append({
                    **ref,
                    'target_info': self.section_refs[target_section],
                    'link_target': f"#section-{target_section}",
                    'resolved': True
                })
            else:
                resolved['broken_refs'].append({**ref, 'reason': 'section_not_found'})
        
        # Resolve page references
        for ref in all_refs['page_refs']:
            target_page = ref['target_page']
            if target_page in self.page_refs:
                sections_on_page = self.page_refs[target_page]
                resolved['page_links'].append({
                    **ref,
                    'sections_on_page': sections_on_page,
                    'link_target': f"#page-{target_page}",
                    'resolved': True
                })
            else:
                resolved['broken_refs'].append({**ref, 'reason': 'page_not_found'})
        
        # Resolve figure references
        for ref in all_refs['figure_refs']:
            target_figure = ref['target_figure']
            if target_figure in self.figure_refs:
                resolved['figure_links'].append({
                    **ref,
                    'target_info': self.figure_refs[target_figure],
                    'link_target': f"#figure-{target_figure}",
                    'resolved': True
                })
            else:
                resolved['broken_refs'].append({**ref, 'reason': 'figure_not_found'})
        
        # Resolve table references
        for ref in all_refs['table_refs']:
            target_table = ref['target_table']
            if target_table in self.table_refs:
                resolved['table_links'].append({
                    **ref,
                    'target_info': self.table_refs[target_table],
                    'link_target': f"#table-{target_table}",
                    'resolved': True
                })
            else:
                resolved['broken_refs'].append({**ref, 'reason': 'table_not_found'})
        
        # Resolve concept references
        concept_terms = concepts.get('terms', {}) if concepts else {}
        for ref in all_refs['concept_refs']:
            concept = ref['concept']
            if concept in concept_terms:
                resolved['concept_links'].append({
                    **ref,
                    'definition': concept_terms[concept].get('definition', ''),
                    'category': concept_terms[concept].get('category', ''),
                    'link_target': f"#concept-{concept}",
                    'resolved': True
                })
        
        return resolved
    
    def resolve_external_references(self, all_refs: Dict[str, List]) -> List[Dict[str, Any]]:
        """Resolve external references (URLs, APIs)"""
        external = []
        
        # Process URL references
        for ref in all_refs['url_refs']:
            external.append({
                **ref,
                'external_type': 'url',
                'accessible': True  # Could add URL checking here
            })
        
        # Process API references
        for ref in all_refs['api_refs']:
            external.append({
                **ref,
                'external_type': 'api',
                'documentation_link': self.find_api_documentation(ref['endpoint'])
            })
        
        return external
    
    def create_link_mapping(self, resolved_internal: Dict[str, Any], 
                           resolved_external: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create a mapping of text to links for replacement"""
        link_mapping = {}
        
        # Internal links
        for link_type in ['section_links', 'page_links', 'figure_links', 'table_links', 'concept_links']:
            for link in resolved_internal.get(link_type, []):
                if link.get('resolved'):
                    original_text = link['text']
                    target_link = link['link_target']
                    # Create markdown link
                    markdown_link = f"[{original_text}]({target_link})"
                    link_mapping[original_text] = markdown_link
        
        # External links (already in proper format)
        for link in resolved_external:
            if link['external_type'] == 'url':
                original_text = link['text']
                url = link['url']
                # Keep as-is or create proper markdown link
                link_mapping[original_text] = f"[{url}]({url})"
        
        return link_mapping
    
    def generate_cross_reference_files(self, resolved_internal: Dict[str, Any],
                                     resolved_external: List[Dict[str, Any]],
                                     link_mapping: Dict[str, str]) -> List[str]:
        """Generate cross-reference documentation files"""
        created_files = []
        
        # Create internal references file
        internal_file = self.create_internal_references_file(resolved_internal)
        created_files.append(str(internal_file))
        
        # Create external references file
        external_file = self.create_external_references_file(resolved_external)
        created_files.append(str(external_file))
        
        # Create link mapping file
        mapping_file = self.create_link_mapping_file(link_mapping)
        created_files.append(str(mapping_file))
        
        # Create broken references report if any
        if resolved_internal.get('broken_refs'):
            broken_file = self.create_broken_references_file(resolved_internal['broken_refs'])
            created_files.append(str(broken_file))
        
        return created_files
    
    def create_internal_references_file(self, resolved_internal: Dict[str, Any]) -> Path:
        """Create internal references documentation"""
        content = f"""# Internal Cross-References

**Generated**: {datetime.now().isoformat()}

This document catalogs all internal cross-references found in the document and their resolution status.

## Summary

"""
        
        for link_type, links in resolved_internal.items():
            if link_type != 'broken_refs' and links:
                count = len(links)
                content += f"- **{link_type.replace('_', ' ').title()}**: {count} references\\n"
        
        content += f"\\n## Reference Details\\n\\n"
        
        # Section References
        section_links = resolved_internal.get('section_links', [])
        if section_links:
            content += f"### Section References ({len(section_links)})\\n\\n"
            content += "| Source | Target | Text | Context |\\n"
            content += "|--------|--------|------|---------|\\n"
            
            for link in section_links:
                source = link['source_section']
                target = link['target_section']
                text = link['text']
                context = link['context'][:50] + "..." if len(link['context']) > 50 else link['context']
                
                content += f"| Section {source} | Section {target} | {text} | {context} |\\n"
            
            content += "\\n"
        
        # Add other reference types similarly...
        
        file_path = self.references_dir / "internal-references.md"
        FileUtils.write_markdown(content, file_path)
        return file_path
    
    def create_external_references_file(self, resolved_external: List[Dict[str, Any]]) -> Path:
        """Create external references documentation"""
        content = f"""# External References

**Generated**: {datetime.now().isoformat()}

This document catalogs all external references (URLs, APIs) found in the document.

## Summary

- **Total External References**: {len(resolved_external)}
- **URLs**: {len([r for r in resolved_external if r['external_type'] == 'url'])}
- **API Endpoints**: {len([r for r in resolved_external if r['external_type'] == 'api'])}

## URL References

"""
        
        url_refs = [r for r in resolved_external if r['external_type'] == 'url']
        if url_refs:
            content += "| URL | Domain | Source Section |\\n"
            content += "|-----|--------|----------------|\\n"
            
            for ref in url_refs:
                url = ref['url']
                domain = ref.get('domain', 'Unknown')
                source = ref['source_section']
                content += f"| {url} | {domain} | Section {source} |\\n"
        
        content += "\\n## API References\\n\\n"
        
        api_refs = [r for r in resolved_external if r['external_type'] == 'api']
        if api_refs:
            content += "| Method | Endpoint | Source Section |\\n"
            content += "|--------|----------|----------------|\\n"
            
            for ref in api_refs:
                method = ref.get('method', 'N/A')
                endpoint = ref['endpoint']
                source = ref['source_section']
                content += f"| {method} | {endpoint} | Section {source} |\\n"
        
        file_path = self.references_dir / "external-references.md"
        FileUtils.write_markdown(content, file_path)
        return file_path
    
    def create_link_mapping_file(self, link_mapping: Dict[str, str]) -> Path:
        """Create link mapping file for automated replacement"""
        content = f"""# Link Mapping

**Generated**: {datetime.now().isoformat()}

This file contains the mapping of original text to markdown links for automated replacement.

## Mappings ({len(link_mapping)})

"""
        
        for original, replacement in link_mapping.items():
            content += f"**Original**: `{original}`\\n"
            content += f"**Replacement**: `{replacement}`\\n\\n"
        
        file_path = self.references_dir / "link-mapping.md"
        FileUtils.write_markdown(content, file_path)
        
        # Also create JSON version for programmatic use
        json_file = self.references_dir / "link-mapping.json"
        FileUtils.write_json(link_mapping, json_file)
        
        return file_path
    
    def create_broken_references_file(self, broken_refs: List[Dict[str, Any]]) -> Path:
        """Create broken references report"""
        content = f"""# Broken References Report

**Generated**: {datetime.now().isoformat()}

This document lists all references that could not be resolved.

## Summary

- **Total Broken References**: {len(broken_refs)}

## Details

"""
        
        content += "| Type | Text | Source Section | Reason |\\n"
        content += "|------|------|----------------|--------|\\n"
        
        for ref in broken_refs:
            ref_type = ref['type']
            text = ref['text']
            source = ref['source_section']
            reason = ref['reason']
            
            content += f"| {ref_type} | {text} | Section {source} | {reason} |\\n"
        
        file_path = self.references_dir / "broken-references.md"
        FileUtils.write_markdown(content, file_path)
        return file_path
    
    # Helper methods
    
    def create_anchor(self, text: str) -> str:
        """Create a URL-safe anchor from text"""
        return FileUtils.safe_filename(text.lower().replace(' ', '-'))
    
    def get_context(self, content: str, position: int, context_length: int = 100) -> str:
        """Get context around a position in text"""
        start = max(0, position - context_length // 2)
        end = min(len(content), position + context_length // 2)
        return content[start:end].strip()
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return "unknown"
    
    def extract_page_references(self, content: str) -> Set[int]:
        """Extract page numbers mentioned in content"""
        pages = set()
        patterns = [r'(?i)page\s+(\d+)', r'(?i)p\.\s*(\d+)']
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                pages.add(int(match.group(1)))
        
        return pages
    
    def extract_figure_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract figure references with captions"""
        figures = []
        # This would be enhanced to actually parse figure captions
        # For now, just extract figure numbers
        pattern = r'(?i)figure\s+(\d+)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            figures.append({
                'id': int(match.group(1)),
                'caption': '',  # Would extract actual caption
                'type': 'figure'
            })
        
        return figures
    
    def extract_table_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract table references with metadata"""
        tables = []
        # Similar to figures, this would be enhanced
        pattern = r'(?i)table\s+(\d+)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            tables.append({
                'id': int(match.group(1)),
                'caption': '',  # Would extract actual caption
                'rows': 0      # Would count actual rows
            })
        
        return tables
    
    def find_api_documentation(self, endpoint: str) -> Optional[str]:
        """Find documentation link for API endpoint"""
        # This could be enhanced to check against known API documentation patterns
        if '/api/' in endpoint:
            return f"#api-docs{endpoint.replace('/', '-')}"
        return None
    
    def count_broken_references(self, resolved_internal: Dict[str, Any]) -> int:
        """Count total broken references"""
        return len(resolved_internal.get('broken_refs', []))