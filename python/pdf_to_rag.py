#!/usr/bin/env python3
"""
PDF to RAG Preparation Tool
Converts PDFs into optimized chunks for vector databases and RAG systems.
Separate from the main markdown converter to focus solely on embedding optimization.
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
import hashlib
from typing import List, Dict, Any, Tuple

# PDF processing libraries
import pypdf
import pdfplumber

# Optional but recommended for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Using approximation for token counting.")

class PDFToRAGProcessor:
    """Processes PDFs into optimized chunks for RAG and vector databases"""
    
    def __init__(self, pdf_path: str, output_dir: str, 
                 chunk_size: int = 768, 
                 chunk_overlap: int = 128,
                 vector_db_format: str = "generic",
                 embedding_model: str = "text-embedding-ada-002"):
        """
        Initialize RAG processor
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory for chunks
            chunk_size: Target chunk size in tokens (default 768 for most embedding models)
            chunk_overlap: Overlap between chunks for context preservation
            vector_db_format: Target vector database format (generic, pinecone, chromadb, weaviate, qdrant)
            embedding_model: Target embedding model for optimization
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_db_format = vector_db_format
        self.embedding_model = embedding_model
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tokenizer if available
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
            except:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            self.tokenizer = None
            
        # Document metadata
        self.doc_id = self.generate_doc_id()
        self.doc_metadata = {
            'source_file': self.pdf_path.name,
            'doc_id': self.doc_id,
            'processed_at': datetime.now().isoformat(),
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'embedding_model': embedding_model
        }
    
    def generate_doc_id(self) -> str:
        """Generate unique document ID from file path and timestamp"""
        content = f"{self.pdf_path.name}{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def extract_text(self) -> List[Dict[str, Any]]:
        """Extract text from PDF with page-level metadata"""
        pages = []
        
        try:
            # Try pdfplumber first for better table extraction
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    
                    # Extract tables if present
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            table_text = self.format_table_for_embedding(table)
                            text += f"\n\n{table_text}\n"
                    
                    pages.append({
                        'page_num': i,
                        'text': text,
                        'char_count': len(text),
                        'has_tables': bool(tables)
                    })
        except Exception as e:
            print(f"pdfplumber failed, falling back to pypdf: {e}")
            # Fallback to pypdf
            with open(self.pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                for i, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    pages.append({
                        'page_num': i,
                        'text': text,
                        'char_count': len(text),
                        'has_tables': False
                    })
        
        return pages
    
    def format_table_for_embedding(self, table: List[List]) -> str:
        """Format table data for optimal embedding"""
        if not table:
            return ""
        
        # Create structured text representation
        lines = []
        if table[0]:  # Header row
            headers = [str(cell) if cell else "" for cell in table[0]]
            lines.append("Table with columns: " + ", ".join(headers))
            
            for row in table[1:]:
                if row:
                    row_text = " | ".join([
                        f"{headers[i] if i < len(headers) else 'Column'}: {cell if cell else 'N/A'}"
                        for i, cell in enumerate(row)
                    ])
                    lines.append(row_text)
        
        return "\n".join(lines)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximation: ~4 characters per token
            return len(text) // 4
    
    def create_semantic_chunks(self, pages: List[Dict]) -> List[Dict]:
        """Create semantically aware chunks optimized for embeddings"""
        chunks = []
        current_chunk = []
        current_tokens = 0
        current_pages = set()
        chunk_id = 0
        
        # Combine all pages into one text for processing
        full_text = "\n\n".join([p['text'] for p in pages])
        
        # Find natural boundaries
        boundaries = self.detect_semantic_boundaries(full_text)
        
        # Split text at boundaries
        segments = self.split_at_boundaries(full_text, boundaries)
        
        for segment in segments:
            segment_tokens = self.count_tokens(segment['text'])
            
            # Determine which pages this segment comes from
            segment_pages = self.find_source_pages(segment['start'], pages)
            
            if current_tokens + segment_tokens <= self.chunk_size:
                # Add to current chunk
                current_chunk.append(segment['text'])
                current_tokens += segment_tokens
                current_pages.update(segment_pages)
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(self.create_chunk_object(
                        chunk_id, chunk_text, list(current_pages), segment.get('type', 'text')
                    ))
                    chunk_id += 1
                
                # Handle oversized segments
                if segment_tokens > self.chunk_size:
                    # Split large segment
                    sub_chunks = self.split_large_segment(segment['text'], segment_pages)
                    for sub_chunk in sub_chunks:
                        chunks.append(self.create_chunk_object(
                            chunk_id, sub_chunk['text'], sub_chunk['pages'], segment.get('type', 'text')
                        ))
                        chunk_id += 1
                    current_chunk = []
                    current_tokens = 0
                    current_pages = set()
                else:
                    # Start new chunk with overlap
                    if chunks and self.chunk_overlap > 0:
                        overlap_text = self.get_overlap_text(current_chunk, self.chunk_overlap)
                        current_chunk = [overlap_text, segment['text']]
                        current_tokens = self.count_tokens(overlap_text) + segment_tokens
                    else:
                        current_chunk = [segment['text']]
                        current_tokens = segment_tokens
                    current_pages = set(segment_pages)
        
        # Add final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(self.create_chunk_object(
                chunk_id, chunk_text, list(current_pages), 'text'
            ))
        
        return chunks
    
    def detect_semantic_boundaries(self, text: str) -> List[Dict]:
        """Detect natural semantic boundaries in text"""
        boundaries = []
        
        # Patterns that indicate semantic boundaries
        patterns = [
            (r'\n#{1,6}\s+(.+)', 'header'),
            (r'\n\n(?=[A-Z])', 'paragraph'),
            (r'\n(?:Chapter|Section|Part)\s+\d+', 'chapter'),
            (r'\n\d+\.\s+[A-Z]', 'numbered_section'),
            (r'\n```[\s\S]*?```', 'code_block'),
            (r'\n\|.*\|.*\n', 'table'),
        ]
        
        for pattern, boundary_type in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                boundaries.append({
                    'position': match.start(),
                    'type': boundary_type,
                    'text': match.group()[:50]  # First 50 chars for context
                })
        
        # Sort by position
        boundaries.sort(key=lambda x: x['position'])
        return boundaries
    
    def split_at_boundaries(self, text: str, boundaries: List[Dict]) -> List[Dict]:
        """Split text at semantic boundaries"""
        segments = []
        last_pos = 0
        
        for boundary in boundaries:
            if boundary['position'] > last_pos:
                segment_text = text[last_pos:boundary['position']].strip()
                if segment_text:
                    segments.append({
                        'text': segment_text,
                        'start': last_pos,
                        'end': boundary['position'],
                        'type': boundary.get('type', 'text')
                    })
                last_pos = boundary['position']
        
        # Add final segment
        if last_pos < len(text):
            segment_text = text[last_pos:].strip()
            if segment_text:
                segments.append({
                    'text': segment_text,
                    'start': last_pos,
                    'end': len(text),
                    'type': 'text'
                })
        
        return segments
    
    def find_source_pages(self, position: int, pages: List[Dict]) -> List[int]:
        """Find which pages a text position belongs to"""
        char_count = 0
        source_pages = []
        
        for page in pages:
            page_start = char_count
            page_end = char_count + page['char_count']
            
            if page_start <= position < page_end:
                source_pages.append(page['page_num'])
            
            char_count = page_end
        
        return source_pages if source_pages else [1]
    
    def split_large_segment(self, text: str, pages: List[int]) -> List[Dict]:
        """Split a large segment into smaller chunks"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_tokens = 0
        
        for word in words:
            word_tokens = self.count_tokens(word + " ")
            if current_tokens + word_tokens <= self.chunk_size:
                current_chunk.append(word)
                current_tokens += word_tokens
            else:
                if current_chunk:
                    chunks.append({
                        'text': " ".join(current_chunk),
                        'pages': pages
                    })
                current_chunk = [word]
                current_tokens = word_tokens
        
        if current_chunk:
            chunks.append({
                'text': " ".join(current_chunk),
                'pages': pages
            })
        
        return chunks
    
    def get_overlap_text(self, chunk_text: List[str], overlap_tokens: int) -> str:
        """Get overlap text from end of previous chunk"""
        if not chunk_text:
            return ""
        
        # Get last part of chunk
        full_text = "\n\n".join(chunk_text)
        words = full_text.split()
        
        overlap_text = []
        current_tokens = 0
        
        for word in reversed(words):
            word_tokens = self.count_tokens(word + " ")
            if current_tokens + word_tokens <= overlap_tokens:
                overlap_text.insert(0, word)
                current_tokens += word_tokens
            else:
                break
        
        return " ".join(overlap_text)
    
    def create_chunk_object(self, chunk_id: int, text: str, pages: List[int], 
                           content_type: str) -> Dict:
        """Create a chunk object with metadata"""
        # Extract keywords and entities
        keywords = self.extract_keywords(text)
        
        # Calculate quality metrics
        quality_score = self.calculate_quality_score(text)
        
        return {
            'chunk_id': f"{self.doc_id}_chunk_{chunk_id:04d}",
            'text': text,
            'metadata': {
                'doc_id': self.doc_id,
                'chunk_index': chunk_id,
                'source_pages': pages,
                'content_type': content_type,
                'token_count': self.count_tokens(text),
                'char_count': len(text),
                'keywords': keywords,
                'quality_score': quality_score,
                'has_code': bool(re.search(r'```|`[^`]+`', text)),
                'has_urls': bool(re.search(r'https?://\S+', text)),
                'embedding_model': self.embedding_model,
                'created_at': datetime.now().isoformat()
            }
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction based on capitalized words and technical terms
        keywords = set()
        
        # Technical terms
        tech_terms = re.findall(r'\b(?:API|HTTP|JSON|XML|REST|GraphQL|OAuth|JWT|SQL|NoSQL|CRUD)\b', 
                               text, re.IGNORECASE)
        keywords.update([term.upper() for term in tech_terms])
        
        # Capitalized phrases (likely important terms)
        cap_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        keywords.update([phrase for phrase in cap_phrases if len(phrase) > 3])
        
        return list(keywords)[:20]  # Limit to 20 keywords
    
    def calculate_quality_score(self, text: str) -> float:
        """Calculate quality score for chunk (0-1)"""
        score = 0.5  # Base score
        
        # Positive factors
        if len(text) > 100:
            score += 0.1
        if re.search(r'[.!?]$', text.strip()):  # Complete sentence
            score += 0.1
        if re.search(r'^[A-Z]', text.strip()):  # Starts with capital
            score += 0.1
        if text.count('.') > 1:  # Multiple sentences
            score += 0.1
        if re.search(r'\b(?:def|class|function|import|return)\b', text):  # Code
            score += 0.1
        
        # Negative factors
        if len(text) < 50:
            score -= 0.2
        if text.count('\n') / max(len(text), 1) > 0.3:  # Too many line breaks
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def generate_vector_db_format(self, chunks: List[Dict]) -> Dict:
        """Generate format specific to target vector database"""
        if self.vector_db_format == "pinecone":
            return self.format_for_pinecone(chunks)
        elif self.vector_db_format == "chromadb":
            return self.format_for_chromadb(chunks)
        elif self.vector_db_format == "weaviate":
            return self.format_for_weaviate(chunks)
        elif self.vector_db_format == "qdrant":
            return self.format_for_qdrant(chunks)
        else:
            return self.format_generic(chunks)
    
    def format_for_pinecone(self, chunks: List[Dict]) -> Dict:
        """Format chunks for Pinecone"""
        vectors = []
        for chunk in chunks:
            vectors.append({
                'id': chunk['chunk_id'],
                'values': [],  # Embeddings would go here
                'metadata': {
                    'text': chunk['text'][:1000],  # Pinecone has metadata size limits
                    'doc_id': chunk['metadata']['doc_id'],
                    'pages': str(chunk['metadata']['source_pages']),
                    'token_count': chunk['metadata']['token_count'],
                    'keywords': ', '.join(chunk['metadata']['keywords'][:10]),
                    'quality_score': chunk['metadata']['quality_score']
                }
            })
        
        return {
            'vectors': vectors,
            'namespace': self.doc_id,
            'dimension': 1536  # For OpenAI embeddings
        }
    
    def format_for_chromadb(self, chunks: List[Dict]) -> Dict:
        """Format chunks for ChromaDB"""
        return {
            'ids': [chunk['chunk_id'] for chunk in chunks],
            'documents': [chunk['text'] for chunk in chunks],
            'metadatas': [
                {
                    'doc_id': chunk['metadata']['doc_id'],
                    'pages': str(chunk['metadata']['source_pages']),
                    'token_count': chunk['metadata']['token_count'],
                    'keywords': ', '.join(chunk['metadata']['keywords']),
                    'quality_score': chunk['metadata']['quality_score']
                }
                for chunk in chunks
            ],
            'collection_name': f"pdf_{self.doc_id}"
        }
    
    def format_for_weaviate(self, chunks: List[Dict]) -> Dict:
        """Format chunks for Weaviate"""
        objects = []
        for chunk in chunks:
            objects.append({
                'class': 'DocumentChunk',
                'id': chunk['chunk_id'],
                'properties': {
                    'content': chunk['text'],
                    'docId': chunk['metadata']['doc_id'],
                    'sourcePages': chunk['metadata']['source_pages'],
                    'tokenCount': chunk['metadata']['token_count'],
                    'keywords': chunk['metadata']['keywords'],
                    'qualityScore': chunk['metadata']['quality_score'],
                    'contentType': chunk['metadata']['content_type']
                }
            })
        
        return {
            'objects': objects,
            'class_name': 'DocumentChunk'
        }
    
    def format_for_qdrant(self, chunks: List[Dict]) -> Dict:
        """Format chunks for Qdrant"""
        points = []
        for i, chunk in enumerate(chunks):
            points.append({
                'id': i,
                'vector': [],  # Embeddings would go here
                'payload': {
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'doc_id': chunk['metadata']['doc_id'],
                    'pages': chunk['metadata']['source_pages'],
                    'token_count': chunk['metadata']['token_count'],
                    'keywords': chunk['metadata']['keywords'],
                    'quality_score': chunk['metadata']['quality_score']
                }
            })
        
        return {
            'points': points,
            'collection_name': f"pdf_{self.doc_id}"
        }
    
    def format_generic(self, chunks: List[Dict]) -> Dict:
        """Generic format that can be adapted to any vector database"""
        return {
            'chunks': chunks,
            'document_metadata': self.doc_metadata,
            'total_chunks': len(chunks),
            'format_version': '1.0'
        }
    
    def save_outputs(self, chunks: List[Dict], vector_format: Dict):
        """Save all outputs to files"""
        # Save raw chunks
        chunks_file = self.output_dir / "chunks.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        # Save vector DB format
        vector_file = self.output_dir / f"{self.vector_db_format}_format.json"
        with open(vector_file, 'w', encoding='utf-8') as f:
            json.dump(vector_format, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        metadata_file = self.output_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.doc_metadata, f, indent=2, ensure_ascii=False)
        
        # Create import instructions
        self.create_import_instructions()
        
        print(f"✅ Created {len(chunks)} chunks optimized for {self.embedding_model}")
        print(f"📁 Output saved to: {self.output_dir}")
        print(f"📊 Format: {self.vector_db_format}")
    
    def create_import_instructions(self):
        """Create database-specific import instructions"""
        instructions = self.output_dir / "import_instructions.md"
        
        content = f"""# Vector Database Import Instructions

