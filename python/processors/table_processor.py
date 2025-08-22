try:
    from ..utils.file_utils import FileUtils
    from ..utils.token_counter import TokenCounter
except ImportError:
    # Handle running as script vs package
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.file_utils import FileUtils
    from utils.token_counter import TokenCounter
"""
Table processing and structured format conversion
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import re


class TableProcessor:
    """Handles table conversion and structured format generation"""
    
    def __init__(self, output_dir: str, token_counter: TokenCounter):
        """
        Initialize table processor
        
        Args:
            output_dir: Output directory for processed tables
            token_counter: Token counter for LLM optimization
        """
        self.output_dir = Path(output_dir)
        self.token_counter = token_counter
        self.tables_dir = self.output_dir / "tables"
        FileUtils.ensure_directory(self.tables_dir)
    
    def process_all_tables(self, tables: List[Dict[str, Any]]) -> List[str]:
        """
        Process all extracted tables into structured formats
        
        Args:
            tables: List of table dictionaries from PDF extraction
            
        Returns:
            List of paths to created table files
        """
        if not tables:
            return []
        
        created_files = []
        all_tables_data = []
        
        for i, table_info in enumerate(tables):
            try:
                # Process individual table
                structured_data = self.process_table_for_structure(table_info)
                
                if structured_data:
                    # Save enhanced markdown
                    table_file = self.create_enhanced_table_markdown(i + 1, table_info, structured_data)
                    created_files.append(str(table_file))
                    
                    # Save structured JSON
                    json_file = self.create_table_json(i + 1, structured_data)
                    created_files.append(str(json_file))
                    
                    all_tables_data.append({
                        'table_id': i + 1,
                        'page': table_info.get('page', 0),
                        'structured_data': structured_data,
                        'markdown_file': table_file.name,
                        'json_file': json_file.name
                    })
                    
            except Exception as e:
                import traceback
                print(f"Failed to process table {i + 1}: {e}")
                traceback.print_exc()
        
        # Create tables index
        if all_tables_data:
            index_file = self.create_tables_index(all_tables_data)
            created_files.append(str(index_file))
        
        return created_files
    
    def process_table_for_structure(self, table_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single table for structured data conversion"""
        table_data = table_info.get('data', [])
        if not table_data or len(table_data) < 2:
            return None
        
        try:
            # Create DataFrame
            df = pd.DataFrame(table_data[1:], columns=table_data[0])
            
            # Clean up the data
            df = df.fillna('')
            df = df.astype(str)
            
            # Detect and convert cell values
            processed_df = df.copy()
            for col in df.columns:
                processed_df[col] = df[col].apply(self.detect_and_convert_cell_value)
            
            # Generate statistics
            stats = self.generate_table_statistics(processed_df, df)
            
            # Create structured representation
            structured_data = {
                'metadata': {
                    'page': table_info.get('page', 0),
                    'table_index': table_info.get('index', 0),
                    'rows': len(processed_df),
                    'columns': len(processed_df.columns),
                    'generated_at': datetime.now().isoformat(),
                    'processing_notes': self.get_table_processing_notes(processed_df, stats)
                },
                'schema': self.generate_table_schema(processed_df, stats),
                'data': {
                    'headers': list(processed_df.columns),
                    'rows': processed_df.values.tolist(),
                    'formatted_rows': []
                },
                'statistics': stats,
                'llm_metadata': {
                    'token_count': self.token_counter.count_tokens(str(processed_df.to_dict())),
                    'processing_complexity': self.assess_table_complexity(processed_df),
                    'recommended_use': self.recommend_table_usage(processed_df, stats)
                }
            }
            
            # Add formatted rows for better LLM consumption
            for _, row in processed_df.iterrows():
                formatted_row = {}
                for col, val in row.items():
                    formatted_row[str(col)] = self.format_cell_for_llm(val)
                structured_data['data']['formatted_rows'].append(formatted_row)
            
            return structured_data
            
        except Exception as e:
            print(f"Error processing table structure: {e}")
            return None
    
    def detect_and_convert_cell_value(self, value: str) -> Union[str, int, float, bool, None]:
        """Detect and convert cell value to appropriate type"""
        if not value or pd.isna(value) or value == '':
            return None
        
        value_str = str(value).strip()
        value_lower = value_str.lower()
        
        # Boolean values
        if value_lower in ['true', 'yes', 'y', '1', 'on', 'enabled']:
            return True
        elif value_lower in ['false', 'no', 'n', '0', 'off', 'disabled']:
            return False
        
        # Numeric values
        try:
            # Try integer first
            if '.' not in value_str and value_str.isdigit():
                return int(value_str)
            # Try float
            elif re.match(r'^-?\d+\.?\d*$', value_str):
                return float(value_str)
        except ValueError:
            pass
        
        # Currency values
        currency_match = re.match(r'^\$?([\d,]+\.?\d*)$', value_str)
        if currency_match:
            try:
                return float(currency_match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        # Percentage values
        if value_str.endswith('%'):
            try:
                return float(value_str[:-1]) / 100
            except ValueError:
                pass
        
        # Date values (simple detection)
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}'
        ]
        if any(re.match(pattern, value_str) for pattern in date_patterns):
            return value_str  # Keep as string but mark as date
        
        # Return as string
        return value_str
    
    def generate_table_statistics(self, processed_df: pd.DataFrame, original_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive table statistics"""
        stats = {
            'dimensions': {
                'rows': len(processed_df),
                'columns': len(processed_df.columns)
            },
            'data_types': {},
            'null_counts': {},
            'value_distributions': {},
            'column_analysis': {}
        }
        
        for col in processed_df.columns:
            col_data = processed_df[col].dropna()
            
            # Data type analysis
            types = {}
            for val in col_data:
                val_type = type(val).__name__
                types[val_type] = types.get(val_type, 0) + 1
            
            stats['data_types'][col] = types
            
            # Null count
            stats['null_counts'][col] = processed_df[col].isnull().sum()
            
            # Value distribution (for categorical-like data)
            if len(col_data.unique()) <= 20:  # Only for low cardinality
                value_counts = col_data.value_counts().to_dict()
                stats['value_distributions'][col] = {str(k): v for k, v in value_counts.items()}
            
            # Column analysis
            stats['column_analysis'][col] = {
                'unique_values': len(col_data.unique()),
                'most_common_type': max(types.items(), key=lambda x: x[1])[0],
                'has_numeric': any(isinstance(v, (int, float)) for v in col_data),
                'has_boolean': any(isinstance(v, bool) for v in col_data),
                'has_null': col in stats['null_counts'] and stats['null_counts'][col] > 0
            }
        
        return stats
    
    def generate_table_schema(self, df: pd.DataFrame, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate table schema for structured representation"""
        schema = {
            'fields': [],
            'primary_key': None,
            'constraints': []
        }
        
        for col in df.columns:
            col_analysis = stats['column_analysis'][col]
            
            field = {
                'name': col,
                'type': self.infer_field_type(col_analysis),
                'nullable': col_analysis['has_null'],
                'unique_values': col_analysis['unique_values'],
                'description': self.generate_field_description(col, col_analysis)
            }
            
            schema['fields'].append(field)
        
        return schema
    
    def infer_field_type(self, col_analysis: Dict[str, Any]) -> str:
        """Infer field type from column analysis"""
        if col_analysis['has_boolean']:
            return 'boolean'
        elif col_analysis['has_numeric']:
            return 'number'
        elif col_analysis['unique_values'] <= 10:
            return 'categorical'
        else:
            return 'text'
    
    def generate_field_description(self, col_name: str, col_analysis: Dict[str, Any]) -> str:
        """Generate human-readable field description"""
        desc_parts = []
        
        if col_analysis['has_boolean']:
            desc_parts.append("Boolean values")
        elif col_analysis['has_numeric']:
            desc_parts.append("Numeric values")
        else:
            desc_parts.append("Text values")
        
        if col_analysis['unique_values'] <= 5:
            desc_parts.append("(low cardinality)")
        elif col_analysis['unique_values'] > 50:
            desc_parts.append("(high cardinality)")
        
        if col_analysis['has_null']:
            desc_parts.append("with null values")
        
        return f"{col_name}: {' '.join(desc_parts)}"
    
    def get_table_processing_notes(self, df: pd.DataFrame, stats: Dict[str, Any]) -> List[str]:
        """Generate processing notes for LLM guidance"""
        notes = []
        
        # Size-based notes
        if len(df) > 100:
            notes.append("Large table - consider processing in chunks for LLM analysis")
        elif len(df) < 5:
            notes.append("Small table - suitable for complete LLM processing")
        
        # Complexity notes
        if len(df.columns) > 10:
            notes.append("Many columns - focus on key fields for initial analysis")
        
        # Data type notes
        numeric_cols = sum(1 for col, analysis in stats['column_analysis'].items() if analysis['has_numeric'])
        if numeric_cols > 0:
            notes.append(f"Contains {numeric_cols} numeric columns suitable for statistical analysis")
        
        categorical_cols = sum(1 for col, analysis in stats['column_analysis'].items() if analysis['unique_values'] <= 10)
        if categorical_cols > 0:
            notes.append(f"Contains {categorical_cols} categorical columns for grouping/filtering")
        
        return notes
    
    def assess_table_complexity(self, df: pd.DataFrame) -> str:
        """Assess table complexity for LLM processing"""
        total_cells = len(df) * len(df.columns)
        
        if total_cells <= 50:
            return "simple"
        elif total_cells <= 200:
            return "moderate"
        elif total_cells <= 1000:
            return "complex"
        else:
            return "very_complex"
    
    def recommend_table_usage(self, df: pd.DataFrame, stats: Dict[str, Any]) -> List[str]:
        """Recommend how to use table for LLM tasks"""
        recommendations = []
        
        # Analysis recommendations
        numeric_cols = sum(1 for col, analysis in stats['column_analysis'].items() if analysis['has_numeric'])
        if numeric_cols >= 2:
            recommendations.append("Suitable for statistical analysis and trend identification")
        
        categorical_cols = sum(1 for col, analysis in stats['column_analysis'].items() if analysis['unique_values'] <= 10)
        if categorical_cols > 0:
            recommendations.append("Good for grouping and categorical analysis")
        
        # Size recommendations
        if len(df) > 20:
            recommendations.append("Use filtering or sampling for initial exploration")
        else:
            recommendations.append("Small enough for complete analysis in single LLM request")
        
        return recommendations
    
    def format_cell_for_llm(self, value: Any) -> str:
        """Format cell value for optimal LLM consumption"""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, float):
            if value == int(value):
                return str(int(value))
            else:
                return f"{value:.2f}"
        else:
            return str(value)
    
    def create_enhanced_table_markdown(self, table_num: int, table_info: Dict, structured_data: Dict) -> Path:
        """Create enhanced markdown file for table"""
        metadata = structured_data['metadata']
        stats = structured_data['statistics']
        llm_meta = structured_data['llm_metadata']
        
        content = f"""# Table {table_num}

**Source**: Page {metadata['page']} of PDF  
**Generated**: {metadata['generated_at']}  
**Dimensions**: {metadata['rows']} rows × {metadata['columns']} columns  
**Token Count**: {llm_meta['token_count']}  
**Complexity**: {llm_meta['processing_complexity']}  

## Processing Notes

{chr(10).join(f"- {note}" for note in metadata['processing_notes'])}

## Recommended Usage

{chr(10).join(f"- {rec}" for rec in llm_meta['recommended_use'])}

## Table Data

{table_info.get('markdown', '')}

## Data Schema

"""
        
        # Add schema information
        for field in structured_data['schema']['fields']:
            content += f"- **{field['name']}**: {field['description']}\n"
        
        # Add statistics
        content += f"""

## Statistics

- **Total Rows**: {stats['dimensions']['rows']}
- **Total Columns**: {stats['dimensions']['columns']}
- **Data Types**: {len(set(field['type'] for field in structured_data['schema']['fields']))} different types
- **Null Values**: {sum(stats['null_counts'].values())} total

### Column Analysis

"""
        
        for col, analysis in stats['column_analysis'].items():
            content += f"- **{col}**: {analysis['unique_values']} unique values, "
            content += f"type: {analysis['most_common_type']}"
            if analysis['has_null']:
                content += f", {stats['null_counts'][col]} nulls"
            content += "\n"
        
        table_file = self.tables_dir / f"table_{table_num:02d}.md"
        FileUtils.write_markdown(content, table_file)
        return table_file
    
    def create_table_json(self, table_num: int, structured_data: Dict) -> Path:
        """Create structured JSON file for table"""
        json_file = self.tables_dir / f"table_{table_num:02d}.json"
        FileUtils.write_json(structured_data, json_file)
        return json_file
    
    def create_tables_index(self, all_tables_data: List[Dict]) -> Path:
        """Create comprehensive tables index"""
        total_rows = sum(table['structured_data']['metadata']['rows'] for table in all_tables_data)
        total_cols = sum(table['structured_data']['metadata']['columns'] for table in all_tables_data)
        total_tokens = sum(table['structured_data']['llm_metadata']['token_count'] for table in all_tables_data)
        
        index_content = f"""# Tables Index

**Generated**: {datetime.now().isoformat()}  
**Total Tables**: {len(all_tables_data)}  
**Total Data**: {total_rows} rows, {total_cols} columns  
**Token Count**: {total_tokens}  

## Quick Reference

| Table | Page | Size | Format | Complexity |
|-------|------|------|---------|------------|
"""
        
        for table in all_tables_data:
            meta = table['structured_data']['metadata']
            llm_meta = table['structured_data']['llm_metadata']
            
            index_content += f"| [{table['table_id']}]({table['markdown_file']}) "
            index_content += f"| {table['page']} "
            index_content += f"| {meta['rows']}×{meta['columns']} "
            index_content += f"| [MD]({table['markdown_file']}) [JSON]({table['json_file']}) "
            index_content += f"| {llm_meta['processing_complexity']} |\n"
        
        index_content += f"""

## Processing Guidelines

### For LLM Analysis
1. **Simple tables** (≤50 cells): Process completely in single request
2. **Moderate tables** (≤200 cells): Focus on key columns first
3. **Complex tables** (≤1000 cells): Use filtering and sampling
4. **Very complex tables** (>1000 cells): Process in chunks

### Data Type Optimization
- **Numeric data**: Use for statistical analysis and calculations
- **Categorical data**: Perfect for grouping and filtering
- **Boolean data**: Ideal for condition-based queries
- **Text data**: Best for pattern matching and content analysis

### Token Management
- **Low token count** (<500): Include full table in prompts
- **Medium token count** (500-2000): Summarize or filter first
- **High token count** (>2000): Use structured queries on JSON format
"""
        
        index_file = self.tables_dir / "README.md"
        FileUtils.write_markdown(index_content, index_file)
        return index_file