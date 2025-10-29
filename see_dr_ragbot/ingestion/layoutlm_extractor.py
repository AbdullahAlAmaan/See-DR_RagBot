"""LayoutLMv3 integration for layout-aware PDF extraction"""
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import os

try:
    from transformers import AutoProcessor, AutoModelForTokenClassification
    from PIL import Image
    import pdf2image
    import torch
    _LAYOUTLM_AVAILABLE = True
except Exception as e:
    _LAYOUTLM_AVAILABLE = False
    _LAYOUTLM_ERROR = str(e)

from ..logging_utils import get_logger

logger = get_logger(__name__)


def extract_with_layoutlm(
    pdf_path: str,
    model_name: str = "microsoft/layoutlmv3-base",
) -> Tuple[str, List[Dict]]:
    """
    Extract text with LayoutLMv3 layout awareness.
    Returns (full_text, page_elements) where elements have layout metadata.
    """
    if not _LAYOUTLM_AVAILABLE:
        raise RuntimeError(f"LayoutLM not available: {_LAYOUTLM_ERROR}")
    
    try:
        processor = AutoProcessor.from_pretrained(model_name, apply_ocr=True)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        
        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path, dpi=200)
        
        all_elements: List[Dict] = []
        all_text: List[str] = []
        
        for page_num, image in enumerate(images, start=1):
            encoding = processor(image, return_tensors="pt", max_length=512)
            
            with torch.no_grad():
                outputs = model(**encoding)
            
            # Extract text with layout info (simplified - full impl would parse bounding boxes)
            # For now, fallback to structure extraction via OCR + layout hints
            text = processor.tokenizer.decode(encoding["input_ids"][0], skip_special_tokens=True)
            
            all_elements.append({
                "text": text,
                "metadata": {
                    "page_number": page_num,
                    "layout_type": "paragraph",  # Would be refined with actual box parsing
                }
            })
            all_text.append(text)
        
        return "\n\n".join(all_text), all_elements
    
    except Exception as e:
        logger.warning(f"LayoutLM extraction failed for {os.path.basename(pdf_path)}: {e}")
        raise

