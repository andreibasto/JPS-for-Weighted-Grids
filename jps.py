import sys
from heapq import heappush, heappop
from colorsys import hls_to_rgb
from PIL import Image
from random import random
from time import perf_counter
from random import randint, seed

OBSTACLE = "#" # Arbitrary, not actually in benchmark grids
MAPS = ["Map" + str(i) for i in range(1, 21)]
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

seed(0)
sys.setrecursionlimit(2500)

def is_blocked(n):     
    return outside(n) or grid[n[0]][n[1]] == OBSTACLE

def outside(n):
    return n[0] < 0 or n[1] < 0 or n[0] >= height or n[1] >= width

def step(x, d):
    return (x[0] + d[0], x[1] + d[1])

def get_neighbors(n):
    return [(n[0] + dx, n[1] + dy) for dx in range(-1, 2) for dy in range(-1, 2) if dx != 0 or dy != 0]

def is_diagonal(d):
    return d[0] != 0 and d[1] != 0

def get_direction(p, n):
    dx = 0 if n[0] - p[0] == 0 else 1 if n[0] > p[0] else -1
    dy = 0 if n[1] - p[1] == 0 else 1 if n[1] > p[1] else -1
    return (dx, dy)

def prune(p, n):
    if not p: # Start node since parent is null
        neighbors = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if (dx == 0 and dy == 0) or is_blocked((n[0] + dx, n[1] + dy)):
                    continue
                elif is_diagonal((dx, dy)) and is_blocked((n[0] + dx, n[1])) and is_blocked((n[0], n[1] + dy)):
                    continue                    
                neighbors.append((n[0] + dx, n[1] + dy))
        return neighbors
    
    direction = get_direction(p, n)
    dx, dy = direction
    x, y = n

    neighbors = []
    if is_diagonal(direction): # Diagonal move
        if not is_blocked((x, y + dy)):
            neighbors.append((x, y + dy))
        if not is_blocked((x + dx, y)):
            neighbors.append((x + dx, y))
        if not is_blocked((x + dx, y + dy)) and (not is_blocked((x, y + dy)) or not is_blocked((x + dx, y))):
            neighbors.append((x + dx, y + dy))
            
        if not is_blocked((x - dx, y + dy)) and (is_blocked((x - dx, y)) or grid[x][y] < grid[x - dx][y] or grid[x][y] != grid[x - dx][y + dy]):
            neighbors.append((x - dx, y + dy))
        if not is_blocked((x + dx, y - dy)) and (is_blocked((x, y - dy)) or grid[x][y] < grid[x][y - dy] or grid[x][y] != grid[x + dx][y - dy]):
            neighbors.append((x + dx, y - dy))
    else: # Straight move
        if not is_blocked((x + dx, y + dy)):
            neighbors.append((x + dx, y + dy))
        
            if dx == 0: # Moving vertically
                if not is_blocked((x + 1, y + dy)) and (is_blocked((x + 1, y)) or grid[x][y] < grid[x + 1][y] or grid[x][y] != grid[x + 1][y + dy]):
                    neighbors.append((x + 1, y + dy))
                if not is_blocked((x - 1, y + dy)) and (is_blocked((x - 1, y)) or grid[x][y] < grid[x - 1][y] or grid[x][y] != grid[x - 1][y + dy]):
                    neighbors.append((x - 1, y + dy))
            elif dy == 0:
                if not is_blocked((x + dx, y + 1)) and (is_blocked((x, y + 1)) or grid[x][y] < grid[x][y + 1] or grid[x][y] != grid[x + dx][y + 1]):
                    neighbors.append((x + dx, y + 1))
                if not is_blocked((x + dx, y - 1)) and (is_blocked((x, y - 1)) or grid[x][y] < grid[x][y - 1] or grid[x][y] != grid[x + dx][y - 1]):
                    neighbors.append((x + dx, y - 1))
    return neighbors

