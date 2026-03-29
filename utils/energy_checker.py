"""Energy conservation checker for the interferometer system with scaling support."""
import logging
import pygame
from config.settings import scale, scale_font, CYAN, WHITE, BLACK

logger = logging.getLogger(__name__)

def check_energy_conservation(components, laser, beam_tracer):
    """
    Check energy conservation across the entire optical system.
    
    Returns a detailed report of energy flow.
    """
    logger.debug("=" * 60)
    logger.debug("ENERGY CONSERVATION ANALYSIS")
    logger.debug("=" * 60)

    # 1. Input energy (from laser)
    if laser and laser.enabled:
        input_power = 1.0  # Laser always outputs unit amplitude -> power = 1
        logger.debug("INPUT ENERGY:")
        logger.debug("  Laser at %s: Power = %.3f", laser.position, input_power)
    else:
        logger.debug("No active laser - no input energy")
        return

    # 2. Energy at each component
    logger.debug("COMPONENT ENERGY ANALYSIS:")
    
    total_bs_input = 0
    total_bs_output = 0
    
    for comp in components:
        if comp.component_type == "beamsplitter":
            if hasattr(comp, 'all_beams_by_port') and hasattr(comp, '_last_v_in') and hasattr(comp, '_last_v_out'):
                # Calculate input power
                input_power = 0
                if comp._last_v_in is not None:
                    input_power = sum(abs(v)**2 for v in comp._last_v_in)
                
                # Calculate output power
                output_power = 0
                if comp._last_v_out is not None:
                    output_power = sum(abs(v)**2 for v in comp._last_v_out)
                
                total_bs_input += input_power
                total_bs_output += output_power
                
                logger.debug("  Beam Splitter at %s:", comp.position)
                logger.debug("    Input power: %.3f", input_power)
                logger.debug("    Output power: %.3f", output_power)
                logger.debug("    Conservation: %s", 'OK' if abs(input_power - output_power) < 0.001 else 'VIOLATION!')

                # Show port details
                if comp._last_v_in is not None:
                    port_names = ['A', 'B', 'C', 'D']
                    for i, v in enumerate(comp._last_v_in):
                        if abs(v) > 0.001:
                            logger.debug("    Input %s: |v|²=%.3f", port_names[i], abs(v)**2)
                
        elif comp.component_type == "mirror":
            if hasattr(comp, '_last_v_in') and hasattr(comp, '_last_v_out'):
                input_power = 0
                if comp._last_v_in is not None:
                    input_power = sum(abs(v)**2 for v in comp._last_v_in)
                
                output_power = 0
                if comp._last_v_out is not None:
                    output_power = sum(abs(v)**2 for v in comp._last_v_out)
                
                if input_power > 0:
                    logger.debug("  Mirror at %s:", comp.position)
                    logger.debug("    Input power: %.3f", input_power)
                    logger.debug("    Output power: %.3f", output_power)
                    logger.debug("    Conservation: %s", 'OK' if abs(input_power - output_power) < 0.001 else 'VIOLATION!')
    
    # 3. Energy at detectors
    logger.debug("DETECTOR ENERGY:")
    
    detectors = [c for c in components if c.component_type == 'detector']
    total_detector_power = 0
    total_incoherent_sum = 0
    
    for detector in detectors:
        if hasattr(detector, 'get_energy_info'):
            info = detector.get_energy_info()
            coherent = info['coherent_intensity']
            incoherent = info['input_power_sum']
            
            total_detector_power += coherent
            total_incoherent_sum += incoherent
            
            logger.debug("  Detector at %s:", info['position'])
            logger.debug("    Number of beams: %d", info['num_beams'])
            logger.debug("    Incoherent sum (Σ|A_i|²): %.3f", incoherent)
            logger.debug("    Coherent intensity (|Σ E_i|²): %.3f", coherent)
            if incoherent > 0:
                logger.debug("    Interference factor: %.3f", coherent/incoherent)

            # Show individual beams
            for i, beam in enumerate(info['beams']):
                logger.debug("    Beam %d: A=%.3f, φ=%.1f°, P=%.3f", i+1, beam['amplitude'], beam['phase_deg'], beam['power'])
    
    # 4. Overall energy conservation
    logger.debug("-" * 60)
    logger.debug("SUMMARY:")
    logger.debug("  Input power (laser): 1.000")
    logger.debug("  Total detector power (coherent): %.3f", total_detector_power)
    logger.debug("  Total detector power (incoherent sum): %.3f", total_incoherent_sum)

    # Check if total coherent power equals input
    conservation_error = abs(total_detector_power - 1.0)
    if conservation_error < 0.01:
        logger.debug("  Energy conservation: OK (error = %.4f)", conservation_error)
    else:
        logger.warning("  Energy conservation: VIOLATION! (error = %.4f)", conservation_error)
        logger.warning("  Missing/excess energy: %+.3f", total_detector_power - 1.0)

    # 5. Beam tracing analysis
    if hasattr(beam_tracer, 'active_beams'):
        logger.debug("  Active beams in system: %d", len(beam_tracer.active_beams))

    logger.debug("=" * 60)
    
    return {
        'input_power': 1.0,
        'total_detector_power': total_detector_power,
        'conservation_error': conservation_error,
        'conserved': conservation_error < 0.01
    }


