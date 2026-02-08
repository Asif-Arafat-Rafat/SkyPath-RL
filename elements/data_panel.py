"""
Data Panel - Displays clear communication metrics and signal quality
"""
import pygame
import math


class DataPanel:
    def __init__(self, width=400, height=600, offset_x=0, offset_y=0):
        """
        Initialize data panel for displaying metrics
        width: width of the panel
        height: height of the panel
        offset_x, offset_y: position on screen
        """
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.surface = pygame.Surface((width, height))
        self.font_title = pygame.font.SysFont("arial", 16, bold=True)
        self.font_label = pygame.font.SysFont("arial", 12)
        self.font_value = pygame.font.SysFont("arial", 11)

    def draw_data_comparison(self, screen, tx_power_dbm, direct_loss_db, relay_loss_db, drone_positions):
        """
        Draw comprehensive data comparison: Direct vs Relay
        
        tx_power_dbm: transmitted power in dBm
        direct_loss_db: total path loss for direct path in dB
        relay_loss_db: total path loss for relay in dB
        drone_positions: list of drone positions
        """
        self.surface.fill((20, 20, 20))
        
        # Validate inputs
        if direct_loss_db is None or math.isnan(direct_loss_db):
            direct_loss_db = 80.0
        if relay_loss_db is None or math.isnan(relay_loss_db):
            relay_loss_db = 100.0
        if tx_power_dbm is None or math.isnan(tx_power_dbm):
            tx_power_dbm = 20.0
        
        # Calculate received powers
        rx_power_direct = tx_power_dbm - direct_loss_db
        rx_power_relay = tx_power_dbm - relay_loss_db
        
        # Title
        title = self.font_title.render("Communication Metrics", True, (255, 255, 255))
        self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 10))
        
        y_offset = 40
        line_height = 25
        
        # --- TRANSMITTED POWER ---
        label = self.font_label.render("Transmitted Power:", True, (100, 200, 255))
        self.surface.blit(label, (20, y_offset))
        value = self.font_value.render(f"{tx_power_dbm:.2f} dBm", True, (0, 255, 0))
        self.surface.blit(value, (self.width - 100, y_offset))
        y_offset += line_height
        
        # Separator
        pygame.draw.line(self.surface, (80, 80, 80), (20, y_offset - 5), (self.width - 20, y_offset - 5), 1)
        y_offset += 10
        
        # --- DIRECT PATH ---
        label = self.font_label.render("DIRECT PATH (TX → RX):", True, (255, 200, 0))
        self.surface.blit(label, (20, y_offset))
        y_offset += line_height
        
        # Direct loss
        label = self.font_label.render("Path Loss:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        value = self.font_value.render(f"{direct_loss_db:.2f} dB", True, (255, 200, 0))
        self.surface.blit(value, (self.width - 100, y_offset))
        y_offset += line_height
        
        # Received power direct
        label = self.font_label.render("Received Power:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        value = self.font_value.render(f"{rx_power_direct:.2f} dBm", True, (0, 100, 255))
        self.surface.blit(value, (self.width - 100, y_offset))
        y_offset += line_height
        
        # Signal quality indicator for direct
        quality_direct = self._calculate_signal_quality(rx_power_direct)
        label = self.font_label.render("Quality:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        color = self._get_quality_color(quality_direct)
        value = self.font_value.render(quality_direct, True, color)
        self.surface.blit(value, (self.width - 120, y_offset))
        y_offset += line_height + 5
        
        # Separator
        pygame.draw.line(self.surface, (80, 80, 80), (20, y_offset - 5), (self.width - 20, y_offset - 5), 1)
        y_offset += 10
        
        # --- RELAY PATH ---
        label = self.font_label.render("RELAY PATH (TX → Drones → RX):", True, (255, 200, 0))
        self.surface.blit(label, (20, y_offset))
        y_offset += line_height
        
        # Number of drones
        num_drones = len(drone_positions) if drone_positions else 0
        label = self.font_label.render(f"Drones in Relay:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        value = self.font_value.render(f"{num_drones}", True, (150, 255, 150))
        self.surface.blit(value, (self.width - 100, y_offset))
        y_offset += line_height
        
        # Relay loss
        label = self.font_label.render("Total Path Loss:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        value = self.font_value.render(f"{relay_loss_db:.2f} dB", True, (200, 150, 100))
        self.surface.blit(value, (self.width - 100, y_offset))
        y_offset += line_height
        
        # Received power relay
        label = self.font_label.render("Received Power:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        value = self.font_value.render(f"{rx_power_relay:.2f} dBm", True, (150, 200, 255))
        self.surface.blit(value, (self.width - 100, y_offset))
        y_offset += line_height
        
        # Signal quality indicator for relay
        quality_relay = self._calculate_signal_quality(rx_power_relay)
        label = self.font_label.render("Quality:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        color = self._get_quality_color(quality_relay)
        value = self.font_value.render(quality_relay, True, color)
        self.surface.blit(value, (self.width - 120, y_offset))
        y_offset += line_height + 5
        
        # Separator
        pygame.draw.line(self.surface, (80, 80, 80), (20, y_offset - 5), (self.width - 20, y_offset - 5), 1)
        y_offset += 10
        
        # --- COMPARISON ---
        label = self.font_label.render("Comparison:", True, (100, 200, 255))
        self.surface.blit(label, (20, y_offset))
        y_offset += line_height
        
        # Loss difference
        loss_diff = relay_loss_db - direct_loss_db
        label = self.font_label.render("Loss Difference:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        color = (0, 255, 0) if loss_diff < 0 else (255, 0, 0)
        value = self.font_value.render(f"{loss_diff:+.2f} dB", True, color)
        self.surface.blit(value, (self.width - 100, y_offset))
        y_offset += line_height
        
        # Power difference
        power_diff = rx_power_relay - rx_power_direct
        label = self.font_label.render("Power Gain:", True, (150, 150, 150))
        self.surface.blit(label, (40, y_offset))
        color = (0, 255, 0) if power_diff > 0 else (255, 0, 0)
        value = self.font_value.render(f"{power_diff:+.2f} dBm", True, color)
        self.surface.blit(value, (self.width - 100, y_offset))
        
        # Blit to screen
        screen.blit(self.surface, (self.offset_x, self.offset_y))

    def _calculate_signal_quality(self, rx_power_dbm):
        """Determine signal quality based on received power"""
        if rx_power_dbm >= -30:
            return "Excellent"
        elif rx_power_dbm >= -50:
            return "Good"
        elif rx_power_dbm >= -70:
            return "Fair"
        elif rx_power_dbm >= -85:
            return "Poor"
        else:
            return "Critical"

    def _get_quality_color(self, quality):
        """Get color for signal quality"""
        if quality == "Excellent":
            return (0, 255, 0)  # Green
        elif quality == "Good":
            return (100, 255, 0)  # Yellow-Green
        elif quality == "Fair":
            return (255, 200, 0)  # Yellow
        elif quality == "Poor":
            return (255, 100, 0)  # Orange
        else:  # Critical
            return (255, 0, 0)  # Red
