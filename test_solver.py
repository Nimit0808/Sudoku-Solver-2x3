from solver import solve

grid = [
    [0, 0, 2, 5, 0, 1],
    [0, 1, 0, 3, 0, 2],
    [3, 5, 4, 0, 1, 0],
    [2, 6, 1, 4, 0, 3],
    [1, 4, 3, 6, 0, 5],
    [0, 2, 0, 1, 3, 4]
]

grid1 = [row[:] for row in grid]
grid2 = [row[:] for row in grid]

res1 = solve(grid1, 3, 2)
res2 = solve(grid2, 2, 3)

print("Solvable 3x2:", res1)
print("Solvable 2x3:", res2)
