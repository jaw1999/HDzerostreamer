import asyncio
from pymavlink import mavutil
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import socket
import time

# Configuration settings
TARGET_IP = "127.0.0.1"  # Change this to your target IP
TARGET_PORT = 6969         # Change this to your target port
MAVLINK_PORT = 5760         # MAVLink input port

class MavlinkToCot:
    def __init__(self, mavlink_port=5760, cot_ip=None, cot_port=6969, log_callback=None):
        self.mavlink_port = mavlink_port
        self.cot_ip = cot_ip
        self.cot_port = cot_port
        self.mav_connection = None
        self.cot_socket = None
        self.uid = f"UAS-TBS-{int(time.time())}"
        self.log_callback = log_callback  # Function to call with log messages
        
    def log(self, message):
        """Log a message and call the callback if it exists"""
        print(message)  # Still print to console
        if self.log_callback:
            self.log_callback(message)

    def connect_mavlink(self):
        """Establish MAVLink connection"""
        # Listen on all interfaces (0.0.0.0) for incoming UDP
        connection_string = f'udpin:0.0.0.0:{self.mavlink_port}'
        try:
            self.log(f"Attempting MAVLink connection on {connection_string}...")
            self.mav_connection = mavutil.mavlink_connection(connection_string)
            self.log("✓ Successfully connected to MAVLink")
            return True
        except Exception as e:
            self.log(f"✗ Failed to connect to MAVLink: {e}")
            return False

    def setup_cot_socket(self):
        """Setup UDP socket for CoT transmission"""
        self.cot_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def create_cot_pli(self, lat, lon, alt, heading):
        """Create CoT PLI message for UAS"""
        root = ET.Element("event")
        root.set("version", "2.0")
        # Use the persistent UID instead of creating a new one each time
        root.set("uid", self.uid)
        root.set("type", "a-f-A-M-F-Q")
        root.set("how", "m-g")  # Adding back how='m-g' for GPS measurement
        
        # Set proper time windows
        now = datetime.utcnow()
        stale_time = now + timedelta(minutes=1)  # Stale after 1 minute
        root.set("time", now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        root.set("start", now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        root.set("stale", stale_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

        point = ET.SubElement(root, "point")
        point.set("lat", str(lat))
        point.set("lon", str(lon))
        point.set("hae", str(alt))
        point.set("ce", "9999999.0")
        point.set("le", "9999999.0")

        detail = ET.SubElement(root, "detail")
        
        # Use same UID in detail section
        uid_detail = ET.SubElement(detail, "uid")
        uid_detail.text = self.uid
        
        contact = ET.SubElement(detail, "contact")
        contact.set("callsign", "TBS-UAS")
        
        track = ET.SubElement(detail, "track")
        track.set("course", str(heading))
        # Add vertical velocity and speed if available from MAVLink
        track.set("speed", "0.00000000")
        
        # Add UAS specific details
        status = ET.SubElement(detail, "status")
        status.set("readiness", "true")
        
        # Add precision location info
        precisionlocation = ET.SubElement(detail, "precisionlocation")
        precisionlocation.set("altsrc", "GPS")
        precisionlocation.set("geopointsrc", "GPS")

        return ET.tostring(root)

    async def process_mavlink(self):
        """Process MAVLink messages and convert to CoT"""
        while True:
            msg = self.mav_connection.recv_match(
                type=['GLOBAL_POSITION_INT', 'ATTITUDE'],
                blocking=True
            )
            
            if msg is not None:
                if msg.get_type() == 'GLOBAL_POSITION_INT':
                    lat = msg.lat / 1e7  # Convert from degE7 to degrees
                    lon = msg.lon / 1e7
                    alt = msg.alt / 1000  # Convert from mm to meters
                    heading = msg.hdg / 100 if msg.hdg != 0 else 0  # Convert from cdeg to degrees
                    
                    # Create and send CoT message
                    cot_msg = self.create_cot_pli(lat, lon, alt, heading)
                    self.cot_socket.sendto(cot_msg, (self.cot_ip, self.cot_port))
                    self.log(f"Sent CoT message - Position: {lat:.6f}, {lon:.6f}, Alt: {alt:.1f}m, Heading: {heading:.1f}°")
            
            await asyncio.sleep(0.1)  # Small delay to prevent CPU overload

    async def run(self):
        """Main run loop"""
        if not self.connect_mavlink():
            return
        
        self.setup_cot_socket()
        
        try:
            await self.process_mavlink()
        except KeyboardInterrupt:
            self.log("Shutting down...")
        finally:
            if self.mav_connection:
                self.mav_connection.close()
            if self.cot_socket:
                self.cot_socket.close()

if __name__ == "__main__":
    # Create instance using the configured values
    bridge = MavlinkToCot()
    
    # Run the bridge
    asyncio.run(bridge.run()) 