def print_grid(grid):
    for i in range(6):
        if i % 2 == 0 and i != 0:
            print("- - - - - - - - - - -")
        for j in range(6):
            if j % 3 == 0 and j != 0:
                print("| ", end="")
            print(str(grid[i][j]) + " ", end="")
        print()

def find_empty(grid):
    for i in range(6):
        for j in range(6):
            if grid[i][j] == 0:
                return (i, j)
    return None

def is_valid(grid, num, pos, box_w=3, box_h=2):
    # Check row
    for j in range(6):
        if grid[pos[0]][j] == num and pos[1] != j:
            return False

    # Check column
    for i in range(6):
        if grid[i][pos[1]] == num and pos[0] != i:
            return False

    # Check box
    box_x = pos[1] // box_w
    box_y = pos[0] // box_h

    for i in range(box_y * box_h, box_y * box_h + box_h):
        for j in range(box_x * box_w, box_x * box_w + box_w):
            if grid[i][j] == num and (i, j) != pos:
                return False

    return True

def solve(grid, box_w=3, box_h=2):
    find = find_empty(grid)
    if not find:
        return True
    else:
        row, col = find

    for i in range(1, 7):
        if is_valid(grid, i, (row, col), box_w, box_h):
            grid[row][col] = i

            if solve(grid, box_w, box_h):
                return True

            grid[row][col] = 0

    return False

if __name__ == "__main__":
    # Example usage. 
    # 0 represents empty cells.
    # Note: The grid from the image has contradictions (e.g. multiple 5s in column 3, and conflicting 2s in column 4) 
    # and cannot be solved as is.
    grid = [
        [1, 3, 6, 0, 5, 4],
        [5, 2, 4, 1, 0, 0],
        [3, 0, 5, 0, 0, 2],
        [0, 0, 2, 5, 0, 0],
        [4, 0, 0, 2, 0, 5],
        [2, 0, 5, 0, 6, 0]
    ]
    
    print("Original Grid:")
    print_grid(grid)
    print("\nSolving...\n")
    
    if solve(grid):
        print("Solved Grid:")
        print_grid(grid)
    else:
        print("No solution exists. The grid has contradictory initial values.")