def has_forced(p, n):    
    direction = get_direction(p, n)
    dx, dy = direction
    x, y = n

    if is_diagonal(direction):
        if not is_blocked((x, y + dy)) and grid[x][y + dy] != grid[x][y]:
            return True
        if not is_blocked((x + dx, y)) and grid[x + dx][y] != grid[x][y]:
            return True
        if not is_blocked((x + dx, y + dy)) and (not is_blocked((x, y + dy)) or not is_blocked((x + dx, y))) and grid[x + dx][y + dy] != grid[x][y]:
            return True
            
        if not is_blocked((x - dx, y + dy)) and (is_blocked((x - dx, y)) or grid[x][y] < grid[x - dx][y] or grid[x][y] != grid[x - dx][y + dy]):
            return True
        if not is_blocked((x + dx, y - dy)) and (is_blocked((x, y - dy)) or grid[x][y] < grid[x][y - dy] or grid[x][y] != grid[x + dx][y - dy]):
            return True
    else:
        if not is_blocked((x + dx, y + dy)):
            if grid[x + dx][y + dy] != grid[x][y]:
                return True
            
            if dx == 0: # Moving vertically
                if not is_blocked((x + 1, y + dy)) and (is_blocked((x + 1, y)) or grid[x][y] < grid[x + 1][y] or grid[x][y] != grid[x + 1][y + dy]):
                    return True
                if not is_blocked((x - 1, y + dy)) and (is_blocked((x - 1, y)) or grid[x][y] < grid[x - 1][y] or grid[x][y] != grid[x - 1][y + dy]):
                    return True
            elif dy == 0:
                if not is_blocked((x + dx, y + 1)) and (is_blocked((x, y + 1)) or grid[x][y] < grid[x][y + 1] or grid[x][y] != grid[x + dx][y + 1]):
                    return True
                if not is_blocked((x + dx, y - 1)) and (is_blocked((x, y - 1)) or grid[x][y] < grid[x][y - 1] or grid[x][y] != grid[x + dx][y - 1]):
                    return True
    return False

def identify_successors(p, x, s, g):
    successors = set()
    pruned_neighbors = prune(p, x)
    for n in pruned_neighbors:
        n = jump(x, get_direction(x, n), s, g)
        if n:
            successors.add(n)
        
    return successors

def jump(x, d, s, g):
    n = step(x, d)
    
    if is_blocked(n):
        return None
    if n == g:
        return n
    
    if has_forced(x, n): # Has forced neighbor
        return n
        
    if is_diagonal(d):
        for di in ((d[0], 0), (0, d[1])):
            if jump(n, di, s, g):
                return n
          
    return jump(n, d, s, g)

def dist(node, goal): # Heuristic using octile distance calc
    dx = abs(node[0] - goal[0])
    dy = abs(node[1] - goal[1])
    return (dx + dy) + (2**0.5 - 2) * min(dx, dy)

def jps(grid, start, goal):
    closed = {start: 0}
    open = []
    number_nodes_expanded = 0    
    heappush(open, (0, start, [None]))
    while open:
        node = heappop(open)        
        cost, child, path = node[0], node[1], node[2]
        number_nodes_expanded += 1
            
        if child[0] == goal[0] and child[1] == goal[1]:
            return path[1:] + [child], number_nodes_expanded
        
        parent = path[-1]
        if not parent:
            path = [start]
            
        successors = identify_successors(parent, child, start, goal)
            
        for jump_point in successors:
            x_dist = abs(child[0] - jump_point[0])
            y_dist = abs(child[1] - jump_point[1])
            if x_dist == 0:
                jumped_over = y_dist - 1
            else:
                jumped_over = x_dist - 1
            total_cost = cost - dist(child, goal) + dist(child, jump_point) + dist(jump_point, goal) + grid[jump_point[0]][jump_point[1]] * jumped_over + grid[child[0]][child[1]]
            
            if jump_point not in closed or total_cost < closed[jump_point]:
                closed[jump_point] = total_cost          
                heappush(open, (total_cost, jump_point, path + [child]))
 
    return number_nodes_expanded

