from pathfinding import Pathfinder, Reservations
from parser import MapParser
from typing import List, Tuple, Dict


class Simulator:
    """Orchestrates the parsed map, pathfinding, and output generation."""

    def __init__(self) -> None:
        self.drone_paths: Dict[int, list[Tuple[int, str]]] = {}
        self.parser = MapParser()
        self.sim_map = self.parser.parse()

    def run(self) -> None:
        """Main execution flow for the simulation."""

        start_zone = self.parser.start_hub
        end_zone = self.parser.end_hub

        pathfinder = Pathfinder(self.sim_map)
        self.reservations = Reservations(self.sim_map, start_zone, end_zone)

        for drone_id in range(1, self.sim_map.nb_drones + 1):
            path = pathfinder.resolve_graph(
                start_zone, end_zone, 0, self.reservations)

            if not path:
                raise ValueError(
                    "Simulation failed:"
                    f"No valid path for drone: {drone_id}")
            self.reservations.reserve_path(path, pathfinder.graph)
            self.drone_paths[drone_id] = path

        self.print_sim_output()

    def get_drone_state(self, path: List[tuple[int, str]],
                        target_turn: int) -> Tuple[str, bool]:
        """Determines where the drone is at turn x
        returns: (location name, is_in_transit_on_connection)
        """
        if target_turn >= path[-1][0]:
            return path[-1][1], False

        for i in range(len(path) - 1):
            time_now, current_zone = path[i]
            time_next, next_zone = path[i+1]

            if time_now == target_turn:
                return current_zone, False

            if time_now < target_turn < time_next:
                return f"{current_zone}-{next_zone}", True

        return path[0][1], False

    def print_sim_output(self) -> None:
        """Formats and prints the ouput turn by turn"""
        if not self.drone_paths:
            return

        max_turn = max(path[-1][0] for path in self.drone_paths.values())

        for turn in range(1, max_turn + 1):
            turn_moves = []

            for drone_id, path in self.drone_paths.items():
                prev_loc, _ = self.get_drone_state(path, turn - 1)
                loc_now, is_transit = self.get_drone_state(path, turn)

                if prev_loc != loc_now or is_transit:
                    if prev_loc != path[-1][1]:
                        if is_transit:
                            turn_moves.append(f"D{drone_id}-{loc_now}")
                        else:
                            if self.parser.flag == 1:
                                curr_occ = self.reservations.zone_usage[loc_now][turn]
                                total_occ = self.sim_map.zones[loc_now].max_drones
                                turn_moves.append(
                                    f"D{drone_id}-{loc_now}, {curr_occ}/{total_occ}")
                            else:
                                turn_moves.append(
                                    f"D{drone_id}-{loc_now}")

            if turn_moves:
                print(f"turn : {turn}")
                print(" ".join(turn_moves))
