"""Energy conservation checker for the interferometer system."""
import pygame

def check_energy_conservation(components, laser, beam_tracer):
    """
    Check energy conservation across the entire optical system.
    
    Returns a detailed report of energy flow.
    """
    print("\n" + "="*60)
    print("ENERGY CONSERVATION ANALYSIS")
    print("="*60)
    
    # 1. Input energy (from laser)
    if laser and laser.enabled:
        input_power = 1.0  # Laser always outputs unit amplitude -> power = 1
        print(f"\nINPUT ENERGY:")
        print(f"  Laser at {laser.position}: Power = {input_power:.3f}")
    else:
        print("\nNo active laser - no input energy")
        return
    
    # 2. Energy at each component
    print(f"\nCOMPONENT ENERGY ANALYSIS:")
    
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
                
                print(f"\n  Beam Splitter at {comp.position}:")
                print(f"    Input power: {input_power:.3f}")
                print(f"    Output power: {output_power:.3f}")
                print(f"    Conservation: {'OK' if abs(input_power - output_power) < 0.001 else 'VIOLATION!'}")
                
                # Show port details
                if comp._last_v_in is not None:
                    port_names = ['A', 'B', 'C', 'D']
                    for i, v in enumerate(comp._last_v_in):
                        if abs(v) > 0.001:
                            print(f"    Input {port_names[i]}: |v|²={abs(v)**2:.3f}")
                
        elif comp.component_type == "mirror":
            if hasattr(comp, '_last_v_in') and hasattr(comp, '_last_v_out'):
                input_power = 0
                if comp._last_v_in is not None:
                    input_power = sum(abs(v)**2 for v in comp._last_v_in)
                
                output_power = 0
                if comp._last_v_out is not None:
                    output_power = sum(abs(v)**2 for v in comp._last_v_out)
                
                if input_power > 0:
                    print(f"\n  Mirror at {comp.position}:")
                    print(f"    Input power: {input_power:.3f}")
                    print(f"    Output power: {output_power:.3f}")
                    print(f"    Conservation: {'OK' if abs(input_power - output_power) < 0.001 else 'VIOLATION!'}")
    
    # 3. Energy at detectors
    print(f"\nDETECTOR ENERGY:")
    
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
            
            print(f"\n  Detector at {info['position']}:")
            print(f"    Number of beams: {info['num_beams']}")
            print(f"    Incoherent sum (Σ|A_i|²): {incoherent:.3f}")
            print(f"    Coherent intensity (|Σ E_i|²): {coherent:.3f}")
            if incoherent > 0:
                print(f"    Interference factor: {coherent/incoherent:.3f}")
            
            # Show individual beams
            for i, beam in enumerate(info['beams']):
                print(f"    Beam {i+1}: A={beam['amplitude']:.3f}, φ={beam['phase_deg']:.1f}°, P={beam['power']:.3f}")
    
    # 4. Overall energy conservation
    print(f"\n" + "-"*60)
    print(f"SUMMARY:")
    print(f"  Input power (laser): 1.000")
    print(f"  Total detector power (coherent): {total_detector_power:.3f}")
    print(f"  Total detector power (incoherent sum): {total_incoherent_sum:.3f}")
    
    # Check if total coherent power equals input
    conservation_error = abs(total_detector_power - 1.0)
    if conservation_error < 0.01:
        print(f"  Energy conservation: OK (error = {conservation_error:.4f})")
    else:
        print(f"  Energy conservation: VIOLATION! (error = {conservation_error:.4f})")
        print(f"  Missing/excess energy: {total_detector_power - 1.0:+.3f}")
    
    # 5. Beam tracing analysis
    if hasattr(beam_tracer, 'active_beams'):
        print(f"\n  Active beams in system: {len(beam_tracer.active_beams)}")
    
    print("="*60 + "\n")
    
    return {
        'input_power': 1.0,
        'total_detector_power': total_detector_power,
        'conservation_error': conservation_error,
        'conserved': conservation_error < 0.01
    }


def trace_beam_paths(components, beam_tracer):
    """Trace and display all beam paths in the system."""
    print("\n" + "="*60)
    print("BEAM PATH ANALYSIS")
    print("="*60)
    
    if not hasattr(beam_tracer, 'active_beams') or not beam_tracer.active_beams:
        print("No active beams in the system")
        return
    
    print(f"Total active beams: {len(beam_tracer.active_beams)}")
    
    for i, beam in enumerate(beam_tracer.active_beams):
        print(f"\nBeam {i+1}:")
        print(f"  Position: {beam['position']}")
        print(f"  Direction: {beam['direction']}")
        print(f"  Amplitude: {beam['amplitude']:.3f}")
        print(f"  Phase: {beam.get('accumulated_phase', beam['phase']) * 180 / 3.14159:.1f}°")
        print(f"  Path length: {beam.get('total_path_length', 0):.1f}")


class EnergyMonitor:
    """Visual energy monitor overlay for the game."""
    
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
        """Draw energy conservation info on screen."""
        if not self.enabled or not self.last_report:
            return
        
        # Draw background panel
        panel_rect = pygame.Rect(10, 100, 300, 150)
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 200))
        screen.blit(panel_surface, panel_rect.topleft)
        pygame.draw.rect(screen, (0, 255, 255), panel_rect, 2)
        
        # Draw title
        font_title = pygame.font.Font(None, 20)
        title = font_title.render("ENERGY CONSERVATION", True, (0, 255, 255))
        screen.blit(title, (panel_rect.x + 10, panel_rect.y + 10))
        
        # Draw data
        font_data = pygame.font.Font(None, 16)
        y_offset = 40
        
        # Input power
        text = font_data.render("Input Power: 1.000", True, (255, 255, 255))
        screen.blit(text, (panel_rect.x + 10, panel_rect.y + y_offset))
        y_offset += 20
        
        # Total detector power
        detector_power = self.last_report['total_detector_power']
        color = (0, 255, 0) if self.last_report['conserved'] else (255, 0, 0)
        text = font_data.render(f"Total Detector Power: {detector_power:.3f}", True, color)
        screen.blit(text, (panel_rect.x + 10, panel_rect.y + y_offset))
        y_offset += 20
        
        # Conservation error
        error = self.last_report['conservation_error']
        text = font_data.render(f"Conservation Error: {error:.4f}", True, color)
        screen.blit(text, (panel_rect.x + 10, panel_rect.y + y_offset))
        y_offset += 20
        
        # Status
        status = "OK" if self.last_report['conserved'] else "VIOLATION!"
        text = font_data.render(f"Status: {status}", True, color)
        screen.blit(text, (panel_rect.x + 10, panel_rect.y + y_offset))
        
        # Hint
        hint_font = pygame.font.Font(None, 14)
        hint = hint_font.render("Press 'E' for detailed analysis", True, (150, 150, 150))
        screen.blit(hint, (panel_rect.x + 10, panel_rect.bottom - 20))