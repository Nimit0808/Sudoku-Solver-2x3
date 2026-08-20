import sys
from ocr_engine import extract_sudoku_from_image

try:
    grid = extract_sudoku_from_image('uploads/Screenshot_2026-08-20_at_3.37.14_PM.png')
    for row in grid:
        print(row)
except Exception as e:
    print(f"Error: {e}")


