_This project has been created as part of the 42 curriculum by epesnel_

<h1>I - Description:</h1>

This project is about Pathfinding.
The goal is to Design an efficient drone routing system that navigates multiple drones
through connected zones while minimizing simulation turns and handling movement constraints.
The routing is represented by a terminal text output and a Pygame visualisation.

<h1>II - Instructions:</h1>

> Make run

the command it invokes is : uv run python3 main.py maps/challenger/01_the_impossible_dream.txt (default map)
you can change the map by replacing the default path

<h1>III - Resources:</h1>

https://www.geeksforgeeks.org/dsa/dijkstras-shortest-path-algorithm-greedy-algo-7/
https://www.pygame.org/docs/

AI was used to provide general directions and blueprints for some functionalities

<h1>IV - Additions :</h1>

- **Algorithm choices and implementation strategies** :

Our map can be represented by a Weighted undirected graph (bidirectional -> drones can go both ways)
For the pathfinding, the chosen algorithm is a modified Dijsktra.
By default, Dijkstra, given a graph and a source vertex in the graph, find the shortest paths from source to all vertices in the given graph.
I had to modify it heavily because in this project we have another constraint that can be represented as another dimension : Time. Each node of the graph is the given Node at a specified time (turn number in our case)
Thus we can say our algorithm is "space-time Dijkstra" that handles the max capacities of the connections and zones with a reservation table.

- **Visual representation** :

I used the pygame python library for the visual representation.
when you launch the program, it automatically runs the visual simulation.
You can reset the simulation with spacebar and quit with ESC.
