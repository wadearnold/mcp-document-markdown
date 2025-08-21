"""
Smart chunking engine for optimal LLM context window utilization
"""
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re

from ..utils.token_counter import TokenCounter
from ..utils.text_utils import TextUtils
from ..utils.file_utils import FileUtils

class ChunkingEngine:
    """Handles smart chunking of content for different LLM context windows"""
    
    def __init__(self, output_dir: str, token_counter: TokenCounter):
        """
        Initialize chunking engine
        
        Args:
            output_dir: Output directory for chunked content
            token_counter: Token counter for optimization
        """
        self.output_dir = Path(output_dir)
        self.token_counter = token_counter
        self.chunked_dir = self.output_dir / "chunked"
        FileUtils.ensure_directory(self.chunked_dir)
        
        # Target token limits for different models
        self.chunk_sizes = {
            'small': 3500,   # GPT-3.5 (4K context)
            'medium': 7500,  # GPT-4 (8K context)  
            'large': 30000,  # GPT-4-32K (32K context)
            'xlarge': 95000  # Claude-2 (100K context)
        }
    
    def process_sections_for_chunking(self, sections: List[Dict[str, Any]]) -> List[str]:
        """
        Process sections and create optimally-sized chunks
        
        Args:
            sections: List of document sections
            
        Returns:
            List of paths to created chunk files
        """
        if not sections:
            return []
        
        # Analyze sections for chunking strategy
        chunk_plan = self.analyze_sections_for_chunking(sections)
        
        # Create chunks based on the plan
        created_files = []
        chunk_metadata = []
        
        for plan_item in chunk_plan:
            chunk_files = self.create_chunks_for_section(plan_item)
            created_files.extend(chunk_files)
            chunk_metadata.append({
                'section_id': plan_item['section_id'],
                'section_title': plan_item['title'],
                'original_tokens': plan_item['tokens'],
                'chunks_created': len(chunk_files),
                'chunk_files': [Path(f).name for f in chunk_files]
            })
        
        # Create chunk manifest
        manifest_file = self.create_chunk_manifest(chunk_metadata)
        created_files.append(str(manifest_file))
        
        return created_files
    
    def analyze_sections_for_chunking(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze sections to determine optimal chunking strategy"""
        chunk_plan = []
        
        for i, section in enumerate(sections):
            content = section.get('content', '')
            title = section.get('title', f'Section {i+1}')
            section_type = section.get('section_type', 'content')
            
            token_count = self.token_counter.count_tokens(content)
            
            plan_item = {
                'section_id': i + 1,
                'title': title,
                'content': content,
                'tokens': token_count,
                'section_type': section_type,
                'chunking_strategy': self.determine_chunking_strategy(token_count, section_type),
                'priority': self.get_section_priority(section_type)
            }
            
            chunk_plan.append(plan_item)
        
        # Sort by priority for optimal processing order
        chunk_plan.sort(key=lambda x: x['priority'], reverse=True)
        
        return chunk_plan
    
    def determine_chunking_strategy(self, token_count: int, section_type: str) -> Dict[str, Any]:
        """Determine the best chunking strategy for a section"""
        strategy = {
            'needs_chunking': token_count > self.chunk_sizes['small'],
            'recommended_sizes': [],
            'approach': 'preserve_context'
        }
        
        # Determine which chunk sizes to create
        for size_name, size_limit in self.chunk_sizes.items():
            if token_count <= size_limit:
                strategy['recommended_sizes'].append(size_name)
        
        # If content is too large for any single chunk
        if token_count > self.chunk_sizes['xlarge']:
            strategy['approach'] = 'semantic_split'
            strategy['recommended_sizes'] = ['small', 'medium', 'large']
        
        # Special handling for different section types
        if section_type in ['api_endpoint', 'code_example']:
            strategy['approach'] = 'preserve_structure'
        elif section_type in ['table', 'data']:
            strategy['approach'] = 'preserve_rows'
        
        return strategy
    
    def get_section_priority(self, section_type: str) -> int:
        """Get processing priority for section type"""
        priority_map = {
            'introduction': 10,
            'summary': 10,
            'authentication': 9,
            'api_endpoint': 8,
            'error_handling': 7,
            'examples': 6,
            'reference': 5,
            'appendix': 3,
            'content': 4
        }
        return priority_map.get(section_type, 4)
    
    def create_chunks_for_section(self, plan_item: Dict[str, Any]) -> List[str]:
        """Create chunk files for a section based on its plan"""
        created_files = []
        section_id = plan_item['section_id']
        title = plan_item['title']
        content = plan_item['content']
        strategy = plan_item['chunking_strategy']
        
        if not strategy['needs_chunking']:
            # Section fits in all chunk sizes - create single file for each size
            for size_name in strategy['recommended_sizes']:
                chunk_file = self.create_single_chunk_file(
                    section_id, title, content, size_name, plan_item
                )
                created_files.append(str(chunk_file))
        else:
            # Section needs splitting
            if strategy['approach'] == 'semantic_split':
                chunks = self.split_content_semantically(content, title)
            elif strategy['approach'] == 'preserve_structure':
                chunks = self.split_preserving_structure(content, title)
            elif strategy['approach'] == 'preserve_rows':
                chunks = self.split_preserving_rows(content, title)
            else:
                chunks = self.split_content_by_tokens(content, title)
            
            # Create files for each chunk and size combination
            for chunk_idx, chunk_content in enumerate(chunks, 1):
                for size_name in strategy['recommended_sizes']:
                    if self.token_counter.count_tokens(chunk_content) <= self.chunk_sizes[size_name]:
                        chunk_file = self.create_chunk_file(
                            section_id, title, chunk_content, size_name, 
                            chunk_idx, len(chunks), plan_item
                        )
                        created_files.append(str(chunk_file))
        
        return created_files
    
    def split_content_semantically(self, content: str, title: str) -> List[str]:
        """Split content at semantic boundaries"""
        chunks = []
        
        # Split by headers first
        parts = re.split(r'\n(#{1,6}\s+.+)', content)
        current_chunk = ""
        
        for part in parts:
            if not part.strip():
                continue
            
            # Check if adding this part would exceed chunk limit
            potential_chunk = current_chunk + "\n\n" + part
            if (current_chunk and 
                self.token_counter.count_tokens(potential_chunk) > self.chunk_sizes['medium']):
                # Save current chunk and start new one
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                current_chunk = potential_chunk if not current_chunk else potential_chunk
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    def split_preserving_structure(self, content: str, title: str) -> List[str]:
        """Split content while preserving code/API structure"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        in_code_block = False
        
        for line in lines:
            # Track code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
            
            current_chunk.append(line)
            
            # Check if we should split (but not inside code blocks)
            if not in_code_block:
                chunk_content = '\n'.join(current_chunk)
                if (len(current_chunk) > 10 and 
                    self.token_counter.count_tokens(chunk_content) > self.chunk_sizes['medium']):
                    
                    # Save chunk and start new one
                    chunks.append(chunk_content)
                    current_chunk = []
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [content]
    
    def split_preserving_rows(self, content: str, title: str) -> List[str]:
        """Split content while preserving table rows"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        in_table = False
        
        for line in lines:
            # Detect table boundaries
            if TextUtils.is_table_row(line):
                in_table = True
            elif in_table and not line.strip():
                in_table = False
            
            current_chunk.append(line)
            
            # Check if we should split (but not inside tables)
            if not in_table and len(current_chunk) > 5:
                chunk_content = '\n'.join(current_chunk)
                if self.token_counter.count_tokens(chunk_content) > self.chunk_sizes['medium']:
                    chunks.append(chunk_content)
                    current_chunk = []
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [content]
    
    def split_content_by_tokens(self, content: str, title: str) -> List[str]:
        """Split content by token count (fallback method)"""
        chunks = []
        sentences = TextUtils.split_into_sentences(content)
        current_chunk = ""
        
        for sentence in sentences:
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if self.token_counter.count_tokens(potential_chunk) > self.chunk_sizes['medium']:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence too long - keep it anyway
                    chunks.append(sentence)
                    current_chunk = ""
            else:
                current_chunk = potential_chunk
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    def create_single_chunk_file(self, section_id: int, title: str, content: str, 
                                size_name: str, plan_item: Dict[str, Any]) -> Path:
        """Create a single chunk file for content that doesn't need splitting"""
        safe_title = FileUtils.safe_filename(title)
        filename = f"{section_id:02d}-{safe_title}-{size_name}.md"
        
        chunk_content = self.format_chunk_content(
            title, content, size_name, 1, 1, plan_item
        )
        
        chunk_file = self.chunked_dir / filename
        FileUtils.write_markdown(chunk_content, chunk_file)
        return chunk_file
    
    def create_chunk_file(self, section_id: int, title: str, content: str, 
                         size_name: str, chunk_num: int, total_chunks: int,
                         plan_item: Dict[str, Any]) -> Path:
        """Create a chunk file with metadata"""
        safe_title = FileUtils.safe_filename(title)
        filename = f"{section_id:02d}-{safe_title}-chunk-{chunk_num}-{size_name}.md"
        
        chunk_content = self.format_chunk_content(
            title, content, size_name, chunk_num, total_chunks, plan_item
        )
        
        chunk_file = self.chunked_dir / filename
        FileUtils.write_markdown(chunk_content, chunk_file)
        return chunk_file
    
    def format_chunk_content(self, title: str, content: str, size_name: str,
                           chunk_num: int, total_chunks: int, 
                           plan_item: Dict[str, Any]) -> str:
        """Format chunk content with metadata header"""
        token_count = self.token_counter.count_tokens(content)
        model_rec = self.token_counter.recommend_model_for_tokens(token_count)
        
        header = f"""# {title}

**Chunk**: {chunk_num} of {total_chunks}  
**Size**: {size_name} ({token_count} tokens)  
**Section Type**: {plan_item['section_type']}  
**Processing Priority**: {plan_item['priority']}  
**Recommended Model**: {model_rec}  
**Generated**: {datetime.now().isoformat()}

---

"""
        
        # Add processing guidance
        guidance = self.get_processing_guidance(size_name, plan_item['section_type'], token_count)
        if guidance:
            header += f"""## Processing Guidance

{chr(10).join(f"- {note}" for note in guidance)}

---

"""
        
        return header + content
    
    def get_processing_guidance(self, size_name: str, section_type: str, token_count: int) -> List[str]:
        """Get processing guidance for chunks"""
        guidance = []
        
        # Size-based guidance
        if size_name == 'small':
            guidance.append("Optimized for GPT-3.5 - good for quick analysis and summaries")
        elif size_name == 'medium':
            guidance.append("Optimized for GPT-4 - suitable for detailed analysis")
        elif size_name == 'large':
            guidance.append("Optimized for GPT-4-32K - can handle complex analysis")
        elif size_name == 'xlarge':
            guidance.append("Optimized for Claude-2 - ideal for comprehensive analysis")
        
        # Section type guidance
        if section_type == 'api_endpoint':
            guidance.append("Contains API documentation - focus on endpoints, parameters, examples")
        elif section_type == 'authentication':
            guidance.append("Contains authentication info - critical for API integration")
        elif section_type == 'code_example':
            guidance.append("Contains code examples - good for implementation guidance")
        elif section_type == 'error_handling':
            guidance.append("Contains error information - useful for troubleshooting")
        
        # Token-based guidance
        if token_count < 1000:
            guidance.append("Concise content - suitable for direct inclusion in prompts")
        elif token_count > 5000:
            guidance.append("Substantial content - consider summarizing key points first")
        
        return guidance
    
    def create_chunk_manifest(self, chunk_metadata: List[Dict[str, Any]]) -> Path:
        """Create a manifest file describing all chunks"""
        total_chunks = sum(item['chunks_created'] for item in chunk_metadata)
        total_sections = len(chunk_metadata)
        
        manifest_content = f"""# Chunk Manifest

**Generated**: {datetime.now().isoformat()}  
**Total Sections**: {total_sections}  
**Total Chunks**: {total_chunks}  

## Chunking Summary

| Section | Title | Original Tokens | Chunks Created |
|---------|-------|-----------------|----------------|
"""
        
        for item in chunk_metadata:
            manifest_content += f"| {item['section_id']} | {item['section_title'][:30]}... | "
            manifest_content += f"{item['original_tokens']} | {item['chunks_created']} |\n"
        
        manifest_content += f"""

## Usage Guide

### Chunk Size Guide
- **small** (≤3.5K tokens): GPT-3.5 compatible - fast, cost-effective
- **medium** (≤7.5K tokens): GPT-4 compatible - balanced performance
- **large** (≤30K tokens): GPT-4-32K compatible - detailed analysis
- **xlarge** (≤95K tokens): Claude-2 compatible - comprehensive analysis

### Processing Strategy
1. **Start with small chunks** for initial understanding and summaries
2. **Use medium chunks** for most analysis tasks
3. **Use large chunks** when you need more context
4. **Use xlarge chunks** for comprehensive analysis of complex topics

### File Naming Convention
- `[section_id]-[title]-[size].md` - Single chunk files
- `[section_id]-[title]-chunk-[num]-[size].md` - Multi-chunk files

### Recommended Workflow
1. Review this manifest to understand document structure
2. Process high-priority sections (authentication, core APIs) first
3. Use appropriate chunk size based on your LLM and task complexity
4. Reference original section numbers for cross-referencing

## Section Details

"""
        
        for item in chunk_metadata:
            manifest_content += f"""### Section {item['section_id']}: {item['section_title']}
- **Original Size**: {item['original_tokens']} tokens
- **Chunks Created**: {item['chunks_created']}
- **Files**: {', '.join(item['chunk_files'])}

"""
        
        manifest_file = self.chunked_dir / "chunk-manifest.md"
        FileUtils.write_markdown(manifest_content, manifest_file)
        
        # Also create JSON version for programmatic access
        json_manifest = {
            'generated_at': datetime.now().isoformat(),
            'total_sections': total_sections,
            'total_chunks': total_chunks,
            'chunk_sizes': self.chunk_sizes,
            'sections': chunk_metadata
        }
        
        json_file = self.chunked_dir / "chunk-manifest.json"
        FileUtils.write_json(json_manifest, json_file)
        
        return manifest_file