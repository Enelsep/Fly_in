from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Any, List, Dict, Tuple
import sys
import re
from enum import Enum


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone(BaseModel):
    """Pydantic model for zone configuration."""
    name: str = Field(pattern=r"^[^\s-]+$")
    x: int
    y: int
    zone_type: ZoneType = Field(default=ZoneType.NORMAL, alias="zone")
    color: Optional[str] = None
    max_drones: int = Field(default=1, ge=1)


class Connection(BaseModel):
    """Pydantic model for edge configuration."""
    zone1: str = Field(min_length=1)
    zone2: str = Field(min_length=1)
    max_link_capacity: int = Field(ge=1, default=1)


class SimulationMap(BaseModel):
    """Pydantic model for map configuration."""
    nb_drones:  int = Field(ge=1)
    zones: Dict[str, Zone]
    connections: List[Connection]


class MapParsingError(Exception):
    """Custom error class."""
    pass


class MapParser:
    """Parses a map file and returns a validated SimulationMap"""
    LINE_PATTERN = re.compile(r"^(.*?)(?:\s*\[(.*?)\])?$")
    METADATA_PATTERN = re.compile(r"(\w+)=([^\s]+)")

    def __init__(self) -> None:
        self.filepath: str = ""
        self.nb_drones: Optional[int] = None
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start_hub = ""
        self.end_hub = ""
        self.start_hub_count = 0
        self.end_hub_count = 0
        self.flag = 0

    def parse_args(self) -> None:
        """Parses arguments to get the config file."""
        arguments = sys.argv[1:]

        if not arguments:
            print("Please provide a map file !")
            sys.exit(1)
        if len(arguments) > 2:
            print("Please provide two arguments only (map file + option flag")
            sys.exit(1)
        try:
            self.filepath = str(sys.argv[1])
        except ValueError as e:
            print(f"Please enter a valid map name. {e}")
            sys.exit(1)
        if str(sys.argv[2] == "--allo"):
            self.flag = 1

    def extract_metadata(self, line: str) -> Tuple[str, Dict[str, Any]]:
        """Splits a line into its base string and a dictionary of metadata"""
        matching = self.LINE_PATTERN.match(line)
        if not matching:
            raise ValueError("Malformed line syntax")
        base_str = matching.group(1).strip()
        meta_str = matching.group(2)

        metadata = {}
        if meta_str:
            pairs = self.METADATA_PATTERN.findall(meta_str)
            metadata = {key: value for key, value in pairs}

        return base_str, metadata

    def process_line(self, line: str) -> None:
        """Takes a single line and route it to appropriate parser logic"""
        if line.startswith("nb_drones:"):
            parts = line.split(":")
            if len(parts) != 2:
                raise ValueError("Invalid nb_drones format")
            self.nb_drones = int(parts[1].strip())

        elif line.startswith("connection:"):
            start = len("connection:")
            base_str, metadata = self.extract_metadata(line[start:])
            zones = base_str.split("-")
            if len(zones) != 2:
                raise ValueError(
                    "Zones connection must be in format zone1-zone2")
            connx_data = {
                "zone1": zones[0].strip(),
                "zone2": zones[1].strip(),
                **metadata
            }
            self.connections.append(Connection(**connx_data))

        elif line.startswith("hub:") or line.startswith("start_hub:")\
                or line.startswith("end_hub"):

            prefix, remainder = line.split(":", 1)
            base_str, metadata = self.extract_metadata(remainder)
            base_parts = base_str.split()

            if len(base_parts) != 3:
                raise ValueError("Zone must define name, x and y.")

            zone_data = {
                "name": base_parts[0],
                "x": int(base_parts[1]),
                "y": int(base_parts[2]),
                **metadata
            }

            zone = Zone(**zone_data)

            if zone.name in self.zones:
                raise ValueError(f"Duplicate name found: {zone.name}")
            self.zones[zone.name] = zone

            if prefix.strip() == "start_hub":
                self.start_hub_count += 1
                self.start_hub = zone.name.lower()
            elif prefix.strip() == "end_hub":
                self.end_hub_count += 1
                self.end_hub = zone.name.lower()

        else:
            raise ValueError("Unknown line prefix")

    def validate_network(self) -> None:
        """Check global network rules after parsing"""
        if self.nb_drones is None:
            raise MapParsingError("Missing drone numbers definition")
        if self.start_hub_count != 1:
            raise MapParsingError("Start-hub count should be extactly one")
        if self.end_hub_count != 1:
            raise MapParsingError("End-hub count should be exactly one")

        for connection in self.connections:
            if connection.zone1 not in self.zones\
                    or connection.zone2 not in self.zones:
                raise MapParsingError(f"Connection {connection.zone1}"
                                      f" -- {connection.zone2} references"
                                      "unknown zones")

    def parse(self) -> SimulationMap:
        """Main loop to read the map text and extract infos"""
        self.parse_args()
        with open(self.filepath, 'r', encoding="UTF-8") as file:
            for line_nbr, line in enumerate(file, start=1):
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("#"):
                    continue

                try:
                    self.process_line(clean_line)
                except ValidationError as e:
                    err_msg = e.errors()[0].get('msg', 'Validation error')
                    err_loc = e.errors()[0].get('loc', ('', ))[0]
                    raise MapParsingError(
                        f"Line {line_nbr}: invalid {err_loc} - {err_msg}")
                except ValueError as e:
                    raise MapParsingError(f"Line {line_nbr}: {str(e)}")

        self.validate_network()

        assert self.nb_drones is not None, "nb_drones must be parsed"
        " before creating SimulationMap"

        return SimulationMap(
            nb_drones=self.nb_drones,
            zones=self.zones,
            connections=self.connections
        )
