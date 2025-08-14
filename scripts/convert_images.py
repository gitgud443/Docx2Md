#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from pathlib import Path
import shutil
import glob
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_conversion.log')
    ]
)
logger = logging.getLogger(__name__)

def convert_gif_to_png(gif_path):
    """Convert a GIF image to PNG using ImageMagick."""
    png_path = gif_path.replace('.gif', '.png')
    
    try:
        cmd = ['convert', gif_path, png_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Converted GIF to PNG: {gif_path} -> {png_path}")
        return png_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to convert GIF to PNG: {gif_path}")
        logger.error(f"Error: {e.stderr}")
        return None

def convert_vector_to_png(vector_path):
    """
    Convert EMF/WMF vector images to PNG using unoconv and ImageMagick.
    
    1. Convert to PDF with unoconv
    2. Convert PDF to PNG with ImageMagick, preserving quality and trimming margins
    """
    # Create temporary PDF file
    pdf_path = vector_path.replace('.emf', '.pdf').replace('.wmf', '.pdf')
    png_path = vector_path.replace('.emf', '.png').replace('.wmf', '.png')
    
    try:
        # Step 1: Convert to PDF with unoconv
        cmd = ['unoconv', '-f', 'pdf', '-o', pdf_path, vector_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Converted vector to PDF: {vector_path} -> {pdf_path}")
        
        # Step 2: Convert PDF to PNG with ImageMagick
        cmd = [
            'convert', 
            '-density', '300', 
            '-trim',
            '-bordercolor', 'white',
            '-border', '5',
            pdf_path, 
            png_path
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Converted PDF to PNG: {pdf_path} -> {png_path}")
        
        # Clean up temporary PDF file
        os.remove(pdf_path)
        
        return png_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to convert vector to PNG: {vector_path}")
        logger.error(f"Error: {e.stderr}")
        return None

def convert_vector_to_svg(vector_path):
    """
    Convert EMF/WMF vector images to SVG using Inkscape or alternative methods.
    """
    # Create SVG file path
    svg_path = vector_path.replace('.emf', '.svg').replace('.wmf', '.svg')
    
    try:
        # First try using Inkscape if available
        if shutil.which('inkscape'):
            cmd = ['inkscape', '--export-filename=' + svg_path, vector_path]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Converted vector to SVG using Inkscape: {vector_path} -> {svg_path}")
            return svg_path
            
        # If Inkscape is not available, try using pdf2svg
        # First convert to PDF with unoconv
        pdf_path = vector_path.replace('.emf', '.pdf').replace('.wmf', '.pdf')
        cmd = ['unoconv', '-f', 'pdf', '-o', pdf_path, vector_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Converted vector to PDF: {vector_path} -> {pdf_path}")
        
        # Then convert PDF to SVG with pdf2svg if available
        if shutil.which('pdf2svg'):
            cmd = ['pdf2svg', pdf_path, svg_path]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Converted PDF to SVG using pdf2svg: {pdf_path} -> {svg_path}")
        else:
            # If pdf2svg is not available, try rsvg-convert
            if shutil.which('rsvg-convert'):
                # First convert PDF to PNG with high resolution
                png_temp = pdf_path.replace('.pdf', '_temp.png')
                cmd = ['convert', '-density', '600', pdf_path, png_temp]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                # Then convert PNG to SVG with rsvg-convert
                cmd = ['rsvg-convert', '-f', 'svg', '-o', svg_path, png_temp]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info(f"Converted PDF to SVG using rsvg-convert: {pdf_path} -> {svg_path}")
                
                # Clean up temporary PNG file
                os.remove(png_temp)
            else:
                # Last resort: try direct conversion with ImageMagick
                cmd = ['convert', pdf_path, svg_path]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info(f"Converted PDF to SVG using ImageMagick: {pdf_path} -> {svg_path}")
        
        # Clean up temporary PDF file
        os.remove(pdf_path)
        return svg_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to convert vector to SVG: {vector_path}")
        logger.error(f"Error: {e.stderr}")
        
        # Fallback to PNG if SVG conversion fails
        logger.warning(f"Falling back to PNG conversion for: {vector_path}")
        png_path = convert_vector_to_png(vector_path)
        if png_path:
            logger.info(f"Successfully converted to PNG as fallback: {vector_path} -> {png_path}")
            # Rename the PNG to have .svg extension for consistency in links
            svg_fallback_path = png_path.replace('.png', '.svg')
            os.rename(png_path, svg_fallback_path)
            return svg_fallback_path
        
        return None

def process_images_in_directory(media_dir, use_svg=False):
    """
    Process all EMF, WMF, and GIF images in the given directory.
    Returns a dictionary mapping original image paths to new PNG/SVG paths.
    
    Args:
        media_dir: Directory containing the media files
        use_svg: If True, convert vector images to SVG instead of PNG
    """
    image_map = {}
    
    # Find all EMF, WMF, and GIF files
    vector_files = glob.glob(os.path.join(media_dir, "*.emf")) + glob.glob(os.path.join(media_dir, "*.wmf"))
    gif_files = glob.glob(os.path.join(media_dir, "*.gif"))
    
    # Process vector files
    for vector_file in vector_files:
        logger.info(f"Processing vector file: {vector_file}")
        if use_svg:
            new_path = convert_vector_to_svg(vector_file)
            if new_path:
                image_map[os.path.basename(vector_file)] = os.path.basename(new_path)
        else:
            new_path = convert_vector_to_png(vector_file)
            if new_path:
                image_map[os.path.basename(vector_file)] = os.path.basename(new_path)
    
    # Process GIF files
    for gif_file in gif_files:
        logger.info(f"Processing GIF file: {gif_file}")
        png_path = convert_gif_to_png(gif_file)
        if png_path:
            image_map[os.path.basename(gif_file)] = os.path.basename(png_path)
    
    return image_map

def update_markdown_links(md_file, image_map, media_dir_rel_path):
    """
    Update image links in the Markdown file to point to the new PNG/SVG images.
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace image links
    for old_image, new_image in image_map.items():
        # Handle different markdown image patterns
        # Standard markdown image: ![alt text](media/image.ext)
        pattern1 = r'!\[(.*?)\]\(' + re.escape(media_dir_rel_path) + r'/' + re.escape(old_image) + r'\)'
        replacement1 = r'![\1](' + media_dir_rel_path + r'/' + new_image + r')'
        content = re.sub(pattern1, replacement1, content)
        
        # HTML img tag: <img src="media/image.ext" ... />
        pattern2 = r'<img\s+src=["\']' + re.escape(media_dir_rel_path) + r'/' + re.escape(old_image) + r'["\']'
        replacement2 = r'<img src="' + media_dir_rel_path + r'/' + new_image + r'"'
        content = re.sub(pattern2, replacement2, content)
        
        # Reference-style markdown image: ![alt text][ref] ... [ref]: media/image.ext
        pattern3 = r'\[(.*?)\]:\s*' + re.escape(media_dir_rel_path) + r'/' + re.escape(old_image)
        replacement3 = r'[\1]: ' + media_dir_rel_path + r'/' + new_image
        content = re.sub(pattern3, replacement3, content)
    
    # Write the updated content back to the file
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Updated image links in: {md_file}")

def process_markdown_file(md_file, use_svg=False):
    """
    Process a single Markdown file:
    1. Find the associated media directory
    2. Convert problematic images
    3. Update links in the Markdown file
    
    Args:
        md_file: Path to the markdown file
        use_svg: If True, convert vector images to SVG instead of PNG
    """
    # Determine the media directory based on your specific structure
    md_dir = os.path.dirname(md_file)
    md_basename = os.path.splitext(os.path.basename(md_file))[0]
    
    # Extract the document name from the intermediate filename pattern
    # Example: output/Document_Name_images_fixed.md -> Document_Name
    doc_name = md_basename.replace('_images_fixed', '')
    
    # Check for the media directory in your specific structure
    media_dir = os.path.join("images", doc_name, "media")
    
    if not os.path.exists(media_dir) or not os.path.isdir(media_dir):
        logger.warning(f"Media directory not found: {media_dir}")
        return False
    
    # Calculate relative path from markdown file to media directory
    # This should match what fix_image_paths.py uses
    media_dir_rel_path = os.path.relpath(media_dir, md_dir)
    
    logger.info(f"Processing Markdown file: {md_file}")
    logger.info(f"Using media directory: {media_dir}")
    logger.info(f"Converting vector images to {'SVG' if use_svg else 'PNG'}")
    
    # Process images in the media directory
    image_map = process_images_in_directory(media_dir, use_svg)
    
    if not image_map:
        logger.info(f"No problematic images found for: {md_file}")
        return True
    
    # Update links in the Markdown file
    update_markdown_links(md_file, image_map, media_dir_rel_path)
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    basic_dependencies = ['convert', 'unoconv']
    missing = []
    
    for dep in basic_dependencies:
        if not shutil.which(dep):
            missing.append(dep)
    
    if missing:
        logger.error(f"Missing basic dependencies: {', '.join(missing)}")
        logger.error("Please install the required dependencies:")
        logger.error("  - ImageMagick (for 'convert' command)")
        logger.error("  - unoconv (for converting vector formats)")
        return False
    
    # Check for SVG conversion tools
    svg_tools = ['inkscape', 'pdf2svg', 'rsvg-convert']
    available_svg_tools = [tool for tool in svg_tools if shutil.which(tool)]
    
    if not available_svg_tools:
        logger.warning("No specialized SVG conversion tools found. SVG conversion may not work properly.")
        logger.warning("For better SVG conversion, consider installing one of these tools:")
        logger.warning("  - Inkscape (preferred)")
        logger.warning("  - pdf2svg")
        logger.warning("  - librsvg (for rsvg-convert)")
    else:
        logger.info(f"Found SVG conversion tools: {', '.join(available_svg_tools)}")
    
    return True


if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
    
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python convert_images.py <markdown_file> [use_svg]")
        print("  use_svg: Optional. Set to 'True' to convert vector images to SVG instead of PNG")
        sys.exit(1)
    
    md_file = sys.argv[1]
    use_svg = False
    
    if len(sys.argv) == 3:
        use_svg = sys.argv[2].lower() == 'true'
    
    if not os.path.isfile(md_file) or not md_file.endswith('.md'):
        logger.error(f"Invalid Markdown file: {md_file}")
        print("Please provide a valid Markdown file")
        sys.exit(1)
    
    if process_markdown_file(md_file, use_svg):
        logger.info(f"Successfully processed: {md_file}")
        sys.exit(0)
    else:
        logger.error(f"Failed to process: {md_file}")
        sys.exit(1)
