"""
Data Panel - Semi-transparent overlay for displaying communication metrics
Press 1, 2, 3, 4 to switch between different data views
Overlay appears on top of the simulation
"""
import pygame
import math


class DataPanel:
    def __init__(self, width=350, height=280):
        """
        Initialize semi-transparent overlay data panel
        width, height: dimensions of the overlay window
        """
        self.width = width
        self.height = height
        self.mode = 1  # Current display mode (1, 2, 3, 4)
        
        # Position overlay in top-left corner with some margin
        self.offset_x = 10
        self.offset_y = 10
        
        # Create semi-transparent surface
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Fonts
        self.font_title = pygame.font.SysFont("arial", 16, bold=True)
        self.font_label = pygame.font.SysFont("arial", 12)
        self.font_value = pygame.font.SysFont("arial", 11)
        self.font_small = pygame.font.SysFont("arial", 9)
        
        # Background color with transparency (semi-transparent dark background)
        self.bg_color = (20, 20, 20, 200)  # 200/255 = 78% opaque
        self.border_color = (100, 100, 100, 255)
        self.expanded = False
        self.visible = True

    def set_mode(self, mode):
        """Set display mode (1, 2, 3, 4)"""
        if 1 <= mode <= 4:
            self.mode = mode

    def set_expanded(self, expanded, width=None, height=None, offset_x=None, offset_y=None):
        """Set expanded state and optionally override size/position.
        When expanded, the overlay will resize to provided width/height or stay large.
        """
        self.expanded = bool(expanded)
        if self.expanded:
            # expand to provided size or a large default
            if width and height:
                self.width = width
                self.height = height
            else:
                self.width = 800
                self.height = 600
            # position at top-left unless override
            self.offset_x = 0 if offset_x is None else offset_x
            self.offset_y = 0 if offset_y is None else offset_y
        else:
            # collapse to small overlay defaults
            self.width = 350
            self.height = 280
            self.offset_x = 10 if offset_x is None else offset_x
            self.offset_y = 10 if offset_y is None else offset_y
        # recreate surface with alpha
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def _update_history(self, relay_loss_db, drone_positions):
        """Keep a short history of relay loss and estimated delay for plotting."""
        # Estimate delay (ms) as base + per-hop component derived from number of drones
        num_hops = len(drone_positions) if drone_positions else 0
        base_delay_ms = 2.0  # base processing delay
        per_hop_ms = 1.5
        # incorporate signal degradation into small additional delay factor
        loss_factor_ms = 0.0
        try:
            if relay_loss_db is not None:
                loss_factor_ms = max(0.0, (relay_loss_db - 80.0) / 20.0)
        except Exception:
            loss_factor_ms = 0.0

        delay_ms = base_delay_ms + num_hops * per_hop_ms + loss_factor_ms

        # maintain rolling history
        if not hasattr(self, 'history_length'):
            self.history_length = 50
            self.delay_history = []
            self.relay_history = []
        self.delay_history.append(delay_ms)
        self.relay_history.append(relay_loss_db if relay_loss_db is not None else 0.0)
        if len(self.delay_history) > self.history_length:
            self.delay_history.pop(0)
            self.relay_history.pop(0)

    def draw_data(self, screen, tx_power_dbm, direct_loss_db, relay_loss_db, drone_positions, drone_controller=None):
        """
        Draw semi-transparent overlay data based on current mode
        """
        # Clear with transparency
        self.surface.fill((0, 0, 0, 0))
        
        # Draw semi-transparent background
        pygame.draw.rect(self.surface, self.bg_color, (0, 0, self.width, self.height))
        
        # Draw border
        pygame.draw.rect(self.surface, self.border_color, (0, 0, self.width, self.height), 2)
        
        # Update internal history used by the graphs
        self._update_history(relay_loss_db, drone_positions)

        # Draw content based on mode
        if self.mode == 1:
            self._draw_mode1_tx_power(tx_power_dbm, direct_loss_db)
        elif self.mode == 2:
            self._draw_mode2_direct_path(tx_power_dbm, direct_loss_db)
        elif self.mode == 3:
            self._draw_mode3_relay_path(tx_power_dbm, relay_loss_db, drone_positions)
        elif self.mode == 4:
            self._draw_mode4_comparison(tx_power_dbm, direct_loss_db, relay_loss_db)
        
        # Draw mode indicator at bottom
        self._draw_mode_indicator()
        
        # Blit overlay to screen if visible
        if getattr(self, 'visible', True):
            screen.blit(self.surface, (self.offset_x, self.offset_y))

    def _draw_mode1_tx_power(self, tx_power_dbm, direct_loss_db):
        """Mode 1: Transmitted Power & Direct Path Loss"""
        if tx_power_dbm is None or math.isnan(tx_power_dbm):
            tx_power_dbm = 20.0
        if direct_loss_db is None or math.isnan(direct_loss_db):
            direct_loss_db = 80.0
        
        rx_power_direct = tx_power_dbm - direct_loss_db
        
        # Title
        title = self.font_title.render("MODE 1: TX Power & Loss", True, (100, 200, 255))
        self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 15))
        
        y_offset = 60
        line_height = 35
        
        # Transmitted Power
        label = self.font_label.render("Transmitted Power:", True, (100, 200, 255))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{tx_power_dbm:.2f} dBm", True, (0, 255, 0))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 20
        
        # Path Loss
        label = self.font_label.render("Direct Path Loss:", True, (100, 200, 255))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{direct_loss_db:.2f} dB", True, (255, 200, 0))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 20
        
        # Received Power
        label = self.font_label.render("Received Power (Direct):", True, (100, 200, 255))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{rx_power_direct:.2f} dBm", True, (0, 100, 255))
        self.surface.blit(value, (30, y_offset + 20))

    def _draw_mode2_direct_path(self, tx_power_dbm, direct_loss_db):
        """Mode 2: Direct Path Details"""
        if tx_power_dbm is None or math.isnan(tx_power_dbm):
            tx_power_dbm = 20.0
        if direct_loss_db is None or math.isnan(direct_loss_db):
            direct_loss_db = 80.0
        
        rx_power_direct = tx_power_dbm - direct_loss_db
        quality = self._calculate_signal_quality(rx_power_direct)
        
        # Title
        title = self.font_title.render("MODE 2: Direct Path", True, (255, 200, 0))
        self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 15))
        
        y_offset = 70
        line_height = 30
        
        # Path Details
        label = self.font_label.render("Path:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        value = self.font_label.render("TX → RX (Direct)", True, (255, 200, 0))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 15
        
        # Loss breakdown
        label = self.font_label.render("Total Loss:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{direct_loss_db:.2f} dB", True, (255, 150, 0))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 15
        
        # Received Power
        label = self.font_label.render("Received Power:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{rx_power_direct:.2f} dBm", True, (0, 100, 255))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 15
        
        # Signal Quality
        label = self.font_label.render("Signal Quality:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        color = self._get_quality_color(quality)
        value = self.font_label.render(quality, True, color)
        self.surface.blit(value, (30, y_offset + 20))

    def _draw_mode3_relay_path(self, tx_power_dbm, relay_loss_db, drone_positions):
        """Mode 3: Relay Path Details"""
        if tx_power_dbm is None or math.isnan(tx_power_dbm):
            tx_power_dbm = 20.0
        if relay_loss_db is None or math.isnan(relay_loss_db):
            relay_loss_db = 100.0
        
        rx_power_relay = tx_power_dbm - relay_loss_db
        quality = self._calculate_signal_quality(rx_power_relay)
        num_drones = len(drone_positions) if drone_positions else 0
        
        # Title
        title = self.font_title.render("MODE 3: Relay Path", True, (150, 200, 100))
        self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 15))
        
        y_offset = 70
        line_height = 30
        
        # Path Details
        label = self.font_label.render("Path:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        value = self.font_label.render(f"TX → {num_drones} Drones → RX", True, (150, 200, 100))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 15
        
        # Number of Drones
        label = self.font_label.render("Active Relay Nodes:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{num_drones} drones", True, (150, 255, 150))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 15
        
        # Total Loss
        label = self.font_label.render("Total Path Loss:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{relay_loss_db:.2f} dB", True, (200, 150, 100))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 15
        
        # Received Power
        label = self.font_label.render("Received Power:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        value = self.font_value.render(f"{rx_power_relay:.2f} dBm", True, (150, 200, 255))
        self.surface.blit(value, (30, y_offset + 20))
        y_offset += line_height + 15
        
        # Signal Quality
        label = self.font_label.render("Signal Quality:", True, (150, 150, 150))
        self.surface.blit(label, (30, y_offset))
        color = self._get_quality_color(quality)
        value = self.font_label.render(quality, True, color)
        self.surface.blit(value, (30, y_offset + 20))
        
        # Draw delay vs relay-loss graph below the text
        self._draw_delay_vs_relay_graph(30, y_offset + 10, self.width - 60, 90)

    def _draw_mode4_comparison(self, tx_power_dbm, direct_loss_db, relay_loss_db):
        """Mode 4: Direct vs Relay Comparison"""
        if tx_power_dbm is None or math.isnan(tx_power_dbm):
            tx_power_dbm = 20.0
        if direct_loss_db is None or math.isnan(direct_loss_db):
            direct_loss_db = 80.0
        if relay_loss_db is None or math.isnan(relay_loss_db):
            relay_loss_db = 100.0
        
        rx_power_direct = tx_power_dbm - direct_loss_db
        rx_power_relay = tx_power_dbm - relay_loss_db
        
        # Title
        title = self.font_title.render("MODE 4: Direct vs Relay", True, (200, 100, 255))
        self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 15))
        
        y_offset = 65
        line_height = 25
        
        # DIRECT
        label = self.font_label.render("DIRECT PATH", True, (255, 200, 0))
        self.surface.blit(label, (30, y_offset))
        y_offset += line_height + 5
        
        label = self.font_label.render("Loss:", True, (150, 150, 150))
        self.surface.blit(label, (50, y_offset))
        value = self.font_value.render(f"{direct_loss_db:.2f} dB", True, (255, 200, 0))
        self.surface.blit(value, (180, y_offset))
        y_offset += line_height
        
        label = self.font_label.render("Power:", True, (150, 150, 150))
        self.surface.blit(label, (50, y_offset))
        value = self.font_value.render(f"{rx_power_direct:.2f} dBm", True, (0, 100, 255))
        self.surface.blit(value, (180, y_offset))
        y_offset += line_height + 15
        
        # RELAY
        label = self.font_label.render("RELAY PATH", True, (150, 200, 100))
        self.surface.blit(label, (30, y_offset))
        y_offset += line_height + 5
        
        label = self.font_label.render("Loss:", True, (150, 150, 150))
        self.surface.blit(label, (50, y_offset))
        value = self.font_value.render(f"{relay_loss_db:.2f} dB", True, (200, 150, 100))
        self.surface.blit(value, (180, y_offset))
        y_offset += line_height
        
        label = self.font_label.render("Power:", True, (150, 150, 150))
        self.surface.blit(label, (50, y_offset))
        value = self.font_value.render(f"{rx_power_relay:.2f} dBm", True, (150, 200, 255))
        self.surface.blit(value, (180, y_offset))
        y_offset += line_height + 20
        
        # DIFFERENCES
        loss_diff = relay_loss_db - direct_loss_db
        power_diff = rx_power_relay - rx_power_direct
        
        label = self.font_label.render("DIFFERENCE", True, (200, 100, 255))
        self.surface.blit(label, (30, y_offset))
        y_offset += line_height + 5
        
        label = self.font_label.render("Loss Δ:", True, (150, 150, 150))
        self.surface.blit(label, (50, y_offset))
        color = (0, 255, 0) if loss_diff < 0 else (255, 0, 0)
        value = self.font_value.render(f"{loss_diff:+.2f} dB", True, color)
        self.surface.blit(value, (180, y_offset))
        y_offset += line_height
        
        label = self.font_label.render("Power Δ:", True, (150, 150, 150))
        self.surface.blit(label, (50, y_offset))
        color = (0, 255, 0) if power_diff > 0 else (255, 0, 0)
        value = self.font_value.render(f"{power_diff:+.2f} dBm", True, color)
        self.surface.blit(value, (180, y_offset))
        y_offset += line_height + 12

        # Draw delay vs relay-loss graph in compare mode as well
        self._draw_delay_vs_relay_graph(30, y_offset, self.width - 60, 90)
        # If a chart image is available, render it inside the overlay (right side)
        if getattr(self, '_chart_surf_cached', None):
            try:
                # reserve right pane width
                img_w = min(400, self.width - 60)
                img_h = min(240, self.height - y_offset - 40)
                if img_w > 16 and img_h > 16:
                    scaled = pygame.transform.smoothscale(self._chart_surf_cached, (img_w, img_h))
                    img_x = self.width - img_w - 20
                    img_y = y_offset
                    self.surface.blit(scaled, (img_x, img_y))
            except Exception:
                pass

    def _draw_mode_indicator(self):
        """Draw mode indicator at bottom"""
        modes = ["1: TX Power", "2: Direct", "3: Relay", "4: Compare"]
        mode_text = " | ".join(modes)
        text = self.font_small.render(mode_text, True, (100, 100, 100))
        
        # Highlight current mode
        y_pos = self.height - 25
        pygame.draw.rect(self.surface, (40, 40, 40), (5, y_pos, self.width - 10, 20))
        pygame.draw.line(self.surface, (100, 100, 100), (5, y_pos), (self.width - 5, y_pos), 1)
        
        self.surface.blit(text, (self.width // 2 - text.get_width() // 2, y_pos + 2))

    def set_chart_path(self, path):
        """Provide a chart image path to the panel for in-mode rendering."""
        try:
            if path and path != getattr(self, 'chart_path', None):
                self.chart_path = path
                # try to load image immediately and cache surface
                try:
                    surf = pygame.image.load(path)
                    # convert with alpha if available
                    try:
                        surf = surf.convert_alpha()
                    except Exception:
                        surf = surf.convert()
                    self._chart_surf_cached = surf
                except Exception:
                    self._chart_surf_cached = None
        except Exception:
            self.chart_path = None
            self._chart_surf_cached = None

    def _draw_delay_vs_relay_graph(self, x, y, w, h):
        """Draw a small time-series: delay (ms) vs relay loss (dB)."""
        # Background for graph
        pygame.draw.rect(self.surface, (30, 30, 30, 200), (x, y, w, h))
        pygame.draw.rect(self.surface, (80, 80, 80), (x, y, w, h), 1)

        # Prepare points
        if not hasattr(self, 'delay_history') or len(self.delay_history) == 0:
            note = self.font_small.render("No history yet", True, (180, 180, 180))
            self.surface.blit(note, (x + 8, y + 8))
            return

        n = len(self.delay_history)
        # compute x positions
        xs = [x + 4 + i * (w - 8) / max(1, n - 1) for i in range(n)]

        # scale delay (left axis)
        max_delay = max(self.delay_history) if len(self.delay_history) else 1.0
        min_delay = min(self.delay_history) if len(self.delay_history) else 0.0
        d_range = max(1e-3, max_delay - min_delay)

        delay_points = [y + h - 4 - (d - min_delay) / d_range * (h - 12) for d in self.delay_history]

        # scale relay loss (right axis)
        max_loss = max(self.relay_history) if len(self.relay_history) else 1.0
        min_loss = min(self.relay_history) if len(self.relay_history) else 0.0
        loss_range = max(1e-3, max_loss - min_loss)
        loss_points = [y + h - 4 - (l - min_loss) / loss_range * (h - 12) for l in self.relay_history]

        # Draw grid lines
        for i in range(1, 3):
            yy = y + i * h / 3
            pygame.draw.line(self.surface, (50, 50, 50), (x + 4, yy), (x + w - 4, yy), 1)

        # Draw delay polyline (green)
        points_delay = list(zip(xs, delay_points))
        if len(points_delay) >= 2:
            pygame.draw.lines(self.surface, (0, 200, 0), False, points_delay, 2)

        # Draw relay-loss polyline (orange)
        points_loss = list(zip(xs, loss_points))
        if len(points_loss) >= 2:
            pygame.draw.lines(self.surface, (255, 150, 0), False, points_loss, 2)

        # Legend
        ld = self.font_small.render("Delay (ms)", True, (0, 200, 0))
        ll = self.font_small.render("Relay Loss (dB)", True, (255, 150, 0))
        self.surface.blit(ld, (x + 6, y + 6))
        self.surface.blit(ll, (x + 90, y + 6))

        # Axis labels (min/max)
        min_d_txt = self.font_small.render(f"{min_delay:.1f}", True, (180, 180, 180))
        max_d_txt = self.font_small.render(f"{max_delay:.1f}", True, (180, 180, 180))
        self.surface.blit(max_d_txt, (x + w - 36, y + 6))
        self.surface.blit(min_d_txt, (x + w - 36, y + h - 18))

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
