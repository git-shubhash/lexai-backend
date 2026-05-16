
import logging
import sys
import os

# Mock the environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from services.extraction_service import extract_text
    print("SUCCESS: extraction_service imported correctly.")
    
    # Try a mock extraction
    res = extract_text(b"mock content", "test.txt")
    print(f"Test Extraction Result: {res['success']}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