def trace_beam_paths(components, beam_tracer):
    """Trace and display all beam paths in the system."""
    logger.debug("=" * 60)
    logger.debug("BEAM PATH ANALYSIS")
    logger.debug("=" * 60)

    if not hasattr(beam_tracer, 'active_beams') or not beam_tracer.active_beams:
        logger.debug("No active beams in the system")
        return

    logger.debug("Total active beams: %d", len(beam_tracer.active_beams))

    for i, beam in enumerate(beam_tracer.active_beams):
        logger.debug("Beam %d:", i+1)
        logger.debug("  Position: %s", beam['position'])
        logger.debug("  Direction: %s", beam['direction'])
        logger.debug("  Amplitude: %.3f", beam['amplitude'])
        logger.debug("  Phase: %.1f°", beam.get('accumulated_phase', beam['phase']) * 180 / 3.14159)
        logger.debug("  Path length: %.1f", beam.get('total_path_length', 0))


class EnergyMonitor:
    """Visual energy monitor overlay for the game with scaling support."""
    
    def __init__(self):
        self.enabled = False
        self.last_report = None
        
    def toggle(self):
        """Toggle the energy monitor on/off."""
        self.enabled = not self.enabled
        return self.enabled
    
    def update(self, components, laser, beam_tracer):
        """Update the energy conservation data."""
        if self.enabled:
            self.last_report = check_energy_conservation(components, laser, beam_tracer)
    
    def draw(self, screen):
        """Draw energy conservation info on screen with scaling."""
        if not self.enabled or not self.last_report:
            return
        
        # Draw background panel - scaled dimensions
        panel_width = scale(300)
        panel_height = scale(150)
        panel_x = scale(10)
        panel_y = scale(100)
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 200))
        screen.blit(panel_surface, panel_rect.topleft)
        pygame.draw.rect(screen, CYAN, panel_rect, scale(2))
        
        # Draw title
        font_title = pygame.font.Font(None, scale_font(20))
        title = font_title.render("ENERGY CONSERVATION", True, CYAN)
        screen.blit(title, (panel_rect.x + scale(10), panel_rect.y + scale(10)))
        
        # Draw data
        font_data = pygame.font.Font(None, scale_font(16))
        y_offset = scale(40)
        
        # Input power
        text = font_data.render("Input Power: 1.000", True, WHITE)
        screen.blit(text, (panel_rect.x + scale(10), panel_rect.y + y_offset))
        y_offset += scale(20)
        
        # Total detector power
        detector_power = self.last_report['total_detector_power']
        color = (0, 255, 0) if self.last_report['conserved'] else (255, 0, 0)
        text = font_data.render(f"Total Detector Power: {detector_power:.3f}", True, color)
        screen.blit(text, (panel_rect.x + scale(10), panel_rect.y + y_offset))
        y_offset += scale(20)
        
        # Conservation error
        error = self.last_report['conservation_error']
        text = font_data.render(f"Conservation Error: {error:.4f}", True, color)
        screen.blit(text, (panel_rect.x + scale(10), panel_rect.y + y_offset))
        y_offset += scale(20)
        
        # Status
        status = "OK" if self.last_report['conserved'] else "VIOLATION!"
        text = font_data.render(f"Status: {status}", True, color)
        screen.blit(text, (panel_rect.x + scale(10), panel_rect.y + y_offset))
        
        # Hint
        hint_font = pygame.font.Font(None, scale_font(14))
        hint = hint_font.render("Press 'E' for detailed analysis", True, (150, 150, 150))
        screen.blit(hint, (panel_rect.x + scale(10), panel_rect.bottom - scale(20)))