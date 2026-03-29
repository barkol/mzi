"""Mirror component with constrained scaling support."""
import pygame
import numpy as np
from components.tunable_beamsplitter import TunableBeamSplitter
from config.settings import CYAN, MIRROR_LOSS, scale, scale_font, GRID_SIZE

class Mirror(TunableBeamSplitter):
    """Perfect mirror - a tunable beam splitter with t=0, r=-1, with constrained scaling."""
    
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
        
        # Scattering matrix for mirror behavior.
        # Port order: [A (left), B (bottom), C (right), D (top)]
        #
        # Port input convention (after fix): a beam going DOWN enters
        # port D (the top face), a beam going UP enters port B (bottom
        # face).  Horizontal beams: RIGHT→A, LEFT→C.
        #
        # '/' on screen: RIGHT→UP, DOWN→LEFT, LEFT→DOWN, UP→RIGHT
        # '\' on screen: RIGHT→DOWN, DOWN→RIGHT, LEFT→UP, UP→LEFT
        if mirror_type == '/':
            self.S = np.array([
                [0,  0,  0, -1],  # A ← D (DOWN→LEFT)
                [0,  0, -1,  0],  # B ← C (LEFT→DOWN)
                [0, -1,  0,  0],  # C ← B (UP→RIGHT)
                [-1, 0,  0,  0]   # D ← A (RIGHT→UP)
            ], dtype=complex)
        else:  # '\'
            self.S = np.array([
                [0, -1,  0,  0],  # A ← B (UP→LEFT)
                [-1, 0,  0,  0],  # B ← A (RIGHT→DOWN)
                [0,  0,  0, -1],  # C ← D (DOWN→RIGHT)
                [0,  0, -1,  0]   # D ← C (LEFT→UP)
            ], dtype=complex)
    
    def draw(self, screen):
        """Draw mirror with custom appearance and constrained scaling."""
        # Mirror surface - size constrained to fit within grid cell
        # Use 80% of grid size to ensure it fits
        size = int(GRID_SIZE * 0.8)
        half_size = size // 2
        
        if self.mirror_type == '/':
            start = (self.position.x - half_size, self.position.y + half_size)
            end = (self.position.x + half_size, self.position.y - half_size)
        else:  # '\'
            start = (self.position.x - half_size, self.position.y - half_size)
            end = (self.position.x + half_size, self.position.y + half_size)
        
        # Draw thick mirror line
        pygame.draw.line(screen, CYAN, start, end, scale(5))

        # Draw hatching on the back side (like flat mirrors) to
        # distinguish from beam splitters which use a square outline.
        hatch_color = (CYAN[0] // 2, CYAN[1] // 2, CYAN[2] // 2)
        hatch_len = scale(7)
        num_hatches = 6
        for i in range(num_hatches):
            t = (i + 0.5) / num_hatches
            mx = int(start[0] + t * (end[0] - start[0]))
            my = int(start[1] + t * (end[1] - start[1]))
            if self.mirror_type == '/':
                # hatching below-right of the '/' line
                pygame.draw.line(screen, hatch_color,
                                 (mx + 2, my + 2),
                                 (mx + hatch_len, my + hatch_len), scale(1))
            else:
                # hatching below-left of the '\' line
                pygame.draw.line(screen, hatch_color,
                                 (mx - 2, my + 2),
                                 (mx - hatch_len, my + hatch_len), scale(1))
        
        # Add direction hints - smaller and closer to mirror
        hint_offset = int(GRID_SIZE * 0.4)
        hint_length = scale(10)
        if self.mirror_type == '/':
            # '/' mirror reflects: left↔top, bottom↔right
            # Show left→top reflection
            points = [
                (self.position.x - hint_offset, self.position.y),
                (self.position.x - hint_offset + hint_length, self.position.y),
                (self.position.x - hint_offset + hint_length, self.position.y - hint_length)
            ]
            pygame.draw.lines(screen, CYAN, False, points, scale(1))
            # Show bottom→right reflection
            points2 = [
                (self.position.x, self.position.y + hint_offset),
                (self.position.x, self.position.y + hint_offset - hint_length),
                (self.position.x + hint_length, self.position.y + hint_offset - hint_length)
            ]
            pygame.draw.lines(screen, CYAN, False, points2, scale(1))
        else:  # '\'
            # '\' mirror reflects: left↔bottom, top↔right
            # Show left→bottom reflection
            points = [
                (self.position.x - hint_offset, self.position.y),
                (self.position.x - hint_offset + hint_length, self.position.y),
                (self.position.x - hint_offset + hint_length, self.position.y + hint_length)
            ]
            pygame.draw.lines(screen, CYAN, False, points, scale(1))
            # Show top→right reflection
            points2 = [
                (self.position.x, self.position.y - hint_offset),
                (self.position.x, self.position.y - hint_offset + hint_length),
                (self.position.x + hint_length, self.position.y - hint_offset + hint_length)
            ]
            pygame.draw.lines(screen, CYAN, False, points2, scale(1))
        
        # Show debug info - keep it compact
        if self.debug:
            font = pygame.font.Font(None, scale_font(10))
            # Show mirror type and phase shift
            info_text = f"Mirror {self.mirror_type}: r={self.r:.0f} (π shift)"
            info_surface = font.render(info_text, True, CYAN)
            screen.blit(info_surface, (self.position.x - scale(30), self.position.y + scale(25)))
            
            # Show active ports if available
            if self._last_v_in is not None and self._last_v_out is not None:
                # Find non-zero input/output
                port_names = ['A', 'B', 'C', 'D']
                for i in range(4):
                    if abs(self._last_v_in[i]) > 0.001:
                        for j in range(4):
                            if abs(self._last_v_out[j]) > 0.001:
                                reflection_text = f"{port_names[i]}→{port_names[j]}"
                                refl_surface = font.render(reflection_text, True, CYAN)
                                screen.blit(refl_surface, (self.position.x - scale(20), 
                                                         self.position.y + scale(35)))
                                break
                        break
            
            # Show beam accumulation info in debug mode
            if hasattr(self, 'all_beams_by_port'):
                total_beams = sum(len(beams) for beams in self.all_beams_by_port.values())
                if total_beams > 0:
                    beam_text = f"Beams: {total_beams}"
                    beam_surface = font.render(beam_text, True, CYAN)
                    screen.blit(beam_surface, (self.position.x - scale(20), 
                                             self.position.y + scale(45)))
                    
                    # Show which ports have beams
                    ports_with_beams = []
                    for port_idx, beams in self.all_beams_by_port.items():
                        if beams:
                            ports_with_beams.append(port_names[port_idx])
                    if ports_with_beams:
                        ports_text = f"Ports: {','.join(ports_with_beams)}"
                        ports_surface = font.render(ports_text, True, CYAN)
                        screen.blit(ports_surface, (self.position.x - scale(20), 
                                                  self.position.y + scale(55)))