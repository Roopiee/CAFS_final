"""
Test script for Mistral LLM integration in forensics.py
Tests both with and without LLM to verify fallback behavior.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.forensics import ForensicsAgent
from pathlib import Path


def test_forensics_agent():
    """Test the ForensicsAgent with sample certificates."""
    print("="*70)
    print("TESTING FORENSICS AGENT WITH LLM INTEGRATION")
    print("="*70)
    
    # Initialize agent
    print("\n1. Initializing ForensicsAgent...")
    agent = ForensicsAgent()
    print(f"   LLM Enabled: {agent.llm_enabled}")
    
    # Find sample certificates
    project_root = Path(__file__).parent.parent
    sample_files = [
        project_root / "roopakcftmlsample.pdf",
        project_root / "samplecourseracft.pdf",
        project_root / "sampleudemycft.pdf",
        project_root / "fakecft.pdf"
    ]
    
    # Also check for converted JPG images
    jpg_dir = project_root / "jpgconvertedimgs"
    if jpg_dir.exists():
        sample_files.extend(list(jpg_dir.glob("*.jpg")))
    
    # Filter to existing files
    existing_files = [f for f in sample_files if f.exists()]
    
    if not existing_files:
        print("\n⚠️  No sample certificates found. Please add sample files:")
        print("   - roopakcftmlsample.pdf")
        print("   - samplecourseracft.pdf")
        print("   - sampleudemycft.pdf")
        print("   - fakecft.pdf")
        return
    
    print(f"\n2. Found {len(existing_files)} sample file(s)")
    
    # Test each file
    for idx, file_path in enumerate(existing_files, 1):
        print(f"\n{'-'*70}")
        print(f"TEST {idx}/{len(existing_files)}: {file_path.name}")
        print(f"{'-'*70}")
        
        try:
            # Read file
            if file_path.suffix.lower() == '.pdf':
                # For PDF, convert first page to image
                from pdf2image import convert_from_path
                from io import BytesIO
                
                images = convert_from_path(str(file_path))
                if images:
                    img_byte_arr = BytesIO()
                    images[0].save(img_byte_arr, format='PNG')
                    image_bytes = img_byte_arr.getvalue()
                else:
                    print("   ❌ Failed to convert PDF")
                    continue
            else:
                # For images, read directly
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
            
            # Analyze
            print("   Analyzing...")
            result = agent.analyze(image_bytes)
            
            # Display results
            print(f"\n   📊 RESULTS:")
            print(f"   Manipulation Score: {result.manipulation_score:.2f}")
            print(f"   High Risk: {'⚠️  YES' if result.is_high_risk else '✅ NO'}")
            print(f"   Status: {result.status}")
            
            if result.llm_analysis:
                print(f"\n   🤖 LLM ANALYSIS:")
                print(f"   Risk Score: {result.llm_risk_score:.2f}")
                print(f"   Confidence: {result.llm_confidence:.2f}")
                print(f"   Reasoning: {result.llm_reasoning}")
                print(f"\n   Full Analysis:")
                # Wrap text for readability
                analysis_lines = result.llm_analysis.split('. ')
                for line in analysis_lines:
                    if line.strip():
                        print(f"   {line.strip()}.")
            else:
                print(f"\n   ℹ️  LLM analysis not available (Ollama may not be running)")
            
            print(f"\n   📝 DETAILS:")
            for detail in result.details[-5:]:  # Show last 5 details
                print(f"   - {detail}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}")
    
    # Summary
    print("\n📋 SUMMARY:")
    if agent.llm_enabled:
        print("✅ LLM integration is working!")
        print("   Your forensics agent is enhanced with AI-powered analysis.")
    else:
        print("⚠️  LLM integration is disabled or unavailable.")
        print("   The agent is using traditional forensic methods only.")
        print("\n   To enable LLM:")
        print("   1. Install Ollama: brew install ollama (macOS)")
        print("   2. Start Ollama: ollama serve")
        print("   3. Pull Mistral: ollama pull mistral")
        print("   4. Restart this script")


if __name__ == "__main__":
    test_forensics_agent()
