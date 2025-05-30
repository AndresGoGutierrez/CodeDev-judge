Ejercicio de nivel medio:
Ejercicio: 
{
  "title": "Ruta más corta en un laberinto",
  "description": "Dado un laberinto representado por una cuadrícula de N x M celdas, donde '0' representa un camino y '1' representa una pared, encuentra la cantidad mínima de pasos necesarios para ir desde la esquina superior izquierda (0,0) hasta la esquina inferior derecha (N-1,M-1). Solo puedes moverte en las 4 direcciones cardinales (arriba, abajo, izquierda, derecha) y no puedes atravesar paredes. Si no es posible llegar, imprime -1.",
  "inputFormat": "La primera línea contiene dos enteros N y M (número de filas y columnas).\nLas siguientes N líneas contienen M caracteres cada una, representando la cuadrícula del laberinto (solo '0' o '1').",
  "outputFormat": "Un solo entero: el número mínimo de pasos para llegar a la meta, o -1 si no es posible.",
  "constraints": "1 <= N, M <= 1000\nCada celda contiene solo los caracteres '0' o '1'.\nLa celda (0,0) y la celda (N-1,M-1) siempre son '0'.",
  "difficulty": "medium",
  "time_limit": 1,
  "memory_limit": 256,
  "is_public": true,
  "external_id": "maze-shortest-path-001",
  "tags": "bfs, graph, matrices, pathfinding",
  "test_cases": [
    {
      "input_data": "3 3\n000\n010\n000",
      "expected_output": "4",
      "is_sample": true,
      "order": 0
    },
    {
      "input_data": "4 4\n0001\n1110\n0000\n0110",
      "expected_output": "6",
      "is_sample": true,
      "order": 1
    },
    {
      "input_data": "3 3\n010\n111\n010",
      "expected_output": "-1",
      "is_sample": false,
      "order": 2
    },
    {
      "input_data": "2 2\n00\n00",
      "expected_output": "2",
      "is_sample": false,
      "order": 3
    },
    {
      "input_data": "5 5\n00000\n01111\n00000\n11110\n00000",
      "expected_output": "8",
      "is_sample": false,
      "order": 4
    }
  ]
}

Solución Sin Json: 
Python
from collections import deque

n, m = map(int, input().split())
maze = [list(input().strip()) for _ in range(n)]

# Direcciones: arriba, abajo, izquierda, derecha
dx = [-1, 1, 0, 0]
dy = [0, 0, -1, 1]

def bfs():
    visited = [[[False]*2 for _ in range(m)] for _ in range(n)]
    queue = deque()
    queue.append((0, 0, 0, 0))  # (x, y, pasos, rompió pared?)
    visited[0][0][0] = True

    while queue:
        x, y, steps, broken = queue.popleft()
        if x == n-1 and y == m-1:
            return steps

        for i in range(4):
            nx = x + dx[i]
            ny = y + dy[i]

            if 0 <= nx < n and 0 <= ny < m:
                if maze[nx][ny] == '0' and not visited[nx][ny][broken]:
                    visited[nx][ny][broken] = True
                    queue.append((nx, ny, steps + 1, broken))
                elif maze[nx][ny] == '1' and broken == 0 and not visited[nx][ny][1]:
                    visited[nx][ny][1] = True
                    queue.append((nx, ny, steps + 1, 1))

    return -1

print(bfs())

Solución python: 
{
  "problem_id": 4,
  "language_submission": "Python 3.8",
  "language_id": 71,
  "sourceCode": "from collections import deque\n\nn, m = map(int, input().split())\nmaze = [list(input().strip()) for _ in range(n)]\n\n# Direcciones: arriba, abajo, izquierda, derecha\ndx = [-1, 1, 0, 0]\ndy = [0, 0, -1, 1]\n\ndef bfs():\n    visited = [[[False]*2 for _ in range(m)] for _ in range(n)]\n    queue = deque()\n    queue.append((0, 0, 0, 0))  # (x, y, pasos, rompió pared?)\n    visited[0][0][0] = True\n\n    while queue:\n        x, y, steps, broken = queue.popleft()\n        if x == n-1 and y == m-1:\n            return steps\n\n        for i in range(4):\n            nx = x + dx[i]\n            ny = y + dy[i]\n\n            if 0 <= nx < n and 0 <= ny < m:\n                if maze[nx][ny] == '0' and not visited[nx][ny][broken]:\n                    visited[nx][ny][broken] = True\n                    queue.append((nx, ny, steps + 1, broken))\n                elif maze[nx][ny] == '1' and broken == 0 and not visited[nx][ny][1]:\n                    visited[nx][ny][1] = True\n                    queue.append((nx, ny, steps + 1, 1))\n\n    return -1\n\nprint(bfs())",
  "user_id": "string"
}


Ejercicio: Contar regiones conectadas
📘 Enunciado:
Dada una matriz binaria de tamaño n x m compuesta por '1' (tierra) y '0' (agua), cuenta cuántas regiones de tierra conectadas existen.
Una región está formada por celdas '1' conectadas vertical u horizontalmente (no en diagonal).

📥 Entrada:
La entrada consiste en:

Una línea con dos enteros n y m, el número de filas y columnas.

Luego n líneas, cada una con m caracteres que pueden ser '0' o '1'.

Ejemplo:
Copiar
Editar
4 5
11000
11000
00100
00011
📤 Salida:
Un número entero: la cantidad de regiones de tierra conectadas.

Ejemplo de salida:
Copiar
Editar
3
🧪 Explicación:
La entrada representa la siguiente matriz:

Copiar
Editar
1 1 0 0 0  
1 1 0 0 0  
0 0 1 0 0  
0 0 0 1 1  
Hay tres regiones de '1' conectadas vertical u horizontalmente.

✅ Restricciones:
1 ≤ n, m ≤ 1000

Cada celda es '0' o '1'

La matriz contiene al menos una fila y una columna

🏷️ Tags:
dfs

bfs

componentes conexos

matriz

grafos

⏱ Tiempo Límite:
1 segundo

💾 Memoria Límite:
256 MB


Solución sin Json: 
Python
import sys
sys.setrecursionlimit(10**7)  # Para manejar entradas grandes si usas DFS recursivo

# Leer tamaño de la matriz
n, m = map(int, input().split())

# Leer la matriz
grid = [list(input().strip()) for _ in range(n)]
visited = [[False]*m for _ in range(n)]

# Direcciones: arriba, abajo, izquierda, derecha
dx = [-1, 1, 0, 0]
dy = [0, 0, -1, 1]

def dfs(x, y):
    stack = [(x, y)]
    visited[x][y] = True
    while stack:
        cx, cy = stack.pop()
        for i in range(4):
            nx, ny = cx + dx[i], cy + dy[i]
            if 0 <= nx < n and 0 <= ny < m:
                if not visited[nx][ny] and grid[nx][ny] == '1':
                    visited[nx][ny] = True
                    stack.append((nx, ny))

# Contar regiones conectadas
regions = 0
for i in range(n):
    for j in range(m):
        if grid[i][j] == '1' and not visited[i][j]:
            dfs(i, j)
            regions += 1

print(regions)
