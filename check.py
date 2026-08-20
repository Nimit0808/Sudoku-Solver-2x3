grid = [
    [1, 0, 6, 0, 5, 4],
    [5, 2, 0, 1, 0, 0],
    [3, 0, 5, 0, 0, 2],
    [0, 0, 2, 5, 0, 0],
    [4, 0, 0, 2, 0, 5],
    [2, 0, 5, 0, 6, 0]
]

def check_grid(g):
    for i in range(6):
        for j in range(6):
            if g[i][j] != 0:
                num = g[i][j]
                # Check row
                for c in range(6):
                    if c != j and g[i][c] == num:
                        print(f"Conflict row {i}: {num} at col {j} and col {c}")
                # Check col
                for r in range(6):
                    if r != i and g[r][j] == num:
                        print(f"Conflict col {j}: {num} at row {i} and row {r}")
                # Check box
                box_x = j // 3
                box_y = i // 2
                for r in range(box_y*2, box_y*2+2):
                    for c in range(box_x*3, box_x*3+3):
                        if (r, c) != (i, j) and g[r][c] == num:
                            print(f"Conflict box {box_y},{box_x}: {num} at ({i},{j}) and ({r},{c})")

check_grid(grid)
