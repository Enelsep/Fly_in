from simulation_engine import Simulator
from parser import MapParsingError
from visuals import Visualizer
import sys


def main() -> None:
    try:
        simulation = Simulator()
        sim_map = simulation.sim_map
        paths = simulation.drone_paths
        simulation.run()
        visuals = Visualizer(sim_map, paths)
        try:
            visuals.run_graphic_sim()
        except KeyboardInterrupt:
            print("Error : Keyboard interruption")
    except MapParsingError as e:
        print(f"Parsing Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Simulation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
