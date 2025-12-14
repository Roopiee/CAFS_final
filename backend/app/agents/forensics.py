"""
forensics.py
Enhanced forensics agent with ELA + TruFor cascade
"""

import cv2
import numpy as np
from PIL import Image
import io
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

class ForensicsAgent:
    """
    Enhanced forensics agent with multi-stage detection:
    1. Quick ELA check (1-2s)
    2. Deep TruFor check if suspicious (3-5s)
    """
    
    def __init__(self, use_trufor: bool = True):
        """
        Initialize forensics agent
        
        Args:
            use_trufor: Whether to use TruFor for deep analysis
        """
        self.use_trufor = use_trufor
        self.trufor_detector = None
        
        if use_trufor:
            try:
                from app.agents.trufor_detector import TruForDetector
                self.trufor_detector = TruForDetector()
                logger.info("✓ TruFor detector initialized")
            except Exception as e:
                logger.warning(f"TruFor not available: {e}. Falling back to ELA only.")
                self.use_trufor = False
    
    def _ela_analysis(self, image_bytes: bytes, quality: int = 90) -> Dict:
        """
        Error Level Analysis - Fast manipulation detection
        
        Args:
            image_bytes: Image data
            quality: JPEG quality for recompression
            
        Returns:
            dict with ELA results
        """
        try:
            start_time = time.time()
            
            # Load image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save with specified quality
            temp_buffer = io.BytesIO()
            img.save(temp_buffer, format='JPEG', quality=quality)
            temp_buffer.seek(0)
            
            # Reload compressed image
            compressed_img = Image.open(temp_buffer)
            
            # Calculate difference
            img_array = np.array(img, dtype=np.float32)
            compressed_array = np.array(compressed_img, dtype=np.float32)
            
            # ELA difference
            diff = np.abs(img_array - compressed_array)
            
            # Normalize to 0-255
            diff_normalized = (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)
            
            # Calculate statistics
            mean_diff = np.mean(diff)
            max_diff = np.max(diff)
            std_diff = np.std(diff)
            
            # Calculate suspicious regions (high diff areas)
            threshold = mean_diff + 2 * std_diff
            suspicious_pixels = np.sum(diff > threshold)
            total_pixels = diff.size
            suspicious_ratio = suspicious_pixels / total_pixels
            
            # Calculate score (0-1)
            ela_score = min(suspicious_ratio * 10, 1.0)  # Scale and cap at 1.0
            
            elapsed = time.time() - start_time
            
            logger.info(f"ELA analysis: score={ela_score:.3f}, time={elapsed:.2f}s")
            
            return {
                'method': 'ela',
                'score': ela_score,
                'mean_diff': float(mean_diff),
                'max_diff': float(max_diff),
                'std_diff': float(std_diff),
                'suspicious_ratio': float(suspicious_ratio),
                'processing_time': elapsed,
                'is_suspicious': ela_score > 0.4  # Threshold for triggering TruFor
            }
            
        except Exception as e:
            logger.error(f"ELA analysis failed: {e}")
            return {
                'method': 'ela',
                'score': 0.0,
                'error': str(e),
                'is_suspicious': False
            }
    
    def _metadata_check(self, image_bytes: bytes) -> Dict:
        """
        Check image metadata for manipulation signs
        
        Returns:
            dict with metadata analysis
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Get EXIF data
            exif_data = img.getexif() if hasattr(img, 'getexif') else {}
            
            # Check for editing software
            software_tags = [271, 305]  # Make, Software tags
            editing_software = []
            
            for tag in software_tags:
                if tag in exif_data:
                    software = str(exif_data[tag]).lower()
                    if any(editor in software for editor in ['photoshop', 'gimp', 'paint', 'editor']):
                        editing_software.append(exif_data[tag])
            
            has_editor_metadata = len(editing_software) > 0
            
            return {
                'method': 'metadata',
                'has_exif': len(exif_data) > 0,
                'editing_software_detected': has_editor_metadata,
                'software_list': editing_software,
                'suspicious': has_editor_metadata
            }
            
        except Exception as e:
            logger.error(f"Metadata check failed: {e}")
            return {
                'method': 'metadata',
                'error': str(e),
                'suspicious': False
            }
    
    def analyze(self, image_bytes: bytes) -> Dict:
        """
        Comprehensive forensics analysis with smart cascade
        
        Flow:
        1. Metadata check (instant)
        2. ELA analysis (1-2s)
        3. If suspicious → TruFor deep analysis (3-5s)
        
        Args:
            image_bytes: Image data
            
        Returns:
            Complete forensics report
        """
        start_time = time.time()
        
        logger.info("🔍 Starting forensics analysis...")
        
        # Stage 1: Metadata check
        metadata_result = self._metadata_check(image_bytes)
        
        # Stage 2: ELA analysis
        ela_result = self._ela_analysis(image_bytes)
        
        # Stage 3: TruFor (if suspicious and available)
        trufor_result = None
        if self.use_trufor and ela_result.get('is_suspicious', False):
            logger.info("📊 ELA suspicious → Running TruFor deep analysis...")
            try:
                trufor_result = self.trufor_detector.detect(image_bytes)
            except Exception as e:
                logger.error(f"TruFor analysis failed: {e}")
                trufor_result = {'error': str(e)}
        
        # Combine results
        total_time = time.time() - start_time
        
        # Calculate final score
        final_score = ela_result.get('score', 0.0)
        
        if trufor_result and 'manipulation_score' in trufor_result:
            # Weight TruFor more heavily (it's more accurate)
            final_score = (ela_result.get('score', 0.0) * 0.3 + 
                          trufor_result.get('manipulation_score', 0.0) * 0.7)
        
        # Determine verdict
        is_high_risk = final_score > 0.65
        
        # Build status message
        if is_high_risk:
            status = "High Risk - Possible Digital Manipulation Detected"
        elif final_score > 0.4:
            status = "Medium Risk - Some Irregularities Detected"
        else:
            status = "Pass - Integrity Intact"
        
        # Build details list
        details = []
        details.append(f"ELA Score: {ela_result.get('score', 0):.2f}")
        
        if trufor_result:
            details.append(f"TruFor Score: {trufor_result.get('manipulation_score', 0):.2f}")
            details.append(f"Analysis Method: ELA + TruFor Deep Learning")
        else:
            details.append(f"Analysis Method: ELA (Fast Check)")
        
        if metadata_result.get('editing_software_detected'):
            details.append(f"Editing software detected: {', '.join(metadata_result.get('software_list', []))}")
        
        details.append(f"Processing time: {total_time:.2f}s")
        
        logger.info(f"✓ Forensics complete: score={final_score:.3f}, status={status}")
        
        return {
            'manipulation_score': final_score,
            'is_high_risk': is_high_risk,
            'status': status,
            'details': details,
            'ela_analysis': ela_result,
            'trufor_analysis': trufor_result,
            'metadata_analysis': metadata_result,
            'processing_time': total_time,
            'methods_used': ['metadata', 'ela'] + (['trufor'] if trufor_result else [])
        }