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

Solución python: 
{
  "problem_id": 4,
  "language_submission": "Python 3.8",
  "language_id": 71,
  "sourceCode": "from collections import deque\n\nn, m = map(int, input().split())\nmaze = [list(input().strip()) for _ in range(n)]\n\n# Direcciones: arriba, abajo, izquierda, derecha\ndx = [-1, 1, 0, 0]\ndy = [0, 0, -1, 1]\n\ndef bfs():\n    visited = [[[False]*2 for _ in range(m)] for _ in range(n)]\n    queue = deque()\n    queue.append((0, 0, 0, 0))  # (x, y, pasos, rompió pared?)\n    visited[0][0][0] = True\n\n    while queue:\n        x, y, steps, broken = queue.popleft()\n        if x == n-1 and y == m-1:\n            return steps\n\n        for i in range(4):\n            nx = x + dx[i]\n            ny = y + dy[i]\n\n            if 0 <= nx < n and 0 <= ny < m:\n                if maze[nx][ny] == '0' and not visited[nx][ny][broken]:\n                    visited[nx][ny][broken] = True\n                    queue.append((nx, ny, steps + 1, broken))\n                elif maze[nx][ny] == '1' and broken == 0 and not visited[nx][ny][1]:\n                    visited[nx][ny][1] = True\n                    queue.append((nx, ny, steps + 1, 1))\n\n    return -1\n\nprint(bfs())",
  "user_id": "string"
}
