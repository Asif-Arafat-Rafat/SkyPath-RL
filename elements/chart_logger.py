"""
Chart logger for tracking direct vs drone relay communication over time
"""
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime

class ChartLogger:
    def __init__(self, log_dir="communication_logs"):
        """
        Initialize chart logger
        
        log_dir: directory to save logs and charts
        """
        self.log_dir = log_dir
        self.current_session = None
        self.data = {
            "timestamp": [],
            "direct_path_loss": [],
            "drone_relay_loss": [],
            "direct_power": [],
            "relay_power": [],
            "direct_better": [],
            "drone_altitude": [],
            "episode": []
        }
        self.episode_counter = 0
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log_communication(self, frame_num, direct_loss, relay_loss, tx_power, drone_alt, episode):
        """Log a communication snapshot"""
        self.data["timestamp"].append(frame_num)
        self.data["direct_path_loss"].append(direct_loss if direct_loss is not None else 0)
        self.data["drone_relay_loss"].append(relay_loss if relay_loss is not None else 0)
        
        # Calculate received power
        direct_power = tx_power - (direct_loss if direct_loss is not None else 80)
        relay_power = tx_power - (relay_loss if relay_loss is not None else 80)
        
        self.data["direct_power"].append(direct_power)
        self.data["relay_power"].append(relay_power)
        self.data["direct_better"].append(1 if direct_power > relay_power else 0)
        self.data["drone_altitude"].append(drone_alt)
        self.data["episode"].append(episode)
    
    def save_and_plot(self, filename_prefix="communication_analysis"):
        """Save data to JSON and generate charts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_filename = os.path.join(self.log_dir, f"{filename_prefix}_{timestamp}.json")
        with open(json_filename, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"Communication data saved to {json_filename}")
        
        # Generate comparison chart
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle(f"Direct Path vs Drone Relay Communication Analysis\n{timestamp}", fontsize=16)
            
            # Chart 1: Path Loss Comparison
            ax1 = axes[0, 0]
            ax1.plot(self.data["timestamp"], self.data["direct_path_loss"], 
                    label="Direct Path Loss", color='green', alpha=0.7)
            ax1.plot(self.data["timestamp"], self.data["drone_relay_loss"], 
                    label="Relay Path Loss", color='red', alpha=0.7)
            ax1.set_xlabel("Frame")
            ax1.set_ylabel("Path Loss (dB)")
            ax1.set_title("Path Loss Over Time")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Chart 2: Received Power Comparison
            ax2 = axes[0, 1]
            ax2.plot(self.data["timestamp"], self.data["direct_power"], 
                    label="Direct RX Power", color='green', alpha=0.7)
            ax2.plot(self.data["timestamp"], self.data["relay_power"], 
                    label="Relay RX Power", color='red', alpha=0.7)
            ax2.set_xlabel("Frame")
            ax2.set_ylabel("Received Power (dBm)")
            ax2.set_title("Received Power Over Time")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Chart 3: Which path is better
            ax3 = axes[1, 0]
            direct_wins = sum(self.data["direct_better"])
            relay_wins = len(self.data["direct_better"]) - direct_wins
            ax3.bar(["Direct Path", "Relay Path"], [direct_wins, relay_wins], color=['green', 'red'])
            ax3.set_ylabel("Times Better")
            ax3.set_title("Path Effectiveness Over Time")
            ax3.grid(True, alpha=0.3, axis='y')
            
            # Chart 4: Drone Altitude Over Time
            ax4 = axes[1, 1]
            ax4.plot(self.data["timestamp"], self.data["drone_altitude"], 
                    color='blue', alpha=0.7)
            ax4.set_xlabel("Frame")
            ax4.set_ylabel("Altitude (m)")
            ax4.set_title("Drone Altitude Optimization")
            ax4.grid(True, alpha=0.3)
            
            # Save figure
            chart_filename = os.path.join(self.log_dir, f"{filename_prefix}_{timestamp}.png")
            plt.tight_layout()
            plt.savefig(chart_filename, dpi=150)
            plt.close()
            print(f"Chart saved to {chart_filename}")
            
            # Print statistics
            print("\n=== Communication Statistics ===")
            print(f"Total frames: {len(self.data['timestamp'])}")
            print(f"Direct path better: {direct_wins} times ({100*direct_wins/len(self.data['direct_better']):.1f}%)")
            print(f"Relay path better: {relay_wins} times ({100*relay_wins/len(self.data['direct_better']):.1f}%)")
            
            if self.data["direct_path_loss"]:
                avg_direct_loss = sum(self.data["direct_path_loss"]) / len(self.data["direct_path_loss"])
                avg_relay_loss = sum(self.data["drone_relay_loss"]) / len(self.data["drone_relay_loss"])
                avg_altitude = sum(self.data["drone_altitude"]) / len(self.data["drone_altitude"])
                
                print(f"Average direct path loss: {avg_direct_loss:.2f} dB")
                print(f"Average relay path loss: {avg_relay_loss:.2f} dB")
                print(f"Average drone altitude: {avg_altitude:.1f} m")
                print(f"Best direct RX power: {max(self.data['direct_power']):.2f} dBm")
                print(f"Best relay RX power: {max(self.data['relay_power']):.2f} dBm")
            
        except Exception as e:
            print(f"Error generating charts: {e}")

    def render_latest_chart(self, filename_prefix="latest_communication"):
        """Render and save the latest chart image (overwrites) and return its path."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fig, axes = plt.subplots(2, 2, figsize=(10, 8))
            fig.suptitle(f"Direct vs Relay Communication\n{timestamp}", fontsize=12)

            # Path Loss
            ax1 = axes[0, 0]
            ax1.plot(self.data["timestamp"], self.data["direct_path_loss"], label="Direct Path Loss", color='green', alpha=0.8)
            ax1.plot(self.data["timestamp"], self.data["drone_relay_loss"], label="Relay Path Loss", color='red', alpha=0.8)
            ax1.set_xlabel("Frame")
            ax1.set_ylabel("Path Loss (dB)")
            ax1.legend(fontsize=8)
            ax1.grid(True, alpha=0.3)

            # Received Power
            ax2 = axes[0, 1]
            ax2.plot(self.data["timestamp"], self.data["direct_power"], label="Direct RX", color='green', alpha=0.8)
            ax2.plot(self.data["timestamp"], self.data["relay_power"], label="Relay RX", color='red', alpha=0.8)
            ax2.set_xlabel("Frame")
            ax2.set_ylabel("Power (dBm)")
            ax2.legend(fontsize=8)
            ax2.grid(True, alpha=0.3)

            # Path effectiveness
            ax3 = axes[1, 0]
            direct_wins = sum(self.data["direct_better"]) if self.data["direct_better"] else 0
            relay_wins = len(self.data["direct_better"]) - direct_wins if self.data["direct_better"] else 0
            ax3.bar(["Direct", "Relay"], [direct_wins, relay_wins], color=['green', 'red'])
            ax3.set_ylabel("Times Better")
            ax3.grid(True, axis='y', alpha=0.3)

            # Altitude
            ax4 = axes[1, 1]
            ax4.plot(self.data["timestamp"], self.data["drone_altitude"], color='blue', alpha=0.8)
            ax4.set_xlabel("Frame")
            ax4.set_ylabel("Altitude (m)")
            ax4.grid(True, alpha=0.3)

            plt.tight_layout()
            out_path = os.path.join(self.log_dir, f"{filename_prefix}.png")
            plt.savefig(out_path, dpi=120)
            plt.close(fig)
            return out_path
        except Exception as e:
            print(f"Error rendering latest chart: {e}")
            return None
    
    def reset(self):
        """Reset data for new session"""
        self.data = {
            "timestamp": [],
            "direct_path_loss": [],
            "drone_relay_loss": [],
            "direct_power": [],
            "relay_power": [],
            "direct_better": [],
            "drone_altitude": [],
            "episode": []
        }
