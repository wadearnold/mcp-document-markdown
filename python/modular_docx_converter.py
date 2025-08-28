#!/usr/bin/env python3
"""
Modular Word Document to Markdown Converter
Converts Microsoft Word documents to AI-optimized markdown documentation
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Word extractor
from processors.docx_extractor import DocxExtractor

# Import existing processors for post-processing
# Removed table processor for LLM-optimized embedded approach
# Removed obsolete processors for LLM-optimized structure

# Import utilities
from utils.token_counter import TokenCounter
from utils.text_utils import TextUtils
from utils.file_utils import FileUtils


class ModularDocxConverter:
    """Orchestrates the conversion of Word documents to structured markdown"""
    
    def __init__(self, docx_path: str, output_dir: str, options: Optional[Dict] = None):
        """
        Initialize the Word document converter
        
        Args:
            docx_path: Path to the Word document
            output_dir: Directory to save converted files
            options: Conversion options
        """
        self.docx_path = Path(docx_path)
        self.output_dir = Path(output_dir)
        
        # Default options
        self.options = {
            'split_by_chapters': True,
            'preserve_tables': True,
            'extract_images': True,
            'generate_summaries': True,
            'generate_concept_map': True,
            'resolve_cross_references': True,
            'structured_tables': True,
            'chunk_size_optimization': True,
        }
        
        if options:
            self.options.update(options)
        
        # Initialize components
        self.token_counter = TokenCounter()
        self.docx_extractor = DocxExtractor()
        # Skip processor initialization - using embedded approach for LLM optimization
        
        # Tracking
        self.generated_files = []
        self.processing_stats = {}
    
    def convert(self) -> Dict[str, Any]:
        """
        Main conversion pipeline for Word documents
        
        Returns:
            Dictionary with conversion results
        """
        start_time = time.time()
        
        try:
            # Create sanitized output folder based on Word file name
            docx_folder_name = FileUtils.sanitize_folder_name(self.docx_path.name)
            self.output_dir = self.output_dir / docx_folder_name
            FileUtils.ensure_directory(self.output_dir)
            
            # Skip processor initialization - using embedded approach for LLM optimization
            
            print(f"\n🚀 Starting Word document conversion: {self.docx_path.name}")
            print(f"📁 Output directory: {self.output_dir}")
            
            # Step 1: Extract content from Word document
            print("\n📄 Step 1: Extracting Word document content...")
            extraction_result = self.docx_extractor.extract_from_file(str(self.docx_path))
            
            if not extraction_result['success']:
                raise Exception(f"Failed to extract Word document: {extraction_result.get('error')}")
            
            # Store stats
            self.processing_stats['docx_extraction'] = extraction_result['stats']
            
            # Step 2: Structure content into sections
            sections = extraction_result['sections']
            
            # Step 3: Generate LLM-optimized markdown files
            print("\n📝 Step 2: Generating LLM-optimized markdown files...")
            markdown_files = self.generate_main_markdown_files(sections, extraction_result)
            self.generated_files.extend(markdown_files)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Store final stats
            self.processing_stats['sections'] = len(sections)
            self.processing_stats['files_created'] = len(self.generated_files)
            self.processing_stats['processing_time'] = processing_time
            
            # Success result
            result = {
                'success': True,
                'output_dir': str(self.output_dir),
                'generated_files': self.generated_files,
                'file_count': len(self.generated_files),
                'processing_stats': self.processing_stats,
                'processing_time_seconds': processing_time
            }
            
            print(f"\n✅ Conversion complete! Generated {len(self.generated_files)} files in {processing_time:.1f}s")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Conversion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_seconds': time.time() - start_time
            }
    
    def process_word_tables(self, tables: List[Dict[str, Any]]) -> List[str]:
        """Process tables extracted from Word document"""
        created_files = []
        tables_dir = self.output_dir / "tables"
        FileUtils.ensure_directory(tables_dir)
        
        for i, table_info in enumerate(tables, 1):
            # Save markdown version
            table_file = tables_dir / f"table-{i:03d}.md"
            table_content = f"# Table {i}\n\n"
            table_content += f"**Dimensions**: {table_info['rows']} rows × {table_info['columns']} columns\n\n"
            table_content += table_info['markdown']
            
            FileUtils.write_markdown(table_content, table_file)
            created_files.append(str(table_file))
            
            # Create structured JSON if requested
            if self.options['structured_tables']:
                json_data = self.table_processor.markdown_to_json(table_info['markdown'])
                if json_data:
                    json_file = tables_dir / f"table-{i:03d}.json"
                    FileUtils.write_json(json_data, json_file)
                    created_files.append(str(json_file))
        
        # Create table index
        if tables:
            index_content = f"# Tables Index\n\n"
            index_content += f"Total tables found: {len(tables)}\n\n"
            
            for i, table_info in enumerate(tables, 1):
                index_content += f"- [Table {i}](table-{i:03d}.md) - "
                index_content += f"{table_info['rows']} rows × {table_info['columns']} columns\n"
            
            index_file = tables_dir / "tables-index.md"
            FileUtils.write_markdown(index_content, index_file)
            created_files.append(str(index_file))
        
        return created_files
    
    def process_word_images(self, images: List[Dict[str, str]]) -> List[str]:
        """Process image references from Word document"""
        created_files = []
        images_dir = self.output_dir / "images"
        FileUtils.ensure_directory(images_dir)
        
        # Create image catalog
        catalog_content = f"# Image Catalog\n\n"
        catalog_content += f"Total images referenced: {len(images)}\n\n"
        
        for i, image_info in enumerate(images, 1):
            catalog_content += f"## Image {i}\n"
            catalog_content += f"- **Alt Text**: {image_info.get('alt_text', 'No description')}\n"
            catalog_content += f"- **Reference**: {image_info.get('url', 'Unknown')}\n\n"
        
        catalog_file = images_dir / "image-catalog.md"
        FileUtils.write_markdown(catalog_content, catalog_file)
        created_files.append(str(catalog_file))
        
        return created_files
    
    def create_word_sections(self, sections: List[Dict[str, Any]]) -> List[str]:
        """Create individual section files from Word content"""
        created_files = []
        sections_dir = self.output_dir / "sections"
        FileUtils.ensure_directory(sections_dir)
        
        for i, section in enumerate(sections):
            safe_title = FileUtils.safe_filename(section.get('title', f'Section {i+1}'))
            section_file = sections_dir / f"{i+1:02d}-{safe_title}.md"
            
            # Check token count and split if needed
            content = section['content']
            token_count = self.token_counter.count_tokens(content)
            
            if token_count > 20000:
                # Split large sections
                print(f"  ⚠️ Section '{section['title']}' has {token_count:,} tokens - splitting...")
                section_parts = self.split_large_section(content, section.get('title'))
                
                for part_idx, part_content in enumerate(section_parts, 1):
                    part_file = sections_dir / f"{i+1:02d}-{safe_title}-part{part_idx:02d}.md"
                    section_md = self.format_section_content(section, part_content, part_idx, len(section_parts))
                    FileUtils.write_markdown(section_md, part_file)
                    created_files.append(str(part_file))
            else:
                # Normal single file
                section_md = self.format_section_content(section, content)
                FileUtils.write_markdown(section_md, section_file)
                created_files.append(str(section_file))
        
        return created_files
    
    def format_section_content(self, section: Dict[str, Any], content: str, 
                              part_num: Optional[int] = None, total_parts: Optional[int] = None) -> str:
        """Format section content with metadata"""
        title = section.get('title', 'Untitled Section')
        
        if part_num and total_parts:
            header = f"# {title} (Part {part_num}/{total_parts})\n\n"
        else:
            header = f"# {title}\n\n"
        
        # Add metadata
        header += f"**Section Type**: {section.get('section_type', 'content')}  \n"
        header += f"**Level**: {section.get('level', 1)}  \n"
        
        token_count = self.token_counter.count_tokens(content)
        header += f"**Tokens**: {token_count:,}  \n"
        header += f"**Estimated Reading Time**: {max(1, token_count // 250)} minutes  \n\n"
        header += "---\n\n"
        
        return header + content
    
    def split_large_section(self, content: str, title: str) -> List[str]:
        """Split large sections into manageable parts"""
        # Use the chunking engine's semantic splitting
        return self.chunking_engine.split_content_semantically(content, title)
    
    def create_word_navigation(self, sections: List[Dict[str, Any]], extraction_result: Dict[str, Any]) -> List[str]:
        """Create navigation files for Word document"""
        created_files = []
        
        # Create structure overview (navigation only)
        structure_content = f"# Document Structure Overview\n\n"
        structure_content += f"**Source Document**: {self.docx_path.name}  \n"
        structure_content += f"**Converted**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n"
        structure_content += f"**Total Sections**: {len(sections)}  \n"
        
        if extraction_result['stats']:
            stats = extraction_result['stats']
            structure_content += f"**Total Words**: {stats.get('total_words', 0):,}  \n"
            structure_content += f"**Total Tables**: {stats.get('total_tables', 0)}  \n"
            structure_content += f"**Total Images**: {stats.get('total_images', 0)}  \n"
        
        structure_content += "\n---\n\n"
        structure_content += "## 📑 Document Sections\n\n"
        
        sections_dir = Path("sections")
        for i, section in enumerate(sections):
            safe_title = FileUtils.safe_filename(section.get('title', f'Section {i+1}'))
            section_file = sections_dir / f"{i+1:02d}-{safe_title}.md"
            
            # Add navigation entry with preview
            level_indicator = "  " * (section.get('level', 1) - 1)
            structure_content += f"{level_indicator}- **[{section['title']}]({section_file})**\n"
            
            # Add brief preview
            content_preview = section['content'][:200].strip()
            if len(section['content']) > 200:
                content_preview += "..."
            
            structure_content += f"{level_indicator}  *Preview*: {content_preview}\n\n"
        
        # Add quick links section
        structure_content += "\n---\n\n## 🔗 Quick Links\n\n"
        structure_content += "- 📝 [Executive Summary](summaries/executive-summary.md)\n"
        structure_content += "- 📚 [Detailed Summary](summaries/detailed-summary.md)\n"
        structure_content += "- 🧠 [Concepts & Glossary](concepts/glossary.md)\n"
        structure_content += "- 📊 [Tables Index](tables/tables-index.md)\n"
        structure_content += "- 🖼️ [Image Catalog](images/image-catalog.md)\n"
        structure_content += "- 🔄 [Chunked Content](chunked/chunk-manifest.md)\n"
        
        structure_file = self.output_dir / "structure-overview.md"
        FileUtils.write_markdown(structure_content, structure_file)
        created_files.append(str(structure_file))
        
        # Create main README
        readme_content = f"# {self.docx_path.stem} - Converted Documentation\n\n"
        readme_content += f"This directory contains the AI-optimized markdown conversion of **{self.docx_path.name}**.\n\n"
        readme_content += "## 📚 How to Use This Documentation\n\n"
        readme_content += "1. **Start with the overview**: Open [structure-overview.md](structure-overview.md) for document navigation\n"
        readme_content += "2. **Quick understanding**: Read [executive-summary.md](summaries/executive-summary.md)\n"
        readme_content += "3. **Deep dive**: Explore individual sections in the `sections/` directory\n"
        readme_content += "4. **Data analysis**: Check `tables/` for structured data\n"
        readme_content += "5. **LLM usage**: Use `chunked/` files optimized for your model's context window\n\n"
        
        readme_content += "## 📁 Directory Structure\n\n"
        readme_content += "```\n"
        readme_content += f"{self.output_dir.name}/\n"
        readme_content += "├── structure-overview.md  # Document navigation\n"
        readme_content += "├── README.md             # This file\n"
        readme_content += "├── sections/             # Individual content sections\n"
        readme_content += "├── summaries/            # Multi-level summaries\n"
        readme_content += "├── concepts/             # Glossary and concept maps\n"
        readme_content += "├── tables/               # Extracted tables\n"
        readme_content += "├── images/               # Image references\n"
        readme_content += "└── chunked/              # LLM-optimized chunks\n"
        readme_content += "```\n\n"
        
        readme_content += "## 📊 Conversion Statistics\n\n"
        if extraction_result['stats']:
            stats = extraction_result['stats']
            readme_content += f"- **Total Words**: {stats.get('total_words', 0):,}\n"
            readme_content += f"- **Total Sections**: {stats.get('total_sections', 0)}\n"
            readme_content += f"- **Total Tables**: {stats.get('total_tables', 0)}\n"
            readme_content += f"- **Total Images**: {stats.get('total_images', 0)}\n"
        
        readme_content += f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        readme_file = self.output_dir / "README.md"
        FileUtils.write_markdown(readme_content, readme_file)
        created_files.append(str(readme_file))
        
        return created_files


def main():
    """Command-line interface for the Word document converter"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python modular_docx_converter.py <docx_file> [output_dir]")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./docs"
    
    # Run conversion
    converter = ModularDocxConverter(docx_path, output_dir)
    result = converter.convert()
    
    if result['success']:
        print(f"\n✅ Success! Files saved to: {result['output_dir']}")
    else:
        print(f"\n❌ Conversion failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()