def a_star(grid, start, goal):
    closed = {start: 0}
    open = []
    number_nodes_expanded = 0
    heappush(open, (0, start, []))

    while open:
        node = heappop(open)
        cost, child, path = node[0], node[1], node[2] 
        number_nodes_expanded += 1
        if child == goal:
            return path + [child], number_nodes_expanded
        x, y = child
        for x1 in range(-1, 2):
            for y1 in range(-1, 2):
                if abs(x1) + abs(y1) == 2 and is_blocked((x + x1, y)) and is_blocked((x, y + y1)):
                    continue
                neighbor = (x + x1, y + y1)
                if is_blocked(neighbor) or child == neighbor:
                    continue
                total_cost = cost - dist(child, goal) + dist(child, neighbor) + dist(neighbor, goal) + grid[neighbor[0]][neighbor[1]]
                if neighbor not in closed or total_cost < closed[neighbor]:
                    closed[neighbor] = total_cost
                    heappush(open, (total_cost, neighbor, path + [child]))
                    
    return number_nodes_expanded

for filename in MAPS:
    map_filename = filename + ".map"
    with open(map_filename) as f:
        lines = [l.strip() for l in f]
        
    height = int(lines[1].split(" ")[1])
    width = int(lines[2].split(" ")[1])

    grid = [[ALPHABET.index(c) for c in segment] for segment in lines[4:]]

    # Creating image to visualize paths        
    image = Image.new(mode="RGB", size=(width, height))
    pixels = image.load()        
    colors = []
    for i in range(26):
        h,s,l = random(), 0.5 + random()/2.0, 0.4 + random()/5.0
        rgb = tuple([int(256*i) for i in hls_to_rgb(h,l,s)]) 
        colors.append(rgb)        
    for x in range(width):
        for y in range(height):
            val = grid[y][x]
            pixels[x, y] = colors[val]


    scenario_filename = filename + ".map.scen"
    with open(scenario_filename) as f:
        lines = [l.strip() for l in f]
    cases = [l.split("\t") for l in lines[1:]]

    print("Looking at", filename)

    for case in cases[:3]:
        start_x, start_y = int(case[4]), int(case[5])
        end_x, end_y = int(case[6]), int(case[7])

        # Flipped since grid is stored in form grid[y][x]
        start = (start_y, start_x)
        end = (end_y, end_x)

        print("\nNew case, start:", (start_x, start_y), "end:", (end_x, end_y))

        start_time = perf_counter()
        res = jps(grid, start, end)
        end_time = perf_counter()

        if isinstance(res, tuple):
            path, number_nodes_expanded = res

            # Connecting jump points to form complete path
            all_points = []
            for i in range(1, len(path)):
                c = path[i]
                p = path[i - 1]
                x, y = p[0], p[1]
                try:
                    dx = (c[0] - p[0]) // abs(c[0] - p[0])
                except:
                    dx = 0            
                try:
                    dy = (c[1] - p[1]) // abs(c[1] - p[1])
                except:
                    dy = 0
                while x != c[0] or y != c[1]:
                    all_points.append((x, y))
                    x += dx
                    y += dy
            all_points.append(path[-1])

            start_path = all_points[0]
            cost = grid[start_path[0]][start_path[1]]
            for i in range(1, len(all_points)):
                a = all_points[i - 1]
                b = all_points[i]
                cost += dist(a, b)
                cost += grid[b[0]][b[1]]
            print("Total cost JPS:", cost)

            for x, y in all_points:
                pixels[y, x] = (255, 255, 255)
        else:
            number_nodes_expanded = res
            end_time = perf_counter()
            print("JPS didn't return path")
        print(f"JPS had {number_nodes_expanded} nodes expanded")
        print(f"JPS took {round(end_time - start_time, 5)} seconds")

        start_time = perf_counter()
        res = a_star(grid, start, end)
        end_time = perf_counter()
        if isinstance(res, tuple):
            path, number_nodes_expanded = res  
            start_path = path[0]
            cost = grid[start_path[0]][start_path[1]]
            for i in range(1, len(path)):
                a = path[i - 1]
                b = path[i]
                cost += dist(a, b)
                cost += grid[b[0]][b[1]]
            print("Total cost A*:", cost)

            for x, y in path:
                if pixels[y, x] == (255, 255, 255):
                    pixels[y, x] = (255, 0, 0)
                else:
                    pixels[y, x] = (0, 0, 0) 
        else:
            number_nodes_expanded = res
            print("A* didn't return path")
        print(f"A*  had {number_nodes_expanded} nodes expanded")
        print(f"A*  took {round(end_time - start_time, 5)} seconds")

        image.save(f"{filename}_paths.png") # JPS - white, A* black, Match - red
