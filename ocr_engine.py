import cv2
import numpy as np
import pytesseract

def order_points(pts):
    # Initialize a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype="float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def find_grid(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
        
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    img_area = image.shape[0] * image.shape[1]
    
    puzzle_contour = None
    
    for c in contours:
        area = cv2.contourArea(c)
        # Skip contours that are too small or take up the whole image
        if area > 0.99 * img_area or area < 0.05 * img_area:
            continue
            
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        
        # Sudoku grid is a square, so aspect ratio should be near 1.0
        if 0.8 <= aspect_ratio <= 1.2:
            puzzle_contour = c
            break
            
    if puzzle_contour is None:
        return None
        
    x, y, w, h = cv2.boundingRect(puzzle_contour)
    # Crop the grid
    warped = gray[y:y+h, x:x+w]
    return warped

def extract_cells(warped, size=6):
    cells = []
    h, w = warped.shape
    cell_h = h // size
    cell_w = w // size
    
    for i in range(size):
        row = []
        for j in range(size):
            y_start = i * cell_h
            y_end = (i + 1) * cell_h
            x_start = j * cell_w
            x_end = (j + 1) * cell_w
            
            cell = warped[y_start:y_end, x_start:x_end]
            row.append(cell)
        cells.append(row)
    return cells

def predict_digit(cell):
    h, w = cell.shape
    # Trim (15%) to avoid grid lines
    trim_y = int(h * 0.15)
    trim_x = int(w * 0.15)
    trimmed = cell[trim_y:h-trim_y, trim_x:w-trim_x]
    
    # Otsu's thresholding
    _, thresh = cv2.threshold(trimmed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return 0
        
    # Get the largest contour which should be the digit
    c = max(contours, key=cv2.contourArea)
    
    # If the contour is too small, it's just noise
    if cv2.contourArea(c) < 50:
        return 0
        
    x, y, cw, ch = cv2.boundingRect(c)
    
    # Extract just the digit
    digit = thresh[y:y+ch, x:x+cw]
    
    # Add substantial padding (tesseract likes this)
    padded = cv2.copyMakeBorder(digit, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=0)
    
    # Invert so digit is black on white background
    inverted = cv2.bitwise_not(padded)
    
    config = r'--oem 3 --psm 10 -c tessedit_char_whitelist=123456'
    
    # Try multiple scales for robustness
    for scale in [1, 2]:
        resized = cv2.resize(inverted, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        text = pytesseract.image_to_string(resized, config=config).strip()
        if text.isdigit() and 1 <= int(text) <= 6:
            return int(text)
            
    return 0

def extract_sudoku_from_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image at {image_path}")
        
    warped = find_grid(image)
    if warped is None:
        # If we can't find a grid, try processing the whole image as the grid
        warped = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
    cv2.imwrite('debug_warped.png', warped)
        
    cells = extract_cells(warped, size=6)
    
    grid = []
    for row in cells:
        grid_row = []
        for cell in row:
            digit = predict_digit(cell)
            grid_row.append(digit)
        grid.append(grid_row)
        
    return grid
