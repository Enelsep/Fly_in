import pygame
from parser import SimulationMap
from typing import Tuple, List, Dict


class Visualizer:
    def __init__(self, sim_map: SimulationMap,
                 drone_paths: Dict[int, list[Tuple[int, str]]],
                 width: int = 1280,
                 height: int = 720):

        self.sim_map = sim_map
        self.width = width
        self.height = height
        self.padding = 50
        self.drone_paths = drone_paths
        self.color_palette = {"blue": "#0071a9",
                              "cyan": "#009ba9",
                              "orange": "#008da9",
                              "black": "#002f47",
                              "yellow": "#0063a9",
                              "red": "#0055a9",
                              "purple": "#0047a9",
                              "maroon": "#0039a9",
                              "brown": "#002ba9",
                              "crimson": "#001da9",
                              "darkred": "#000fa9",
                              "gold": "#0093dc"}
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Drone Fleet Simulation")
        self.calculate_mapping()

    def calculate_mapping(self) -> None:
        """Maps the x, y coordinates to fit the map on the screen"""
        xs = [zone.x for zone in self.sim_map.zones.values()]
        ys = [zone.y for zone in self.sim_map.zones.values()]

        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)

        range_x = self.max_x - self.min_x or 1
        range_y = self.max_y - self.min_y or 1

        scale_x = (self.width - 2 * self.padding) / range_x
        scale_y = (self.height - 2 * self.padding) / range_y

        self.scale = min(scale_x, scale_y)

        self.offset_x = self.padding + \
            (self.width - 2 * self.padding - range_x * self.scale) / 2
        self.offset_y = self.padding + \
            (self.height - 2 * self.padding - range_y * self.scale) / 2

    def to_pixel(self, x: int, y: int) -> Tuple[int, int]:
        """Translates abstract map coordinates to Pygame pixel coordinates."""
        px = self.offset_x + (x - self.min_x) * self.scale
        py = self.offset_y + (y - self.min_y) * self.scale
        return int(px), int(py)

    def draw_connection(self, p1: Tuple[int, int], p2: Tuple[int, int],
                        color: pygame.Color,
                        thickness: int,
                        dashed: bool = False) -> None:
        if not dashed:
            pygame.draw.line(self.screen, color, p1, p2, thickness)
            return

        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = max(1, (dx**2 + dy**2) ** 0.5)
        ux, uy = dx / length, dy / length

        dash_len, gap_len = 10, 6
        pos = 0
        drawing = True

        while pos < length:
            segment_len = min(dash_len if drawing else gap_len, length - pos)
            if drawing:
                start = (p1[0] + ux * pos, p1[1] + uy * pos)
                end = (p1[0] + ux * (pos + segment_len),
                       p1[1] + uy * (pos + segment_len))
                pygame.draw.aaline(self.screen, color, start, end, thickness)
            pos += segment_len
            drawing = not drawing

    def draw_graph(self) -> None:
        """Draws the connections and zones on the screen"""

        for conn in self.sim_map.connections:
            z1 = self.sim_map.zones[conn.zone1]
            z2 = self.sim_map.zones[conn.zone2]
            p1 = self.to_pixel(z1.x, z1.y)
            p2 = self.to_pixel(z2.x, z2.y)

            is_high_capacity = conn.max_link_capacity > 1
            self.draw_connection(
                p1, p2,
                color=pygame.Color("#0071a9"),
                thickness=max(1, conn.max_link_capacity * 2),
                dashed=not is_high_capacity
            )

        for zone in self.sim_map.zones.values():
            px, py = self.to_pixel(zone.x, zone.y)

            if zone.color:
                try:
                    hex_code = self.color_palette.get(zone.color, "#0071a9")
                    color = pygame.Color(hex_code)
                except ValueError:
                    color = pygame.Color("#0071a9")
            else:
                color = pygame.Color("#0071a9")
            pygame.draw.circle(self.screen, pygame.Color(
                "#002f47"), (px, py), radius=17)
            pygame.draw.circle(self.screen, color, (px, py), radius=15)

    def get_drone_pixel_pos(self, path: List[tuple[int, str]],
                            current_time: float) -> tuple[int, int]:
        """Calculates the interpolated pixel (x, y) for a drone
        at a continuous time."""
        if current_time <= path[0][0]:
            z = self.sim_map.zones[path[0][1]]
            return self.to_pixel(z.x, z.y)

        if current_time >= path[-1][0]:
            z = self.sim_map.zones[path[-1][1]]
            return self.to_pixel(z.x, z.y)

        for i in range(len(path) - 1):
            t1, zone1_name = path[i]
            t2, zone2_name = path[i+1]

            if t1 <= current_time < t2:
                progress = (current_time - t1) / (t2 - t1)

                z1 = self.sim_map.zones[zone1_name]
                z2 = self.sim_map.zones[zone2_name]

                px1, py1 = self.to_pixel(z1.x, z1.y)
                px2, py2 = self.to_pixel(z2.x, z2.y)

                interp_x = px1 + (px2 - px1) * progress
                interp_y = py1 + (py2 - py1) * progress

                return int(interp_x), int(interp_y)
        z = self.sim_map.zones[path[-1][1]]
        return self.to_pixel(z.x, z.y)

    def draw_drone_glow(self, px: int, py: int,
                        glow_color: Tuple[int, int, int] = (255, 255, 255),
                        glow_radius: int = 18, alpha: int = 80) -> None:
        size = glow_radius * 2
        glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)

        for r in range(glow_radius, 6, -2):
            layer_alpha = int(alpha * (r / glow_radius))
            color = (*glow_color, layer_alpha)
            pygame.draw.circle(glow_surface, color,
                               (glow_radius, glow_radius), r)
        self.screen.blit(glow_surface, (px - glow_radius, py - glow_radius))

    def run_graphic_sim(self) -> None:
        """simple loop"""
        clock = pygame.time.Clock()
        running = True
        current_time = 0.0
        turns_per_second = 2.5
        max_turn = max(path[-1][0] for path in self.drone_paths.values())

        pygame.font.init()
        font = pygame.font.SysFont('RobotoMono.ttf', 22)

        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        current_time = 0.0
                    if event.key == pygame.K_ESCAPE:
                        running = False

            if current_time < max_turn:
                current_time += dt * turns_per_second
            self.screen.fill(pygame.Color("black"))
            self.draw_graph()

            for drone_id, path in self.drone_paths.items():
                px, py = self.get_drone_pixel_pos(path, current_time)
                self.draw_drone_glow(px, py, glow_color=(
                    255, 255, 255), glow_radius=16, alpha=75)

            for drone_id, path in self.drone_paths.items():
                px, py = self.get_drone_pixel_pos(path, current_time)
                pygame.draw.circle(self.screen, pygame.Color(
                    "black"), (px, py), radius=6)
                pygame.draw.circle(self.screen, pygame.Color(
                    "white"), (px, py), radius=6, width=1)

            esc_text = font.render("Press ESC to quit",
                                   True, pygame.Color("#ffffff"))
            space_text = font.render(
                "Press SPACE to reset", True, pygame.Color("#ffffff"))
            self.screen.blit(esc_text, (20, self.height - 50))
            self.screen.blit(space_text, (20, self.height - 25))

            pygame.display.flip()
        pygame.quit()
