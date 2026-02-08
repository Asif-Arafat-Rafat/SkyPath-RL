"""
Signal visualization module - displays transmitted, degraded, and received signals
"""
import pygame
import math
import numpy as np
import random

class SignalVisualizer:
    def __init__(self, width=400, height=600, offset_x=0, offset_y=0):
        """
        Initialize signal visualizer
        width: width of the visualization area
        height: height of the visualization area
        offset_x, offset_y: position on screen
        """
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.surface = pygame.Surface((width, height))
        
        # Signal parameters
        self.frequency = 2.4e9  # 2.4 GHz
        self.amplitude_tx = 1.0
        self.amplitude_rx = 0.1  # Will be updated based on loss
        self.time = 0
        self.samples = 200  # number of samples to draw
        
    def draw_waveform(self, surface, x_start, y_center, amplitude, color, samples=200):
        """Draw a sinusoidal waveform as filled area"""
        # Ensure amplitude is valid
        if amplitude is None or amplitude <= 0 or not isinstance(amplitude, (int, float)):
            amplitude = 0.1
        
        # Check for NaN or inf
        if math.isnan(amplitude) or math.isinf(amplitude):
            amplitude = 0.1
            
        try:
            # Draw filled rectangles instead of polygon
            for i in range(samples - 1):
                x1 = int(x_start + (i / samples) * (self.width - 40))
                x2 = int(x_start + ((i + 1) / samples) * (self.width - 40))
                
                # Calculate y values
                y1 = int(y_center - amplitude * 30 * math.sin(2 * math.pi * i / samples))
                y2 = int(y_center - amplitude * 30 * math.sin(2 * math.pi * (i + 1) / samples))
                
                # Draw line from point to point
                if 0 <= x1 < surface.get_width() and 0 <= x2 < surface.get_width():
                    if 0 <= y1 < surface.get_height() and 0 <= y2 < surface.get_height():
                        pygame.draw.line(surface, color, (x1, y1), (x2, y2), 2)
        except Exception as e:
            print(f"Error drawing waveform: {e}")



    
    def draw_signal_visualization(self, screen, tx_power_dbm, path_loss_db, drone_relay_loss_db=None):
        """
        Draw the complete signal visualization
        
        tx_power_dbm: transmitted power in dBm
        path_loss_db: total path loss in dB (direct path)
        drone_relay_loss_db: total path loss through drone relay in dB (optional)
        """
        self.surface.fill((30, 30, 30))
        
        # Validate inputs
        if path_loss_db is None or math.isnan(path_loss_db) or math.isinf(path_loss_db):
            path_loss_db = 80.0  # Default loss
        if tx_power_dbm is None or math.isnan(tx_power_dbm) or math.isinf(tx_power_dbm):
            tx_power_dbm = 20.0  # Default TX power
        
        # Calculate received power for direct path
        rx_power_dbm = tx_power_dbm - path_loss_db
        
        # Normalize amplitudes (for visualization)
        # Convert dBm to linear for amplitude scaling
        try:
            tx_linear = 10 ** (tx_power_dbm / 20)  # Linear scale
            rx_linear = 10 ** (rx_power_dbm / 20)  # Linear scale
        except:
            tx_linear = 1.0
            rx_linear = 0.1
        
        # Ensure values are valid
        if math.isnan(tx_linear) or math.isinf(tx_linear):
            tx_linear = 1.0
        if math.isnan(rx_linear) or math.isinf(rx_linear):
            rx_linear = 0.1
        
        # Normalize to reasonable display values (0-1)
        max_linear = 10 ** (30 / 20)  # Reference level
        tx_amp_display = min(tx_linear / max_linear, 1.0)
        rx_amp_display = min(max(rx_linear / max_linear, 0.01), 1.0)
        
        # Ensure amplitudes are valid
        if math.isnan(tx_amp_display) or math.isinf(tx_amp_display) or tx_amp_display < 0:
            tx_amp_display = 0.5
        if math.isnan(rx_amp_display) or math.isinf(rx_amp_display) or rx_amp_display < 0:
            rx_amp_display = 0.1
        
        # Determine layout based on whether drone relay is available
        if drone_relay_loss_db is None:
            # Original layout: 3 rows (TX, degraded, RX)
            row_height = self.height // 4
            
            # --- Row 1: Transmitted Signal ---
            y1 = row_height
            pygame.draw.line(self.surface, (100, 100, 100), (10, y1), (self.width - 10, y1), 1)
            self.draw_waveform(self.surface, 10, y1, tx_amp_display, (0, 255, 0))
            
            # Label and info for transmitted
            font_small = pygame.font.SysFont("arial", 10)
            text = font_small.render(f"TX: {tx_power_dbm:.2f} dBm", True, (0, 255, 0))
            self.surface.blit(text, (10, y1 - 15))
            
            # --- Row 2: Signal After Loss (degraded) ---
            y2 = 2 * row_height
            pygame.draw.line(self.surface, (100, 100, 100), (10, y2), (self.width - 10, y2), 1)
            # Draw degraded signal with noise
            self._draw_noisy_waveform(self.surface, 10, y2, rx_amp_display, (255, 200, 0))
            
            # Label and info for degraded
            loss_info = f"Loss: {path_loss_db:.2f} dB"
            text = font_small.render(loss_info, True, (255, 200, 0))
            self.surface.blit(text, (10, y2 - 15))
            
            # --- Row 3: Received Signal ---
            y3 = 3 * row_height
            pygame.draw.line(self.surface, (100, 100, 100), (10, y3), (self.width - 10, y3), 1)
            self.draw_waveform(self.surface, 10, y3, rx_amp_display, (0, 100, 255))
            
            # Label and info for received
            text = font_small.render(f"RX (Direct): {rx_power_dbm:.2f} dBm", True, (0, 100, 255))
            self.surface.blit(text, (10, y3 - 15))
            
            # --- Header ---
            font_large = pygame.font.SysFont("arial", 14)
            title = font_large.render("Signal Propagation (Direct Path)", True, (255, 255, 255))
            self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 5))
        else:
            # Extended layout: 6 rows (TX, degraded direct, RX direct, drone relay path, degraded relay, RX relay)
            row_height = self.height // 7
            font_small = pygame.font.SysFont("arial", 9)
            font_large = pygame.font.SysFont("arial", 12)
            
            # --- Header ---
            title = font_large.render("Signal Propagation: Direct vs Drone Relay", True, (255, 255, 255))
            self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 5))
            
            # ===== DIRECT PATH =====
            y_offset = row_height * 1.2
            
            # Direct: TX
            y1 = y_offset
            pygame.draw.line(self.surface, (100, 100, 100), (10, y1), (self.width - 10, y1), 1)
            self.draw_waveform(self.surface, 10, y1, tx_amp_display, (0, 255, 0))
            text = font_small.render(f"TX: {tx_power_dbm:.2f} dBm", True, (0, 255, 0))
            self.surface.blit(text, (10, y1 - 12))
            
            # Direct: degraded
            y2 = y_offset + row_height
            pygame.draw.line(self.surface, (100, 100, 100), (10, y2), (self.width - 10, y2), 1)
            self._draw_noisy_waveform(self.surface, 10, y2, rx_amp_display, (255, 200, 0))
            text = font_small.render(f"Direct Loss: {path_loss_db:.2f} dB", True, (255, 200, 0))
            self.surface.blit(text, (10, y2 - 12))
            
            # Direct: RX
            y3 = y_offset + row_height * 2
            pygame.draw.line(self.surface, (100, 100, 100), (10, y3), (self.width - 10, y3), 1)
            self.draw_waveform(self.surface, 10, y3, rx_amp_display, (0, 100, 255))
            text = font_small.render(f"RX Direct: {rx_power_dbm:.2f} dBm", True, (0, 100, 255))
            self.surface.blit(text, (10, y3 - 12))
            
            # Separator
            sep_y = y_offset + row_height * 2.8
            pygame.draw.line(self.surface, (80, 80, 80), (10, sep_y), (self.width - 10, sep_y), 1)
            
            # ===== DRONE RELAY PATH =====
            y_offset_relay = y_offset + row_height * 3.2
            
            # Relay: TX to Drone + Drone to RX
            try:
                if drone_relay_loss_db is None or math.isnan(drone_relay_loss_db) or math.isinf(drone_relay_loss_db):
                    drone_relay_loss_db = 80.0
                
                rx_power_drone_dbm = tx_power_dbm - drone_relay_loss_db
                
                if math.isnan(rx_power_drone_dbm) or math.isinf(rx_power_drone_dbm):
                    rx_power_drone_dbm = -60.0
                
                rx_linear_drone = 10 ** (rx_power_drone_dbm / 20)
                
                if math.isnan(rx_linear_drone) or math.isinf(rx_linear_drone):
                    rx_linear_drone = 0.001
                
                rx_amp_display_drone = min(max(rx_linear_drone / max_linear, 0.01), 1.0)
                
                if math.isnan(rx_amp_display_drone) or math.isinf(rx_amp_display_drone):
                    rx_amp_display_drone = 0.1
            except Exception as e:
                print(f"Error calculating drone relay amplitude: {e}")
                rx_power_drone_dbm = -60.0
                rx_amp_display_drone = 0.1
            
            # Relay: TX (same as direct)
            y4 = y_offset_relay
            pygame.draw.line(self.surface, (100, 100, 100), (10, y4), (self.width - 10, y4), 1)
            self.draw_waveform(self.surface, 10, y4, tx_amp_display, (0, 255, 0))
            text = font_small.render(f"TX: {tx_power_dbm:.2f} dBm", True, (0, 255, 0))
            self.surface.blit(text, (10, y4 - 12))
            
            # Relay: degraded
            y5 = y_offset_relay + row_height
            pygame.draw.line(self.surface, (100, 100, 100), (10, y5), (self.width - 10, y5), 1)
            self._draw_noisy_waveform(self.surface, 10, y5, rx_amp_display_drone, (255, 150, 150))
            text = font_small.render(f"Via Drone Loss: {drone_relay_loss_db:.2f} dB", True, (255, 150, 150))
            self.surface.blit(text, (10, y5 - 12))
            
            # Relay: RX
            y6 = y_offset_relay + row_height * 2
            pygame.draw.line(self.surface, (100, 100, 100), (10, y6), (self.width - 10, y6), 1)
            self.draw_waveform(self.surface, 10, y6, rx_amp_display_drone, (150, 200, 255))
            text = font_small.render(f"RX Relay: {rx_power_drone_dbm:.2f} dBm", True, (150, 200, 255))
            self.surface.blit(text, (10, y6 - 12))
            
            # Comparison info
            comparison_y = y_offset_relay + row_height * 2.8
            gain = rx_power_dbm - rx_power_drone_dbm
            if gain > 0:
                comp_text = f"Direct is better by {gain:.2f} dB"
                comp_color = (0, 255, 0)
            else:
                comp_text = f"Relay is better by {-gain:.2f} dB"
                comp_color = (150, 200, 255)
            text = font_small.render(comp_text, True, comp_color)
            self.surface.blit(text, (10, comparison_y))
        
        # --- Draw border ---
        pygame.draw.rect(self.surface, (100, 100, 100), (0, 0, self.width, self.height), 2)
        
        # Blit to main screen
        screen.blit(self.surface, (self.offset_x, self.offset_y))
    
    def _draw_noisy_waveform(self, surface, x_start, y_center, amplitude, color, samples=200):
        """Draw a waveform with simulated noise"""
        # Ensure amplitude is valid
        if amplitude is None or amplitude <= 0 or not isinstance(amplitude, (int, float)):
            amplitude = 0.1
        
        # Check for NaN or inf
        if math.isnan(amplitude) or math.isinf(amplitude):
            amplitude = 0.1
            
        try:
            np.random.seed(int(self.time * 10) % 256)  # Deterministic noise
            for i in range(samples - 1):
                x1 = int(x_start + (i / samples) * (self.width - 40))
                x2 = int(x_start + ((i + 1) / samples) * (self.width - 40))
                
                # Signal with noise
                signal1 = amplitude * 30 * math.sin(2 * math.pi * i / samples)
                noise1 = np.random.normal(0, amplitude * 5)
                y1 = int(y_center - (signal1 + noise1))
                
                signal2 = amplitude * 30 * math.sin(2 * math.pi * (i + 1) / samples)
                noise2 = np.random.normal(0, amplitude * 5)
                y2 = int(y_center - (signal2 + noise2))
                
                # Draw line
                if 0 <= x1 < surface.get_width() and 0 <= x2 < surface.get_width():
                    if 0 <= y1 < surface.get_height() and 0 <= y2 < surface.get_height():
                        pygame.draw.line(surface, color, (x1, y1), (x2, y2), 1)
        except Exception as e:
            print(f"Error drawing noisy waveform: {e}")
    
    def update(self, dt=0.016):
        """Update animation state"""
        self.time += dt
