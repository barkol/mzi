"""Mirror component - special case of tunable beam splitter with no transmission."""
import pygame
import numpy as np
from components.tunable_beamsplitter import TunableBeamSplitter
from config.settings import MAGENTA, MIRROR_LOSS

class Mirror(TunableBeamSplitter):
    """Perfect mirror - a tunable beam splitter with t=0, r=-1."""
    
    def __init__(self, x, y, mirror_type='/'):
        """
        Initialize mirror.
        
        Args:
            x, y: Position
            mirror_type: '/' or '\' - determines reflection geometry
        """
        # For a perfect mirror:
        # t = 0 (no transmission)
        # r = -1 (perfect reflection with π phase shift)
        # r' = -1 (to satisfy r*r' = -1)
        t = 0.0
        r = -1.0
        
        super().__init__(x, y, t=t, r=r, orientation=mirror_type, loss=MIRROR_LOSS)
        self.component_type = "mirror"
        self.mirror_type = mirror_type
        
        # Override the scattering matrix for proper mirror behavior
        # Port order: [A (left), B (bottom), C (right), D (top)]
        if mirror_type == '/':
            # '/' mirror: A↔D, B↔C (with π phase shift)
            self.S = np.array([
                [0,  0,  0, -1],  # A reflects to/from D
                [0,  0, -1,  0],  # B reflects to/from C
                [0, -1,  0,  0],  # C reflects to/from B
                [-1, 0,  0,  0]   # D reflects to/from A
            ], dtype=complex)
        else:  # '\'
            # '\' mirror: A↔B, C↔D (with π phase shift)
            self.S = np.array([
                [0, -1,  0,  0],  # A reflects to/from B
                [-1, 0,  0,  0],  # B reflects to/from A
                [0,  0,  0, -1],  # C reflects to/from D
                [0,  0, -1,  0]   # D reflects to/from C
            ], dtype=complex)
    
    def draw(self, screen):
        """Draw mirror with custom appearance."""
        # Mirror surface
        if self.mirror_type == '/':
            start = (self.position.x - 20, self.position.y + 20)
            end = (self.position.x + 20, self.position.y - 20)
        else:  # '\'
            start = (self.position.x - 20, self.position.y - 20)
            end = (self.position.x + 20, self.position.y + 20)
        
        # Draw thick mirror line
        pygame.draw.line(screen, MAGENTA, start, end, 6)
        
        # Draw reflection indicators (dimmed)
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        s_center = (30, 30)
        if self.mirror_type == '/':
            pygame.draw.line(s, (MAGENTA[0], MAGENTA[1], MAGENTA[2], 100),
                           (s_center[0] - 20, s_center[1] + 20),
                           (s_center[0] + 20, s_center[1] - 20), 2)
        else:
            pygame.draw.line(s, (MAGENTA[0], MAGENTA[1], MAGENTA[2], 100),
                           (s_center[0] - 20, s_center[1] - 20),
                           (s_center[0] + 20, s_center[1] + 20), 2)
        screen.blit(s, (self.position.x - 30, self.position.y - 30))
        
        # Add direction hints
        if self.mirror_type == '/':
            # '/' mirror reflects: left↔top, bottom↔right
            # Show left→top reflection
            points = [
                (self.position.x - 20, self.position.y),
                (self.position.x - 10, self.position.y),
                (self.position.x - 10, self.position.y - 10)
            ]
            pygame.draw.lines(screen, MAGENTA, False, points, 1)
            # Show bottom→right reflection
            points2 = [
                (self.position.x, self.position.y + 20),
                (self.position.x, self.position.y + 10),
                (self.position.x + 10, self.position.y + 10)
            ]
            pygame.draw.lines(screen, MAGENTA, False, points2, 1)
        else:  # '\'
            # '\' mirror reflects: left↔bottom, top↔right
            # Show left→bottom reflection
            points = [
                (self.position.x - 20, self.position.y),
                (self.position.x - 10, self.position.y),
                (self.position.x - 10, self.position.y + 10)
            ]
            pygame.draw.lines(screen, MAGENTA, False, points, 1)
            # Show top→right reflection
            points2 = [
                (self.position.x, self.position.y - 20),
                (self.position.x, self.position.y - 10),
                (self.position.x + 10, self.position.y - 10)
            ]
            pygame.draw.lines(screen, MAGENTA, False, points2, 1)
        
        # Show debug info
        if self.debug:
            font = pygame.font.Font(None, 10)
            # Show mirror type and phase shift
            info_text = f"Mirror {self.mirror_type}: r={self.r:.0f} (π shift)"
            info_surface = font.render(info_text, True, MAGENTA)
            screen.blit(info_surface, (self.position.x - 30, self.position.y + 25))
            
            # Show active ports if available
            if self._last_v_in is not None and self._last_v_out is not None:
                # Find non-zero input/output
                port_names = ['A', 'B', 'C', 'D']
                for i in range(4):
                    if abs(self._last_v_in[i]) > 0.001:
                        for j in range(4):
                            if abs(self._last_v_out[j]) > 0.001:
                                reflection_text = f"{port_names[i]}→{port_names[j]}"
                                refl_surface = font.render(reflection_text, True, MAGENTA)
                                screen.blit(refl_surface, (self.position.x - 20, self.position.y + 35))
                                break
                        break
            
            # Show beam accumulation info in debug mode
            if hasattr(self, 'all_beams_by_port'):
                total_beams = sum(len(beams) for beams in self.all_beams_by_port.values())
                if total_beams > 0:
                    beam_text = f"Beams: {total_beams}"
                    beam_surface = font.render(beam_text, True, MAGENTA)
                    screen.blit(beam_surface, (self.position.x - 20, self.position.y + 45))
                    
                    # Show which ports have beams
                    ports_with_beams = []
                    for port_idx, beams in self.all_beams_by_port.items():
                        if beams:
                            ports_with_beams.append(port_names[port_idx])
                    if ports_with_beams:
                        ports_text = f"Ports: {','.join(ports_with_beams)}"
                        ports_surface = font.render(ports_text, True, MAGENTA)
                        screen.blit(ports_surface, (self.position.x - 20, self.position.y + 55))