Generated: {datetime.now().isoformat()}
Document: {self.pdf_path.name}
Chunks: See chunks.json
Format: {self.vector_db_format}

## Quick Import Examples

### ChromaDB
```python
import chromadb
import json

# Load the prepared chunks
with open('{self.vector_db_format}_format.json', 'r') as f:
    data = json.load(f)

# Create client and collection
client = chromadb.Client()
collection = client.create_collection(name=data['collection_name'])

# Add documents with embeddings
collection.add(
    ids=data['ids'],
    documents=data['documents'],
    metadatas=data['metadatas']
)
```

### Pinecone
```python
import pinecone
import json
from openai import OpenAI

# Load the prepared chunks
with open('{self.vector_db_format}_format.json', 'r') as f:
    data = json.load(f)

# Initialize Pinecone
pinecone.init(api_key="YOUR_API_KEY")
index = pinecone.Index("your-index-name")

# Generate embeddings (example with OpenAI)
client = OpenAI()
for vector in data['vectors']:
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=vector['metadata']['text']
    )
    vector['values'] = response.data[0].embedding

# Upsert to Pinecone
index.upsert(vectors=data['vectors'], namespace=data['namespace'])
```

### Weaviate
```python
import weaviate
import json

# Load the prepared chunks  
with open('{self.vector_db_format}_format.json', 'r') as f:
    data = json.load(f)

# Connect to Weaviate
client = weaviate.Client("http://localhost:8080")

# Import objects
client.batch.configure(batch_size=100)
with client.batch as batch:
    for obj in data['objects']:
        batch.add_data_object(
            obj['properties'],
            class_name=obj['class'],
            uuid=obj['id']
        )
```

