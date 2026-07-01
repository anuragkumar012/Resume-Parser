import fitz
from typing import Union, List, Tuple
from loguru import logger

def extract_text_from_pdf(pdf_source: Union[str, bytes]) -> str:
    """
    Extracts text from a PDF file path or PDF bytes using PyMuPDF (fitz).
    Handles multi-column layouts, tables, headers/footers, and unicode content.
    """
    try:
        if isinstance(pdf_source, bytes):
            doc = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            doc = fitz.open(pdf_source)
            
        full_text = []
        for page_idx, page in enumerate(doc):
            page_text = extract_page_text_layout_aware(page)
            full_text.append(page_text)
            
        doc.close()
        return "\n\n--- Page Break ---\n\n".join(full_text)
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise e

def extract_page_text_layout_aware(page: fitz.Page) -> str:
    """
    Extracts text from a single page by analyzing spatial blocks.
    Identifies multi-column sections vs full-width banners (headers/footers)
    and sorts them in reading order.
    """
    # Get page width
    rect = page.rect
    width = rect.width
    
    # Get text blocks: (x0, y0, x1, y1, text, block_no, block_type)
    # block_type == 0 is text, block_type == 1 is image
    blocks = page.get_text("blocks")
    
    # Filter text blocks
    text_blocks = [b for b in blocks if b[6] == 0]
    
    if not text_blocks:
        return page.get_text().strip()
        
    full_width_blocks = []
    left_column_blocks = []
    right_column_blocks = []
    
    midpoint = width / 2.0
    
    for block in text_blocks:
        x0, y0, x1, y1, text, _, _ = block
        b_width = x1 - x0
        
        # Check if block is full width (e.g. Header, Footer, Page Title, Full section spacer)
        if b_width > (width * 0.65):
            full_width_blocks.append(block)
        elif x1 <= midpoint + (width * 0.05):
            # Clearly in the left half
            left_column_blocks.append(block)
        elif x0 >= midpoint - (width * 0.05):
            # Clearly in the right half
            right_column_blocks.append(block)
        else:
            # Overlaps the middle, assign based on centroid
            centroid_x = (x0 + x1) / 2.0
            if centroid_x < midpoint:
                left_column_blocks.append(block)
            else:
                right_column_blocks.append(block)
                
    # Sort each group by y0 (top to bottom)
    left_column_blocks.sort(key=lambda b: b[1])
    right_column_blocks.sort(key=lambda b: b[1])
    assembled_text = []
    
    # We can interweave full-width and column blocks by processing from top to bottom
    all_blocks = list(text_blocks)
    
    # Sort full-width blocks by y0
    full_width_blocks.sort(key=lambda b: b[1])
    
    last_y = 0.0
    for fw_block in full_width_blocks:
        fw_x0, fw_y0, fw_x1, fw_y1, fw_text, _, _ = fw_block
        
        # Extract everything in the band [last_y, fw_y0]
        band_left = [b for b in left_column_blocks if last_y <= b[1] < fw_y0]
        band_right = [b for b in right_column_blocks if last_y <= b[1] < fw_y0]
        
        # Append left column, then right column in this band
        for b in band_left:
            assembled_text.append(b[4])
        for b in band_right:
            assembled_text.append(b[4])
            
        # Append the full width block
        assembled_text.append(fw_text)
        last_y = fw_y1
        
    # Append remaining blocks after the last full-width block
    remaining_left = [b for b in left_column_blocks if b[1] >= last_y]
    remaining_right = [b for b in right_column_blocks if b[1] >= last_y]
    
    for b in remaining_left:
        assembled_text.append(b[4])
    for b in remaining_right:
        assembled_text.append(b[4])
    processed_texts = set(assembled_text)
    for b in text_blocks:
        if b[4] not in processed_texts:
            # Insert sorted by Y
            assembled_text.append(b[4])
            
    # Clean and join
    cleaned_blocks = []
    for text in assembled_text:
        text_str = text.strip()
        if text_str:
            cleaned_blocks.append(text_str)
            
    result = "\n\n".join(cleaned_blocks)
    if not result.strip():
        return page.get_text().strip()
    return result
