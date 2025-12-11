import cv2
import numpy as np
from PIL import Image, ImageChops, ImageStat
import io
import json
from typing import Optional, Dict, Any
from app.schemas import ForensicsResult
from app.config import config

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class ForensicsAgent:
    """
    Agent 1: Digital Forensics using Multiple Detection Methods.
    Uses ELA, Noise Variance Analysis, JPEG Quality Estimation,
    and Mistral LLM for intelligent pattern analysis to detect
    digitally manipulated certificates.
    """
    
    def __init__(self):
        """Initialize the forensics agent with LLM support."""
        self.llm_enabled = config.LLM_ENABLED and OLLAMA_AVAILABLE
        if self.llm_enabled:
            try:
                # Test Ollama connection
                ollama.list()
            except Exception as e:
                print(f"Warning: Ollama not available: {e}")
                self.llm_enabled = False

    def analyze(self, image_bytes: bytes) -> ForensicsResult:
        try:
            original_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Multi-layered detection approach
            ela_score, ela_details = self._perform_ela(original_image)
            noise_score, noise_details = self._analyze_noise_variance(original_image)
            quality_score, quality_details = self._estimate_compression_quality(original_image)
            
            # Combine all detection methods
            # Balanced weighting to avoid over-sensitivity
            combined_score = (ela_score * 0.5) + (noise_score * 0.30) + (quality_score * 0.20)
            
            debug_metadata = ela_details + noise_details + quality_details
            debug_metadata.append(f"Combined Score: {combined_score:.2f}")

            # --- LLM ANALYSIS INTEGRATION ---
            llm_analysis = None
            llm_risk_score = None
            llm_confidence = None
            llm_reasoning = None
            
            if self.llm_enabled:
                llm_result = self._analyze_with_llm(
                    ela_score=ela_score,
                    noise_score=noise_score,
                    quality_score=quality_score,
                    combined_score=combined_score,
                    details=debug_metadata
                )
                if llm_result:
                    llm_analysis = llm_result.get("analysis")
                    llm_risk_score = llm_result.get("risk_score")
                    llm_confidence = llm_result.get("confidence")
                    llm_reasoning = llm_result.get("reasoning")
                    
                    # Adjust combined score based on LLM insight (60% traditional + 40% LLM)
                    if llm_risk_score is not None:
                        combined_score = (combined_score * 0.6) + (llm_risk_score * 0.4)
                        debug_metadata.append(f"LLM-Adjusted Score: {combined_score:.2f}")

            # --- IMPROVED SENSITIVITY LOGIC ---
            # Fake certificates typically show:
            # 1. High ELA scores (inconsistent compression artifacts)
            # 2. High noise variance (pasted elements have different noise patterns)
            # 3. Quality inconsistencies (re-compressed multiple times)
            
            # Primary threshold - combined score (lenient to reduce false positives)
            # Most legitimate certificates score below 0.75
            is_high_risk = combined_score > 0.75
            
            
            # Additional strong indicators - flag only if EXTREMELY high scores
            # This catches obvious manipulations while allowing normal variations
            if ela_score > 0.95:
                # ELA alone is extremely high - clear manipulation
                is_high_risk = True
            elif combined_score > 0.65 and ela_score > 0.75:
                # High combined score with elevated ELA suggests manipulation
                is_high_risk = True

            # LLM override: If LLM has very high confidence in its assessment, consider it
            if llm_confidence is not None and llm_confidence > 0.85:
                if llm_risk_score is not None and llm_risk_score > 0.80:
                    is_high_risk = True
                    debug_metadata.append("LLM High Confidence Override: HIGH RISK")

            status = "Pass - Integrity Intact"
            if is_high_risk:
                status = "High Risk - Possible Digital Manipulation Detected"
            elif combined_score > 0.50:
                status = "Warning - Minor Anomalies Detected"
            
            # Include LLM reasoning in status if available
            if llm_reasoning and is_high_risk:
                status += f" | LLM Insight: {llm_reasoning[:100]}"

            return ForensicsResult(
                manipulation_score=float(round(combined_score, 2)),
                is_high_risk=is_high_risk,
                status=status,
                details=debug_metadata,
                llm_analysis=llm_analysis,
                llm_risk_score=float(round(llm_risk_score, 2)) if llm_risk_score else None,
                llm_confidence=float(round(llm_confidence, 2)) if llm_confidence else None,
                llm_reasoning=llm_reasoning
            )

        except Exception as e:
            return ForensicsResult(
                manipulation_score=0.0,
                is_high_risk=False,
                status=f"Error analyzing image: {str(e)}",
                details=[str(e)]
            )

    def _analyze_with_llm(
        self, 
        ela_score: float, 
        noise_score: float, 
        quality_score: float, 
        combined_score: float,
        details: list
    ) -> Optional[Dict[str, Any]]:
        """
        Uses Mistral LLM to intelligently analyze forensic metrics and provide
        enhanced detection through pattern recognition and contextual reasoning.
        
        Args:
            ela_score: Error Level Analysis score (0-1)
            noise_score: Noise variance inconsistency score (0-1)
            quality_score: Compression quality anomaly score (0-1)
            combined_score: Weighted combination of all scores
            details: Detailed metrics from forensic analysis
            
        Returns:
            Dictionary containing LLM analysis, risk score, confidence, and reasoning
        """
        try:
            # Construct intelligent prompt with forensic context
            prompt = f"""You are an expert digital forensics analyst specializing in certificate forgery detection. Analyze the following forensic metrics from a certificate image:

FORENSIC METRICS:
- Error Level Analysis (ELA) Score: {ela_score:.2f} (0=consistent compression, 1=inconsistent/manipulated)
- Noise Variance Score: {noise_score:.2f} (0=uniform noise, 1=inconsistent noise patterns)
- Compression Quality Score: {quality_score:.2f} (0=single compression, 1=multiple re-compressions)
- Combined Traditional Score: {combined_score:.2f}

DETAILED ANALYSIS:
{chr(10).join(details[:10])}

TASK:
Analyze these metrics to determine if this certificate shows signs of digital manipulation (photoshopping, text replacement, etc.).

KEY INDICATORS OF FORGERY:
1. High ELA scores (>0.7) suggest inconsistent compression artifacts from copy-paste manipulation
2. High noise variance (>0.6) suggests elements from different sources pasted together
3. High quality scores (>0.6) suggest multiple re-compressions typical of edited documents
4. Localized anomalies (small-scale outliers) often indicate text replacement

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "risk_score": <float 0-1, your assessment of forgery likelihood>,
    "confidence": <float 0-1, your confidence in this assessment>,
    "reasoning": "<brief explanation of key red flags or lack thereof>",
    "analysis": "<detailed technical analysis>"
}}

Be conservative: Real certificates may have minor variations. Only flag as high-risk if multiple strong indicators align."""

            # Call Mistral via Ollama
            response = ollama.generate(
                model=config.LLM_MODEL,
                prompt=prompt,
                options={
                    "temperature": config.LLM_TEMPERATURE,
                    "num_predict": config.LLM_MAX_TOKENS,
                }
            )
            
            # Parse response
            if response and 'response' in response:
                response_text = response['response'].strip()
                
                # Extract JSON from response (handle markdown code blocks)
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '```' in response_text:
                    json_start = response_text.find('```') + 3
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                # Parse JSON
                result = json.loads(response_text)
                
                # Validate and return
                if all(k in result for k in ["risk_score", "confidence", "reasoning", "analysis"]):
                    return {
                        "risk_score": float(result["risk_score"]),
                        "confidence": float(result["confidence"]),
                        "reasoning": str(result["reasoning"]),
                        "analysis": str(result["analysis"])
                    }
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"LLM JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return None


    def _perform_ela(self, original: Image.Image) -> tuple:
        """
        Multi-scale Error Level Analysis to detect both global and localized manipulation.
        Uses two block sizes: larger blocks for context, smaller blocks for precise detection.
        """
        # 1. Save compressed version to memory (Simulate 90% quality)
        buffer = io.BytesIO()
        original.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)
        resaved = Image.open(buffer)

        # 2. Calculate Difference (The ELA Noise Map)
        ela_image = ImageChops.difference(original, resaved)
        
        # 3. Convert to grayscale numpy array for statistical analysis
        ela_data = np.array(ela_image.convert('L')).astype(float)
        h, w = ela_data.shape
        
        # 4. MULTI-SCALE ANALYSIS
        # Use two different block sizes to catch both global and localized anomalies
        
        # Scale 1: Larger blocks (32x32) for overall pattern
        large_block_size = 32
        large_block_means = []
        
        for y in range(0, h, large_block_size):
            for x in range(0, w, large_block_size):
                block = ela_data[y:y+large_block_size, x:x+large_block_size]
                if block.size > 0:
                    large_block_means.append(np.mean(block))
        
        large_block_means = np.array(large_block_means)
        
        # Scale 2: Smaller blocks (16x16) for localized text manipulation
        small_block_size = 16
        small_block_means = []
        small_block_maxs = []
        
        for y in range(0, h, small_block_size):
            for x in range(0, w, small_block_size):
                block = ela_data[y:y+small_block_size, x:x+small_block_size]
                if block.size > 0:
                    small_block_means.append(np.mean(block))
                    small_block_maxs.append(np.max(block))
        
        small_block_means = np.array(small_block_means)
        small_block_maxs = np.array(small_block_maxs)
        
        if large_block_means.size == 0 or small_block_means.size == 0:
            return 0.0, ["Image too small for ELA analysis"]

        # 5. Statistical Analysis on BOTH scales
        # Large blocks provide the baseline/context
        large_median = np.median(large_block_means)
        large_mean = np.mean(large_block_means)
        large_std = np.std(large_block_means)
        
        # Small blocks detect localized anomalies
        small_median = np.median(small_block_means)
        small_mean = np.mean(small_block_means)
        small_std = np.std(small_block_means)
        small_max = np.max(small_block_means)
        
        anomaly_score = 0.0
        details = []

        # Enhanced detection logic
        if large_median < 4.0:  # Digital file with low background noise
            # LOCALIZED MANIPULATION DETECTION
            # Key insight: Fake certificates have small regions with different error patterns
            
            # Strategy 1: Small-scale outlier detection
            # Count small blocks that are significantly above the large-scale baseline
            small_outlier_threshold = large_mean + 2.0 * large_std
            small_outliers = np.sum(small_block_means > small_outlier_threshold)
            small_outlier_ratio = small_outliers / len(small_block_means)
            localized_score = min(small_outlier_ratio * 8.0, 1.0)  # Sensitive to small regions
            
            # Strategy 2: Cross-scale consistency check
            # Compare variability at different scales - manipulation shows inconsistency
            if large_std > 0.01:
                scale_ratio = small_std / large_std
                # If small-scale variability is much higher, suggests localized manipulation
                scale_inconsistency = max(0, (scale_ratio - 1.0) / 2.0)
                scale_score = min(scale_inconsistency, 1.0)
            else:
                scale_score = 0.0
            
            # Strategy 3: Extreme value detection at small scale
            # Localized manipulation creates extreme values in small blocks
            extreme_deviation = small_max - small_median
            extreme_score = min(extreme_deviation / 3.0, 1.0)
            
            # Strategy 4: Small-scale coefficient of variation
            if small_mean > 0.01:
                small_cv = small_std / small_mean
                cv_score = min(small_cv / 3.5, 1.0)
            else:
                cv_score = 0.0
            
            # Strategy 5: Percentile analysis on small blocks
            small_p95 = np.percentile(small_block_means, 95)
            small_p75 = np.percentile(small_block_means, 75)
            small_p50 = np.percentile(small_block_means, 50)
            
            # Large gap between p95 and p75 suggests a few anomalous blocks
            percentile_gap = small_p95 - small_p75
            gap_score = min(percentile_gap / 1.5, 1.0)
            
            # Strategy 6: Maximum block value analysis
            max_of_small_maxs = np.max(small_block_maxs)
            median_of_small_maxs = np.median(small_block_maxs)
            max_deviation = max_of_small_maxs - median_of_small_maxs
            max_score = min(max_deviation / 6.0, 1.0)
            
            # WEIGHTED COMBINATION - emphasize localized detection
            anomaly_score = (
                localized_score * 0.30 +    # Outliers in small blocks (most important)
                extreme_score * 0.25 +      # Extreme values (second most important)
                gap_score * 0.20 +          # Percentile gap
                cv_score * 0.15 +           # Coefficient of variation
                max_score * 0.10 +          # Max deviation
                scale_score * 0.00          # Cross-scale (experimental, not weighted for now)
            )
            
            # Strong evidence threshold - if multiple indicators are moderate-high, flag it
            strong_indicators = sum([
                localized_score > 0.55,  # Slightly more conservative
                extreme_score > 0.50,
                gap_score > 0.50,
                cv_score > 0.60,
                max_score > 0.60
            ])
            
            # Flag if we have 4+ strong indicators (stricter)
            if strong_indicators >= 4:
                anomaly_score = max(anomaly_score, 0.55)
            
            details.append(f"ELA: Multi-scale analysis - Large blocks: {len(large_block_means)}, Small blocks: {len(small_block_means)}")
            details.append(f"ELA: Small-scale outliers: {small_outlier_ratio*100:.1f}%")
            details.append(f"ELA: Extreme deviation: {extreme_deviation:.2f}")
            details.append(f"ELA: P95-P75 gap: {percentile_gap:.2f}")
            details.append(f"ELA: Small CV: {small_cv:.2f}")
            details.append(f"ELA: Scores - Localized:{localized_score:.2f} Extreme:{extreme_score:.2f} Gap:{gap_score:.2f} CV:{cv_score:.2f} Max:{max_score:.2f}")

        else:  # Scanned or compressed file
            # For scans, we need to see much stronger anomalies
            diff = small_max - large_median
            anomaly_score = min(diff / 30.0, 1.0)
            details.append(f"ELA: Scan Mode - Max deviation: {diff:.2f}")

        return anomaly_score, details


    def _analyze_noise_variance(self, original: Image.Image) -> tuple:
        """
        Analyzes noise patterns across the image.
        Manipulated images often have inconsistent noise patterns where
        different elements were pasted from different sources.
        """
        # Convert to numpy array
        img_array = np.array(original)
        
        # Split into regions and analyze noise variance
        h, w, _ = img_array.shape
        region_size = 64
        
        noise_variances = []
        
        for y in range(0, h, region_size):
            for x in range(0, w, region_size):
                region = img_array[y:y+region_size, x:x+region_size]
                if region.size > 0:
                    # Calculate local noise estimate using high-frequency components
                    gray_region = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
                    # Apply Laplacian to extract noise
                    laplacian = cv2.Laplacian(gray_region, cv2.CV_64F)
                    variance = np.var(laplacian)
                    noise_variances.append(variance)
        
        if len(noise_variances) == 0:
            return 0.0, ["Noise: Image too small"]
        
        noise_variances = np.array(noise_variances)
        
        # Calculate statistics
        median_var = np.median(noise_variances)
        std_var = np.std(noise_variances)
        
        # High standard deviation in noise variance suggests manipulation
        # Normalize by median to get relative inconsistency
        if median_var > 0:
            inconsistency_score = min((std_var / median_var) / 10.0, 1.0)
        else:
            inconsistency_score = 0.0
        
        details = [f"Noise: Variance inconsistency: {inconsistency_score:.2f}"]
        
        return inconsistency_score, details

    def _estimate_compression_quality(self, original: Image.Image) -> tuple:
        """
        Estimates JPEG compression quality and detects re-compression.
        Fake certificates are often re-compressed multiple times,
        leading to quality degradation patterns.
        """
        # Convert to numpy for analysis
        img_array = np.array(original)
        
        # Compress at different quality levels and measure similarity
        qualities_to_test = [95, 90, 85, 80, 75]
        similarities = []
        
        for quality in qualities_to_test:
            buffer = io.BytesIO()
            original.save(buffer, format='JPEG', quality=quality)
            buffer.seek(0)
            compressed = Image.open(buffer)
            
            # Calculate mean squared error
            compressed_array = np.array(compressed)
            mse = np.mean((img_array.astype(float) - compressed_array.astype(float)) ** 2)
            similarities.append((quality, mse))
        
        # Find the quality level with minimum MSE
        min_mse_quality = min(similarities, key=lambda x: x[1])
        estimated_quality = min_mse_quality[0]
        
        # Also check for blockiness (8x8 DCT artifacts)
        # which become more pronounced with multiple compressions
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Simple blockiness detection using gradients
        grad_y, grad_x = np.gradient(gray.astype(float))
        
        # Count gradient peaks at 8-pixel intervals (JPEG block boundaries)
        block_size = 8
        h, w = gray.shape
        boundary_strength = 0.0
        
        for i in range(block_size, w, block_size):
            boundary_strength += np.mean(np.abs(grad_x[:, i]))
        for j in range(block_size, h, block_size):
            boundary_strength += np.mean(np.abs(grad_y[j, :]))
        
        # Normalize
        boundary_strength /= (h + w)
        
        # Higher blockiness suggests multiple compressions (manipulation)
        blockiness_score = min(boundary_strength / 2.0, 1.0)
        
        # Lower estimated quality also suggests manipulation
        quality_score = 0.0
        if estimated_quality < 85:
            quality_score = (95 - estimated_quality) / 50.0
        
        combined_quality_score = max(blockiness_score, quality_score)
        
        details = [
            f"Quality: Estimated JPEG quality: {estimated_quality}%",
            f"Quality: Blockiness score: {blockiness_score:.2f}"
        ]
        
        return combined_quality_score, details