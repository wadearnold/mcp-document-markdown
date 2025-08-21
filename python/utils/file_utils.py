"""
File I/O and path utilities
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class FileUtils:
    """File and directory utilities"""
    
    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Ensure directory exists, create if needed"""
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def safe_filename(text: str, max_length: int = 100) -> str:
        """Create a safe filename from text"""
        import re
        # Remove/replace unsafe characters
        safe = re.sub(r'[<>:"/\\|?*]', '_', text)
        safe = re.sub(r'[^\w\s-]', '', safe)
        safe = re.sub(r'[-\s]+', '-', safe)
        
        # Truncate if too long
        if len(safe) > max_length:
            safe = safe[:max_length].rsplit('-', 1)[0]
        
        return safe.strip('-')
    
    @staticmethod
    def write_json(data: Any, file_path: Path, indent: int = 2) -> None:
        """Write data to JSON file with proper formatting"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def read_json(file_path: Path) -> Any:
        """Read data from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def write_markdown(content: str, file_path: Path) -> None:
        """Write markdown content to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def read_markdown(file_path: Path) -> str:
        """Read markdown content from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def create_index_file(directory: Path, title: str, items: List[Dict[str, Any]]) -> Path:
        """Create an index markdown file for a directory"""
        index_content = f"""# {title}

Generated: {datetime.now().isoformat()}
Total Items: {len(items)}

## Contents

"""
        
        for item in items:
            name = item.get('name', 'Unnamed')
            description = item.get('description', '')
            file_path = item.get('file', '')
            
            if file_path:
                index_content += f"- [{name}]({file_path})"
            else:
                index_content += f"- {name}"
            
            if description:
                index_content += f" - {description}"
            
            index_content += "\n"
        
        index_file = directory / "README.md"
        FileUtils.write_markdown(index_content, index_file)
        return index_file
    
    @staticmethod
    def get_file_stats(file_path: Path) -> Dict[str, Any]:
        """Get file statistics"""
        if not file_path.exists():
            return {}
        
        stat = file_path.stat()
        return {
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat()
        }
    
    @staticmethod
    def list_files_by_extension(directory: Path, extension: str) -> List[Path]:
        """List all files with given extension in directory"""
        pattern = f"*.{extension.lstrip('.')}"
        return list(directory.glob(pattern))
    
    @staticmethod
    def create_metadata_file(directory: Path, metadata: Dict[str, Any]) -> Path:
        """Create metadata file for a directory"""
        metadata_file = directory / "metadata.json"
        
        # Add generation timestamp
        metadata['generated_at'] = datetime.now().isoformat()
        metadata['directory'] = str(directory)
        
        FileUtils.write_json(metadata, metadata_file)
        return metadata_file