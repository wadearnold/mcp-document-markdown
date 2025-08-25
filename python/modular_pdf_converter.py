"""
Modular PDF to Markdown converter - main orchestrator
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import all processor modules
from processors.pdf_extractor import PDFExtractor
from processors.table_processor import TableProcessor  
from processors.chunking_engine import ChunkingEngine
from processors.concept_mapper import ConceptMapper
from processors.cross_referencer import CrossReferencer
from processors.summary_generator import SummaryGenerator

# Import utilities
from utils.token_counter import TokenCounter
from utils.text_utils import TextUtils
from utils.file_utils import FileUtils

class ModularPDFConverter:
    """
    Main orchestrator for modular PDF to Markdown conversion
    
    This class coordinates all the specialized processors to convert PDF documents
    into well-structured, LLM-optimized markdown with comprehensive analysis.
    """
    
    def __init__(self, pdf_path: str, output_dir: str, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the modular PDF converter
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory for all generated files
            options: Conversion options and settings
        """
        self.pdf_path = Path(pdf_path)
        base_output_dir = Path(output_dir)
        self.options = options or {}
        
        # Create a subdirectory based on the PDF filename
        pdf_folder_name = FileUtils.sanitize_folder_name(self.pdf_path.name)
        self.output_dir = base_output_dir / pdf_folder_name
        
        # Ensure output directory exists
        FileUtils.ensure_directory(self.output_dir)
        
        # Initialize core utilities
        self.token_counter = TokenCounter()
        
        # Initialize processors
        self.pdf_extractor = PDFExtractor(
            str(self.pdf_path), 
            str(self.output_dir),
            extract_images=self.options.get('extract_images', True)
        )
        
        self.table_processor = TableProcessor(str(self.output_dir), self.token_counter)
        self.chunking_engine = ChunkingEngine(str(self.output_dir), self.token_counter)
        self.concept_mapper = ConceptMapper(str(self.output_dir), self.token_counter)
        self.cross_referencer = CrossReferencer(str(self.output_dir))
        self.summary_generator = SummaryGenerator(str(self.output_dir), self.token_counter)
        
        # Conversion state
        self.conversion_results = {}
        self.processing_stats = {}
        
    def convert(self) -> Dict[str, Any]:
        """
        Main conversion method that orchestrates the entire process
        
        Returns:
            Complete conversion results with all generated files and analysis
        """
        print(f"Starting modular PDF conversion: {self.pdf_path.name}")
        start_time = datetime.now()
        
        try:
            # Step 1: Extract content from PDF
            print("Step 1: Extracting PDF content...")
            pdf_content = self.pdf_extractor.extract_all_content()
            self.processing_stats['pdf_extraction'] = {
                'pages': len(pdf_content.get('pages', [])),
                'images': len(pdf_content.get('images', [])),
                'tables': len(pdf_content.get('tables', [])),
                'characters': len(pdf_content.get('text', ''))
            }
            
            # Step 2: Structure content into sections
            print("Step 2: Structuring content into sections...")
            sections = self.structure_content_into_sections(pdf_content)
            self.processing_stats['sections'] = len(sections)
            
            # Step 3: Process tables
            print("Step 3: Processing tables...")
            if pdf_content.get('tables'):
                table_results = self.table_processor.process_all_tables(pdf_content['tables'])
                self.conversion_results['tables'] = table_results
            else:
                self.conversion_results['tables'] = {'processed_tables': [], 'table_files': []}
            
            # Step 4: Generate concept mapping
            print("Step 4: Generating concept mapping...")
            concept_results = self.concept_mapper.generate_concept_map_and_glossary(sections)
            self.conversion_results['concepts'] = concept_results
            
            # Step 5: Resolve cross-references
            print("Step 5: Resolving cross-references...")
            if self.options.get('resolve_cross_references', True):
                xref_results = self.cross_referencer.resolve_cross_references(
                    sections, 
                    concept_results
                )
                self.conversion_results['cross_references'] = xref_results
            else:
                self.conversion_results['cross_references'] = {}
            
            # Step 6: Generate summaries
            print("Step 6: Generating summaries...")
            if self.options.get('generate_summaries', True):
                summary_results = self.summary_generator.generate_all_summaries(
                    sections,
                    concept_results,
                    pdf_content.get('tables', [])
                )
                self.conversion_results['summaries'] = summary_results
            else:
                self.conversion_results['summaries'] = {}
            
            # Step 7: Create chunked versions
            print("Step 7: Creating optimized chunks...")
            if self.options.get('create_chunks', True):
                chunk_results = self.chunking_engine.process_sections_for_chunking(sections)
                self.conversion_results['chunks'] = {
                    'chunk_files': chunk_results,
                    'total_chunks': len(chunk_results)
                }
            else:
                self.conversion_results['chunks'] = {'chunk_files': [], 'total_chunks': 0}
            
            # Step 8: Generate main markdown files
            print("Step 8: Generating main markdown files...")
            markdown_files = self.generate_main_markdown_files(sections, pdf_content)
            self.conversion_results['markdown_files'] = markdown_files
            
            # Step 9: Create master index
            print("Step 9: Creating master index...")
            index_file = self.create_master_index()
            self.conversion_results['index_file'] = str(index_file)
            
            # Step 10: Generate metadata
            print("Step 10: Generating metadata...")
            metadata_file = self.create_conversion_metadata(start_time)
            self.conversion_results['metadata_file'] = str(metadata_file)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"✅ Conversion completed in {processing_time:.2f} seconds")
            print(f"📄 Generated {len(self.get_all_generated_files()):,} files total")
            
            # Final results
            final_results = {
                'success': True,
                'pdf_file': str(self.pdf_path),
                'output_directory': str(self.output_dir),
                'processing_time_seconds': processing_time,
                'conversion_results': self.conversion_results,
                'processing_stats': self.processing_stats,
                'generated_files': self.get_all_generated_files(),
                'file_count': len(self.get_all_generated_files())
            }
            
            return final_results
            
        except Exception as e:
            import traceback
            error_time = datetime.now()
            processing_time = (error_time - start_time).total_seconds()
            
            print(f"Conversion failed after {processing_time:.2f} seconds: {str(e)}")
            traceback.print_exc()
            
            return {
                'success': False,
                'pdf_file': str(self.pdf_path),
                'output_directory': str(self.output_dir),
                'processing_time_seconds': processing_time,
                'error': str(e),
                'error_type': type(e).__name__,
                'partial_results': self.conversion_results,
                'processing_stats': self.processing_stats
            }
    
    def structure_content_into_sections(self, pdf_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Structure the extracted PDF content into logical sections"""
        text = pdf_content.get('text', '')
        pages = pdf_content.get('pages', [])
        structure = pdf_content.get('structure', {})
        
        sections = []
        
        # If we have outline/bookmarks, use them for structure
        outline = structure.get('outline', [])
        if outline:
            sections = self.structure_by_outline(text, outline, pages)
        else:
            # Fallback to header-based structuring
            sections = self.structure_by_headers(text, pages)
        
        # If no clear structure found, create page-based sections
        if not sections or len(sections) < 2:
            sections = self.structure_by_pages(pages)
        
        # Add section metadata
        for i, section in enumerate(sections):
            section['section_id'] = i + 1
            section['token_count'] = self.token_counter.count_tokens(section.get('content', ''))
            section['section_type'] = self.classify_section_type(section)
        
        return sections
    
    def structure_by_outline(self, text: str, outline: List[Dict], pages: List[Dict]) -> List[Dict[str, Any]]:
        """Structure content using PDF outline/bookmarks"""
        sections = []
        
        for bookmark in outline:
            title = bookmark.get('title', 'Untitled Section')
            level = bookmark.get('level', 0)
            page_num = bookmark.get('page')
            
            # Extract content for this section
            # This is a simplified approach - in practice, you'd need more sophisticated
            # content extraction based on page ranges
            section_content = self.extract_section_content_by_page(pages, page_num)
            
            sections.append({
                'title': title,
                'content': section_content,
                'level': level,
                'page': page_num,
                'source': 'outline'
            })
        
        return sections
    
    def structure_by_headers(self, text: str, pages: List[Dict]) -> List[Dict[str, Any]]:
        """Structure content by detecting headers in text"""
        sections = []
        lines = text.split('\\n')
        
        current_section = {
            'title': 'Introduction',
            'content': '',
            'level': 1,
            'source': 'header_detection'
        }
        
        for line in lines:
            if TextUtils.is_header(line):
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                title = line.strip()
                level = TextUtils.determine_header_level(line)
                
                current_section = {
                    'title': title,
                    'content': '',
                    'level': level,
                    'source': 'header_detection'
                }
            else:
                current_section['content'] += line + '\\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def structure_by_pages(self, pages: List[Dict]) -> List[Dict[str, Any]]:
        """Fallback: create sections based on pages"""
        sections = []
        
        # Group pages into logical sections (every 2-3 pages)
        pages_per_section = 3
        
        for i in range(0, len(pages), pages_per_section):
            page_group = pages[i:i + pages_per_section]
            
            # Create section from page group
            section_title = f"Section {len(sections) + 1}"
            if len(page_group) == 1:
                section_title += f" (Page {page_group[0]['page_num']})"
            else:
                start_page = page_group[0]['page_num']
                end_page = page_group[-1]['page_num']
                section_title += f" (Pages {start_page}-{end_page})"
            
            content = '\\n\\n'.join(page['text'] for page in page_group)
            
            sections.append({
                'title': section_title,
                'content': content,
                'level': 1,
                'pages': [p['page_num'] for p in page_group],
                'source': 'page_grouping'
            })
        
        return sections
    
    def extract_section_content_by_page(self, pages: List[Dict], page_num: Optional[int]) -> str:
        """Extract content for a section based on page number"""
        if not page_num or not pages:
            return ""
        
        # Find the page
        for page in pages:
            if page.get('page_num') == page_num:
                return page.get('text', '')
        
        return ""
    
    def classify_section_type(self, section: Dict[str, Any]) -> str:
        """Classify the type of section based on content and title"""
        title = section.get('title', '').lower()
        content = section.get('content', '').lower()
        
        # Classification based on title keywords
        if any(term in title for term in ['introduction', 'overview', 'getting started']):
            return 'introduction'
        elif any(term in title for term in ['summary', 'conclusion', 'wrap up']):
            return 'summary'
        elif any(term in title for term in ['api', 'endpoint', 'method']):
            return 'api_endpoint'
        elif any(term in title for term in ['authentication', 'auth', 'login', 'security']):
            return 'authentication'
        elif any(term in title for term in ['example', 'tutorial', 'walkthrough']):
            return 'examples'
        elif any(term in title for term in ['error', 'troubleshooting', 'debug']):
            return 'error_handling'
        elif any(term in title for term in ['reference', 'appendix', 'glossary']):
            return 'reference'
        
        # Classification based on content patterns
        elif any(term in content for term in ['http get', 'http post', 'curl', 'endpoint']):
            return 'api_endpoint'
        elif content.count('```') >= 2:  # Has code blocks
            return 'code_example'
        elif any(term in content for term in ['table', '|']) and content.count('|') > 5:
            return 'data'
        
        return 'content'
    
    def generate_main_markdown_files(self, sections: List[Dict[str, Any]], 
                                   pdf_content: Dict[str, Any]) -> List[str]:
        """Generate the main markdown files for LLM agents"""
        generated_files = []
        
        # Generate structure overview (navigation and metadata for LLM agents)
        structured_md = self.create_structured_markdown(sections, pdf_content)
        structure_file = self.output_dir / "structure-overview.md"
        FileUtils.write_markdown(structured_md, structure_file)
        generated_files.append(str(structure_file))
        
        # Generate individual section files (optimized for LLM processing)
        sections_dir = self.output_dir / "sections"
        FileUtils.ensure_directory(sections_dir)
        
        for i, section in enumerate(sections):
            section_md = self.create_section_markdown(section, i + 1)
            safe_title = FileUtils.safe_filename(section.get('title', f'section-{i+1}'))
            
            # Check if section is too large (>20k tokens)
            token_count = self.token_counter.count_tokens(section_md)
            if token_count > 20000:
                # Split large section into multiple parts
                section_parts = self.split_large_section(section_md, section.get('title', f'Section {i+1}'))
                for part_idx, part_content in enumerate(section_parts):
                    part_file = sections_dir / f"{i+1:02d}-{safe_title}-part{part_idx+1:02d}.md"
                    FileUtils.write_markdown(part_content, part_file)
                    generated_files.append(str(part_file))
            else:
                # Section is manageable size
                section_file = sections_dir / f"{i+1:02d}-{safe_title}.md"
                FileUtils.write_markdown(section_md, section_file)
                generated_files.append(str(section_file))
        
        return generated_files
    
    def split_large_section(self, section_md: str, section_title: str) -> List[str]:
        """Split a large section into smaller, manageable parts"""
        # First check if section actually needs splitting
        total_tokens = self.token_counter.count_tokens(section_md)
        if total_tokens <= 20000:
            return [section_md]
        
        lines = section_md.split('\n')
        parts = []
        current_part = []
        current_tokens = 0
        target_tokens = 12000  # Target size per part (leave room for headers)
        
        # Keep the header in each part
        header_lines = []
        content_start = 0
        for i, line in enumerate(lines):
            if line.startswith('---'):
                content_start = i + 1
                break
            header_lines.append(line)
        
        # Calculate header token count once
        header_tokens = sum(self.token_counter.count_tokens(hl) for hl in header_lines)
        
        # Split content while preserving structure
        for i in range(content_start, len(lines)):
            line = lines[i]
            line_tokens = self.token_counter.count_tokens(line)
            
            # If adding this line would exceed target, start new part
            if current_tokens + line_tokens > target_tokens and current_part:
                # Finish current part
                part_header = header_lines + [f"\n**Part {len(parts)+1} of Section**\n---\n"]
                part_content = '\n'.join(part_header + current_part)
                parts.append(part_content)
                current_part = []
                current_tokens = header_tokens + 50  # Account for part header
            
            current_part.append(line)
            current_tokens += line_tokens
        
        # Add final part
        if current_part:
            part_header = header_lines + [f"\n**Part {len(parts)+1} of Section**\n---\n"] 
            part_content = '\n'.join(part_header + current_part)
            parts.append(part_content)
        
        return parts if parts else [section_md]
    
    def create_structured_markdown(self, sections: List[Dict[str, Any]], 
                                 pdf_content: Dict[str, Any]) -> str:
        """Create a structure overview document for LLM navigation"""
        metadata = pdf_content.get('metadata', {})
        stats = pdf_content.get('stats', {})
        
        content = f"""# {metadata.get('title', 'PDF Document')} - Structure Overview

**Document Type**: {self.processing_stats.get('document_type', 'Unknown')}  
**Converted**: {datetime.now().isoformat()}  
**Source**: {self.pdf_path.name}  
**Processing Method**: Modular PDF Converter  

## Document Statistics

- **Pages**: {stats.get('total_pages', 'Unknown')}
- **Sections**: {len(sections)}
- **Images**: {stats.get('total_images', 0)}
- **Tables**: {stats.get('total_tables', 0)}
- **Total Characters**: {stats.get('total_chars', 0):,}

## Table of Contents

"""
        
        # Add table of contents
        for i, section in enumerate(sections):
            title = section.get('title', 'Untitled Section')
            section_type = section.get('section_type', 'content')
            token_count = section.get('token_count', 0)
            
            content += f"{i+1}. [{title}](#section-{i+1}) ({section_type}, {token_count} tokens)\\n"
        
        content += "\\n---\\n\\n"
        
        # Add sections with navigation metadata only (no full content)
        for i, section in enumerate(sections):
            title = section.get('title', 'Untitled Section')
            section_content = section.get('content', '')
            section_type = section.get('section_type', 'content')
            token_count = section.get('token_count', 0)
            level = section.get('level', 1)
            
            # Create preview - first 200 chars of content
            content_preview = section_content[:200].strip()
            if len(section_content) > 200:
                content_preview += "..."
            
            safe_title = FileUtils.safe_filename(title)
            section_file = f"sections/{i+1:02d}-{safe_title}.md"
            
            content += f"## {i+1}. {title} {{#section-{i+1}}}\\n\\n"
            content += f"**Section Type**: {section_type}  \\n"
            content += f"**Token Count**: {token_count}  \\n"
            content += f"**Level**: {level}  \\n"
            content += f"**File**: `{section_file}`  \\n\\n"
            content += f"**Preview**: {content_preview}\\n\\n"
            content += f"[📖 Read Full Section]({section_file})\\n\\n---\\n\\n"
        
        return content
    
    def create_section_markdown(self, section: Dict[str, Any], section_num: int) -> str:
        """Create markdown for an individual section"""
        title = section.get('title', f'Section {section_num}')
        content = section.get('content', '')
        section_type = section.get('section_type', 'content')
        token_count = section.get('token_count', 0)
        level = section.get('level', 1)
        pages = section.get('pages', [])
        
        markdown = f"""# {title}

**Section**: {section_num}  
**Type**: {section_type}  
**Level**: {level}  
**Token Count**: {token_count}  
**Generated**: {datetime.now().isoformat()}
"""
        
        if pages:
            markdown += f"**Source Pages**: {', '.join(map(str, pages))}  \\n"
        
        markdown += f"""
---

{content}
"""
        
        return markdown
    
    def create_master_index(self) -> Path:
        """Create a master index of all generated files"""
        index_content = f"""# PDF Conversion Results

**Source**: {self.pdf_path.name}  
**Converted**: {datetime.now().isoformat()}  
**Output Directory**: {self.output_dir.name}  
**Processing Time**: {self.processing_stats.get('processing_time', 'Unknown')}

## Generated Files Summary

"""
        
        # Count files by category
        all_files = self.get_all_generated_files()
        file_categories = self.categorize_generated_files(all_files)
        
        for category, files in file_categories.items():
            if files:
                index_content += f"### {category.replace('_', ' ').title()} ({len(files)} files)\\n\\n"
                # Only list first few files to keep README manageable
                if len(files) <= 10:
                    for file_path in files:
                        file_obj = Path(file_path)
                        relative_path = file_obj.relative_to(self.output_dir)
                        index_content += f"- [{file_obj.name}]({relative_path})\\n"
                else:
                    # Show first 5 and last 3 files
                    for file_path in files[:5]:
                        file_obj = Path(file_path)
                        relative_path = file_obj.relative_to(self.output_dir)
                        index_content += f"- [{file_obj.name}]({relative_path})\\n"
                    index_content += f"- ... ({len(files)-8} more files)\\n"
                    for file_path in files[-3:]:
                        file_obj = Path(file_path)
                        relative_path = file_obj.relative_to(self.output_dir)
                        index_content += f"- [{file_obj.name}]({relative_path})\\n"
                index_content += "\\n"
        
        # Add processing statistics
        index_content += "## Processing Statistics\\n\\n"
        for stat_name, stat_value in self.processing_stats.items():
            if isinstance(stat_value, dict):
                index_content += f"**{stat_name.replace('_', ' ').title()}**:\\n"
                for sub_stat, sub_value in stat_value.items():
                    index_content += f"- {sub_stat}: {sub_value}\\n"
            else:
                index_content += f"- **{stat_name.replace('_', ' ').title()}**: {stat_value}\\n"
        
        index_content += """

## Usage Guide

### Quick Start
1. Start with `structure-overview.md` for navigation and metadata
2. Check `summaries/README.md` for different summary types
3. Use `chunked/` directory for LLM-optimized content

### For Developers
- Use `concepts/` for technical terms and definitions
- Check `references/` for cross-references and links
- Use `tables/` for structured data analysis

### For LLM Integration
- Use files in `chunked/` directory based on your model's context window
- Start with `summaries/executive-summary.md` for quick understanding
- Reference `concepts/glossary.md` for key terminology

"""
        
        index_file = self.output_dir / "README.md"
        FileUtils.write_markdown(index_content, index_file)
        return index_file
    
    def create_conversion_metadata(self, start_time: datetime) -> Path:
        """Create detailed metadata about the conversion process"""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        metadata = {
            'conversion_info': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'processing_time_seconds': processing_time,
                'converter_version': '2.0.0-modular',
                'python_version': sys.version
            },
            'source_document': {
                'pdf_path': str(self.pdf_path),
                'file_size_bytes': self.pdf_path.stat().st_size,
                'file_name': self.pdf_path.name
            },
            'output_info': {
                'output_directory': str(self.output_dir),
                'total_files_generated': len(self.get_all_generated_files()),
                'file_categories': self.categorize_generated_files(self.get_all_generated_files())
            },
            'processing_options': self.options,
            'processing_stats': self.processing_stats,
            'conversion_results_summary': {
                'sections_created': self.processing_stats.get('sections', 0),
                'tables_processed': len(self.conversion_results.get('tables', [])) if isinstance(self.conversion_results.get('tables', []), list) else len(self.conversion_results.get('tables', {}).get('processed_tables', [])),
                'concepts_extracted': len(self.conversion_results.get('concepts', [])) if isinstance(self.conversion_results.get('concepts', []), list) else len(self.conversion_results.get('concepts', {}).get('terms', {})),
                'summaries_generated': len(self.conversion_results.get('summaries', [])) if isinstance(self.conversion_results.get('summaries', []), list) else len(self.conversion_results.get('summaries', {}).get('summaries', {})),
                'chunks_created': len(self.conversion_results.get('chunks', [])) if isinstance(self.conversion_results.get('chunks', []), list) else self.conversion_results.get('chunks', {}).get('total_chunks', 0)
            }
        }
        
        metadata_file = self.output_dir / "conversion-metadata.json"
        FileUtils.write_json(metadata, metadata_file)
        return metadata_file
    
    def get_all_generated_files(self) -> List[str]:
        """Get a list of all generated files"""
        all_files = []
        
        # Add markdown files
        all_files.extend(self.conversion_results.get('markdown_files', []))
        
        # Add table files
        table_results = self.conversion_results.get('tables', [])
        if isinstance(table_results, list):
            all_files.extend(table_results)
        elif isinstance(table_results, dict):
            all_files.extend(table_results.get('table_files', []))
        
        # Add concept files
        concept_results = self.conversion_results.get('concepts', [])
        if isinstance(concept_results, list):
            all_files.extend(concept_results)
        elif isinstance(concept_results, dict):
            all_files.extend(concept_results.get('concept_files', []))
        
        # Add cross-reference files
        xref_results = self.conversion_results.get('cross_references', [])
        if isinstance(xref_results, list):
            all_files.extend(xref_results)
        elif isinstance(xref_results, dict):
            all_files.extend(xref_results.get('reference_files', []))
        
        # Add summary files
        summary_results = self.conversion_results.get('summaries', [])
        if isinstance(summary_results, list):
            all_files.extend(summary_results)
        elif isinstance(summary_results, dict):
            all_files.extend(summary_results.get('summary_files', []))
            if summary_results.get('index_file'):
                all_files.append(summary_results['index_file'])
        
        # Add chunk files
        chunk_results = self.conversion_results.get('chunks', [])
        if isinstance(chunk_results, list):
            all_files.extend(chunk_results)
        elif isinstance(chunk_results, dict):
            all_files.extend(chunk_results.get('chunk_files', []))
        
        # Add metadata files
        if self.conversion_results.get('index_file'):
            all_files.append(self.conversion_results['index_file'])
        if self.conversion_results.get('metadata_file'):
            all_files.append(self.conversion_results['metadata_file'])
        
        return all_files
    
    def categorize_generated_files(self, file_list: List[str]) -> Dict[str, List[str]]:
        """Categorize generated files by type"""
        categories = {
            'main_documents': [],
            'sections': [],
            'summaries': [],
            'concepts': [],
            'tables': [],
            'chunks': [],
            'references': [],
            'metadata': []
        }
        
        for file_path in file_list:
            file_obj = Path(file_path)
            parent_dir = file_obj.parent.name
            file_name = file_obj.name
            
            if parent_dir == 'summaries':
                categories['summaries'].append(file_path)
            elif parent_dir == 'concepts':
                categories['concepts'].append(file_path)
            elif parent_dir == 'tables':
                categories['tables'].append(file_path)
            elif parent_dir == 'chunked':
                categories['chunks'].append(file_path)
            elif parent_dir == 'references':
                categories['references'].append(file_path)
            elif parent_dir == 'sections':
                categories['sections'].append(file_path)
            elif file_name.endswith('-metadata.json') or file_name == 'README.md':
                categories['metadata'].append(file_path)
            else:
                categories['main_documents'].append(file_path)
        
        return categories


def main():
    """Command-line interface for the modular PDF converter"""
    if len(sys.argv) < 3:
        print("Usage: python modular_pdf_converter.py <pdf_path> <output_dir> [options_json]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Parse options if provided
    options = {}
    if len(sys.argv) > 3:
        try:
            options = json.loads(sys.argv[3])
        except json.JSONDecodeError:
            print("Warning: Invalid JSON options provided, using defaults")
    
    # Create converter and run
    converter = ModularPDFConverter(pdf_path, output_dir, options)
    results = converter.convert()
    
    # Output results
    if results['success']:
        print("\\n=== Conversion Successful ===")
        print(f"Generated {results['file_count']} files in {results['processing_time_seconds']:.2f} seconds")
        print(f"Output directory: {results['output_directory']}")
    else:
        print("\\n=== Conversion Failed ===")
        print(f"Error: {results['error']}")
        print(f"Error type: {results['error_type']}")
    
    # Output full results as JSON for programmatic use
    print("\\n=== CONVERSION_RESULTS_JSON ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()