### Qdrant
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json

# Load the prepared chunks
with open('{self.vector_db_format}_format.json', 'r') as f:
    data = json.load(f)

# Initialize Qdrant client
client = QdrantClient("localhost", port=6333)

# Create collection
client.recreate_collection(
    collection_name=data['collection_name'],
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Generate embeddings and upload
# (Add your embedding generation here)
client.upsert(
    collection_name=data['collection_name'],
    points=data['points']
)
```

## Next Steps

1. **Generate Embeddings**: Use your preferred embedding model
2. **Import to Database**: Use the examples above for your database
3. **Test Queries**: Verify retrieval with sample queries
4. **Optimize**: Adjust chunk_size and overlap based on results

## Files Generated

- `chunks.json`: Raw chunks with full metadata
- `{self.vector_db_format}_format.json`: Database-specific format
- `metadata.json`: Document-level metadata
- `import_instructions.md`: This file
"""
        
        with open(instructions, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def process(self) -> int:
        """Main processing pipeline"""
        print(f"📄 Processing: {self.pdf_path.name}")
        print(f"🎯 Target: {self.vector_db_format} with {self.embedding_model}")
        
        # Extract text from PDF
        pages = self.extract_text()
        print(f"📖 Extracted {len(pages)} pages")
        
        # Create semantic chunks
        chunks = self.create_semantic_chunks(pages)
        print(f"✂️ Created {len(chunks)} chunks (~{self.chunk_size} tokens each)")
        
        # Generate vector database format
        vector_format = self.generate_vector_db_format(chunks)
        
        # Save outputs
        self.save_outputs(chunks, vector_format)
        
        return len(chunks)


def main():
    parser = argparse.ArgumentParser(
        description='Prepare PDF for RAG and vector databases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf ./rag_output
  %(prog)s document.pdf ./rag_output --chunk-size 512 --format chromadb
  %(prog)s document.pdf ./rag_output --model text-embedding-3-small
        """
    )
    
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('output_dir', help='Output directory for chunks')
    parser.add_argument('--chunk-size', type=int, default=768,
                       help='Target chunk size in tokens (default: 768)')
    parser.add_argument('--chunk-overlap', type=int, default=128,
                       help='Overlap between chunks in tokens (default: 128)')
    parser.add_argument('--format', choices=['generic', 'pinecone', 'chromadb', 'weaviate', 'qdrant'],
                       default='generic', help='Vector database format (default: generic)')
    parser.add_argument('--model', default='text-embedding-ada-002',
                       help='Target embedding model (default: text-embedding-ada-002)')
    
    args = parser.parse_args()
    
    processor = PDFToRAGProcessor(
        args.pdf_path,
        args.output_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        vector_db_format=args.format,
        embedding_model=args.model
    )
    
    num_chunks = processor.process()
    print(f"\n✅ Success! Created {num_chunks} chunks ready for vector database import")
    print(f"📚 See import_instructions.md in output directory for next steps")


if __name__ == "__main__":
    main()