from flask import Flask, render_template, request, jsonify
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from ocr_engine import extract_sudoku_from_image
from solver import solve

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve_sudoku():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 1. Extract grid from image
            grid = extract_sudoku_from_image(filepath)
            
            if grid is None:
                return jsonify({'error': 'Could not detect a 6x6 Sudoku grid in the image.'}), 400
                
            original_grid = [row[:] for row in grid]
            
            # 2. Solve the grid (Try 3x2 format first, then 2x3 format)
            solved = False
            grid_copy_1 = [row[:] for row in grid]
            grid_copy_2 = [row[:] for row in grid]
            
            if solve(grid_copy_1, box_w=3, box_h=2):
                solved = True
                final_grid = grid_copy_1
            elif solve(grid_copy_2, box_w=2, box_h=3):
                solved = True
                final_grid = grid_copy_2

            if solved:
                return jsonify({
                    'success': True,
                    'original_grid': original_grid,
                    'solved_grid': final_grid
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No solution exists for the extracted grid. It might have misread numbers or invalid givens.',
                    'extracted_grid': original_grid
                })
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up the uploaded file
            # if os.path.exists(filepath):
            #     os.remove(filepath)
            pass

@app.route('/solve_manual', methods=['POST'])
def solve_manual():
    import json
    try:
        grid_str = request.form.get('grid')
        if not grid_str:
            return jsonify({'error': 'No grid provided'}), 400
            
        grid = json.loads(grid_str)
        original_grid = [row[:] for row in grid]
        
        solved = False
        grid_copy_1 = [row[:] for row in grid]
        grid_copy_2 = [row[:] for row in grid]
        
        if solve(grid_copy_1, box_w=3, box_h=2):
            solved = True
            final_grid = grid_copy_1
        elif solve(grid_copy_2, box_w=2, box_h=3):
            solved = True
            final_grid = grid_copy_2
            
        if solved:
            return jsonify({
                'success': True,
                'solved_grid': final_grid
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No solution exists for this edited grid. Check for contradictions.'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
