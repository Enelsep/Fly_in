from parser import SimulationMap, Connection
from collections import defaultdict
from typing import Dict, Optional, List, Tuple
import heapq


class Pathfinder():
    """Class for pathfinding with a time-based implementation
    of Dijsktra algorithm"""

    def __init__(self, simulation_map: SimulationMap):
        self.sim_map = simulation_map
        self.graph = self.build_graph()

    def build_graph(self) -> Dict[str, Dict[str, Connection]]:
        """Build the data representation of our graph"""
        graph: Dict[str, Dict[str, Connection]] = {
            zone_name: {} for zone_name in self.sim_map.zones
        }

        for connection in self.sim_map.connections:
            graph[connection.zone1][connection.zone2] = connection
            graph[connection.zone2][connection.zone1] = connection

        return graph

    def resolve_graph(
            self,
            start_zone: str,
            end_zone: str,
            start_time: int,
            reservations: 'Reservations'
    ) -> Optional[List[tuple[int, str]]]:
        """
        Finds the fastest path for a single drone using Space-Time Dijkstra.
        Returns a list of states: [(time, zone_name), ...]
        """
        queue = [(start_time, 1, start_zone)]
        distances = {(start_zone, start_time): start_time}
        came_from: Dict[Tuple[str, int], Tuple[str, int]] = {}
        zone_priority = {"priority": 0, "normal": 1, "restricted": 2}

        while queue:
            current_time, _, current_zone = heapq.heappop(queue)
            if current_time > 5000:
                return None
            if current_zone == end_zone:
                return self.rewind(came_from, (current_zone, current_time))

            wait_time = current_time + 1
            if reservations.can_occupy_zone(current_zone, wait_time):
                if distances.get((current_zone, wait_time),
                                 float('inf')) > wait_time:
                    distances[(current_zone, wait_time)] = wait_time
                    came_from[(current_zone, wait_time)] = (
                        current_zone, current_time)
                    heapq.heappush(queue, (wait_time, 1, current_zone))

            for neighbor_name, connection in self.graph[current_zone].items():
                neighbor_zone = self.sim_map.zones[neighbor_name]

                z_type_str = neighbor_zone.zone_type.value if hasattr(
                    neighbor_zone.zone_type, 'value') else str(
                        neighbor_zone.zone_type)
                cost = 2 if z_type_str == "restricted" else 1
                arrival_time = current_time + cost

                if not reservations.can_use_connection(connection,
                                                       current_time):
                    continue
                if not reservations.can_occupy_zone(neighbor_name,
                                                    arrival_time):
                    continue
                if cost == 2 and not reservations.can_use_connection(
                        connection, current_time + 1):
                    continue

                if distances.get((neighbor_name, arrival_time),
                                 float('inf')) > arrival_time:
                    distances[(neighbor_name, arrival_time)] = arrival_time
                    came_from[(neighbor_name, arrival_time)] = (
                        current_zone, current_time)
                    priority_score = zone_priority.get(
                        z_type_str, 1)
                    heapq.heappush(
                        queue, (arrival_time, priority_score, neighbor_name))
        return None

    def rewind(self, came_from: Dict[Tuple[str, int], Tuple[str, int]],
               current_state: Tuple[str, int]) -> list[Tuple[int, str]]:
        """Backtracks from the end node to generate the sequence
        of movements.
        """
        path = [current_state]
        while current_state in came_from:
            current_state = came_from[current_state]
            path.append(current_state)
        path.reverse()
        return [(time, zone) for zone, time in path]


class Reservations():
    """Tracks and validates zone and connection capacities over time."""

    def __init__(self, sim_map: SimulationMap, start_zone: str, end_zone: str):
        self.sim_map = sim_map
        self.start_zone = start_zone
        self.end_zone = end_zone
        self.zone_usage: Dict[str, dict[int, int]
                              ] = defaultdict(lambda: defaultdict(int))
        self.conn_usage: Dict[frozenset[str], dict[int, int]
                              ] = defaultdict(lambda: defaultdict(int))

    def can_occupy_zone(self, zone_name: str, time: int) -> bool:
        """Checks if a zone has available capacity at a specific turn."""
        if zone_name in (self.start_zone, self.end_zone):
            return True
        zone = self.sim_map.zones[zone_name]
        z_type_str = zone.zone_type.value if hasattr(
            zone.zone_type, 'value') else str(
            zone.zone_type)
        if z_type_str == "blocked":
            return False
        current_occ = self.zone_usage[zone_name][time]

        return current_occ < zone.max_drones

    def can_use_connection(self, conn: Connection, time: int) -> bool:
        """Checks if a connection has available capacity at a specific turn."""
        link_key = frozenset([conn.zone1, conn.zone2])
        current_occ = self.conn_usage[link_key][time]

        return current_occ < conn.max_link_capacity

    def reserve_path(
        self, path: List[Tuple[int, str]],
            graph: Dict[str, dict[str, Connection]]) -> None:
        """Commits a drone path to the reservation table.
        path format: [(0, 'start'), (1, 'circle_a1')...]
        """

        for i in range(len(path) - 1):
            time_now, current_zone = path[i]
            time_next, next_zone = path[i+1]

            self.zone_usage[next_zone][time_next] += 1

            if current_zone != next_zone:
                link_key = frozenset([current_zone, next_zone])

                for time in range(time_now, time_next):
                    self.conn_usage[link_key][time] += 1
