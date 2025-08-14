#!/bin/bash

# Function to display usage information
show_usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -c, --clean-only    Clean old files without processing new ones"
    echo "  -s, --skip-images   Skip image conversion step"
    echo "  -v, --vector-svg    Convert vector to SVG instead"
    echo "  -h, --help          Show this help message"
}

# Parse command line arguments
CLEAN_ONLY=false
SKIP_IMAGES=false
VECTOR_SVG=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean-only)
            CLEAN_ONLY=true
            shift
            ;;
        -s|--skip-images)
            SKIP_IMAGES=true
            shift
            ;;
        -v|--vector-svg)
            VECTOR_SVG=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Clean up old files
echo "Cleaning up old files..."

# Remove old output files
if [ -d "output" ]; then
    echo "Removing old output files..."
    rm -rf output/*
fi

# Remove old image directories
if [ -d "images" ]; then
    echo "Removing old image directories..."
    rm -rf images/*
fi

# Remove old marked source files
if [ -d "source_marked" ]; then
    echo "Removing old marked files..."
    rm -rf source_marked/*.docx
fi

# Create directories if they don't exist
mkdir -p output
mkdir -p images
mkdir -p source_marked

# Exit if clean-only mode is enabled
if [ "$CLEAN_ONLY" = true ]; then
    echo "Cleanup completed. Exiting without processing files."
    exit 0
fi

# Check for required dependencies for image conversion
if [ "$SKIP_IMAGES" = false ]; then
    echo "Checking image conversion dependencies..."
    if ! command -v convert &> /dev/null; then
        echo "WARNING: ImageMagick 'convert' command not found. Image conversion may fail."
        echo "Install with: apt-get install imagemagick"
    fi
    
    if ! command -v unoconv &> /dev/null; then
        echo "WARNING: 'unoconv' command not found. Vector image conversion may fail."
        echo "Install with: apt-get install unoconv libreoffice"
    fi
fi

# Process all .docx files in source directory
for file in source/*.docx; do
    if [ -f "$file" ]; then
        filename=$(basename -- "$file")
        name="${filename%.*}"
        
        # Create a sanitized version of the name (replace spaces with underscores)
        sanitized_name=$(echo "$name" | tr ' ' '_')
        
        echo "=========================================="
        echo "Processing $filename..."
        echo "=========================================="
        
        # Create image directory with sanitized name
        mkdir -p "images/$sanitized_name"

        # Before the Pandoc conversion
        echo "Step 1: Extraction and insertion of the markers inside the docx"
        python3 scripts/extract_and_mark_inplace.py "$file" "source_marked/${sanitized_name}_marked.docx" "output/${sanitized_name}_codeblocks.json"

        echo "Step 2: Initial conversion with Pandoc on the marked docx"
        if ! pandoc -f docx -t gfm \
          --wrap=none \
          --extract-media="./images/$sanitized_name" \
          --standalone \
          "source_marked/${sanitized_name}_marked.docx" -o "output/${sanitized_name}_raw.md"; then
            
            echo "Pandoc conversion failed. Trying alternative methods..."
            
            # Call the fallback converter
            if ! python3 scripts/convert_problematic_docx.py "$file" "output/${sanitized_name}_raw.md" "./images/$sanitized_name"; then
                echo "ERROR: All conversion methods failed for $filename"
                echo "Skipping to next file..."
                continue
            fi
        fi
        
        echo "Step 3: Preserving tables as HTML"
        python3 scripts/preserve_tables.py "output/${sanitized_name}_raw.md" "output/${sanitized_name}_tables_fixed.md"

        echo "Step 4: Fixing table of contents"
        python3 scripts/fix_toc.py "output/${sanitized_name}_tables_fixed.md" "output/${sanitized_name}_toc_fixed.md"

        echo "Step 5: Fixing section numbering"
        python3 scripts/fix_section_numbering.py "output/${sanitized_name}_toc_fixed.md" "output/${sanitized_name}_sections_fixed.md"

        echo "Step 6: Fixing image paths"
        python3 scripts/fix_image_paths.py "output/${sanitized_name}_sections_fixed.md" "output/${sanitized_name}_images_fixed.md"

        # Convert problematic images (EMF, WMF, GIF) to PNG or SVG
        if [ "$SKIP_IMAGES" = false ]; then
            if [ "$VECTOR_SVG" = true ]; then
                echo "Step 7: Converting problematic images to SVG"
                python3 scripts/convert_images.py "output/${sanitized_name}_images_fixed.md" "True"
            else
                echo "Step 7: Converting problematic images to PNG"
                python3 scripts/convert_images.py "output/${sanitized_name}_images_fixed.md" "False"
            fi
            
            # If the conversion was successful, copy the result to final
            if [ $? -eq 0 ]; then
                cp "output/${sanitized_name}_images_fixed.md" "output/${sanitized_name}_final.md"
            else
                echo "WARNING: Image conversion failed. Using previous version as final."
                cp "output/${sanitized_name}_images_fixed.md" "output/${sanitized_name}_final.md"
            fi
        else
            # Skip image conversion, just copy the file
            cp "output/${sanitized_name}_images_fixed.md" "output/${sanitized_name}_final.md"
        fi
        
        # Putting back the code blocks inside the markdown
        echo "Step 8: Injecting the code blocks inside the final markdown"
        python3 scripts/inject_code_blocks.py "output/${sanitized_name}_final.md" "output/${sanitized_name}_codeblocks.json"

        echo "Completed processing $filename"
        echo "Final output: output/${sanitized_name}_final.md"
        echo ""
    fi
done

echo "All documents processed!"
