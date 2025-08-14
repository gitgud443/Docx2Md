#!/usr/bin/env python3

import sys
import os

def convert_problematic_docx(input_file, output_file):
    """Try multiple methods to convert a problematic DOCX file."""
    methods = [
        try_mammoth,
        try_python_docx,
        try_docx2python,
        try_docx2txt,
        try_direct_extraction
    ]
    
    for method in methods:
        try:
            print(f"Trying {method.__name__}...")
            if method(input_file, output_file):
                return True
        except Exception as e:
            print(f"Method {method.__name__} failed: {e}")
    
    print("All conversion methods failed.")
    return False

def try_mammoth(input_file, output_file):
    """Try converting with mammoth."""
    try:
        import mammoth
        with open(input_file, "rb") as docx_file:
            result = mammoth.convert_to_markdown(docx_file)
            markdown = result.value
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        print(f"Successfully converted using mammoth")
        return True
    except ImportError:
        print("mammoth not installed. Skipping.")
        return False
    except Exception as e:
        print(f"mammoth conversion error: {e}")
        return False

def try_python_docx(input_file, output_file):
    """Try converting with python-docx."""
    try:
        import docx
        doc = docx.Document(input_file)
        
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write('\n\n'.join(full_text))
        
        print(f"Successfully converted using python-docx")
        return True
    except ImportError:
        print("python-docx not installed. Skipping.")
        return False
    except Exception as e:
        print(f"python-docx conversion error: {e}")
        return False

def try_docx2python(input_file, output_file):
    """Try converting with docx2python."""
    try:
        import docx2python
        doc = docx2python.docx2python(input_file)
        
        markdown_content = []
        for paragraph in doc.body_runs:
            if paragraph:
                text = ' '.join([run[1] for run in paragraph if run[1].strip()])
                if text.strip():
                    markdown_content.append(text)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write('\n\n'.join(markdown_content))
        
        print(f"Successfully converted using docx2python")
        return True
    except ImportError:
        print("docx2python not installed. Skipping.")
        return False
    except Exception as e:
        print(f"docx2python conversion error: {e}")
        return False

def try_docx2txt(input_file, output_file):
    """Try converting with docx2txt."""
    try:
        import docx2txt
        text = docx2txt.process(input_file)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        
        print(f"Successfully converted using docx2txt")
        return True
    except ImportError:
        print("docx2txt not installed. Skipping.")
        return False
    except Exception as e:
        print(f"docx2txt conversion error: {e}")
        return False

def try_direct_extraction(input_file, output_file):
    """Try direct extraction by treating the DOCX as a ZIP file."""
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        # Create a temporary directory
        temp_dir = os.path.join(os.path.dirname(input_file), "temp_extract")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract the DOCX file as a ZIP
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Parse the document.xml file
        doc_xml = os.path.join(temp_dir, "word", "document.xml")
        
        if not os.path.exists(doc_xml):
            print(f"Could not find document.xml in the extracted DOCX file")
            return False
        
        # Parse the XML
        tree = ET.parse(doc_xml)
        root = tree.getroot()
        
        # Extract text content
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        text_content = []
        
        for paragraph in root.findall(f".//{namespace}p"):
            para_text = []
            for text_elem in paragraph.findall(f".//{namespace}t"):
                if text_elem.text:
                    para_text.append(text_elem.text)
            
            if para_text:
                text_content.append("".join(para_text))
        
        # Write the extracted text to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(text_content))
        
        print(f"Successfully extracted text directly")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"Direct extraction error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_problematic_docx.py input_file.docx output_file.md")
        sys.exit(1)
    
    success = convert_problematic_docx(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
