# TBS Converter Control Panel

A web-based control panel for managing MAVLink to CoT conversion and MediaMTX streaming on Raspberry Pi.

## Overview
This system provides:
- Conversion of MAVLink telemetry from TBS devices to Cursor on Target (CoT)
- Video streaming via MediaMTX
- Web-based control interface
- Automatic startup on boot

## Hardware Requirements
- Raspberry Pi (3 or newer recommended)
- TBS device configured to output MAVLink data
- Network connection between TBS device and Pi

## Installation

### 1. Basic Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip git

# Clone repository
cd /home/pi
git clone https://github.com/yourusername/tbs_converter.git
cd tbs_converter

# Install Python dependencies
pip3 install -r requirements.txt
```

### 2. MediaMTX Setup
```bash
# Download MediaMTX (replace URL with latest version)
wget https://github.com/bluenviron/mediamtx/releases/download/vX.X.X/mediamtx_vX.X.X_linux_arm64v8.tar.gz
tar -xzf mediamtx_vX.X.X_linux_arm64v8.tar.gz
rm mediamtx_vX.X.X_linux_arm64v8.tar.gz

# Make MediaMTX executable
chmod +x mediamtx
```

### 3. Service Installation
```bash
# Copy service file
sudo cp tbs-control.service /etc/systemd/system/

# Create log files and set permissions
sudo touch /var/log/tbs-control.log
sudo touch /var/log/tbs-control.error.log
sudo chown pi:pi /var/log/tbs-control.*

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tbs-control
sudo systemctl start tbs-control
```

## Configuration Files

### requirements.txt
```
flask
psutil
pymavlink
asyncio
```

### mediamtx.yml
Default MediaMTX configuration:
```yaml
# Global settings
logLevel: info
logDestinations: [stdout]

# RTSP settings
rtspAddress: :8554

# Path settings
paths:
  all:
    readUser: admin
    readPass: admin
```

### config.json
This file is automatically created with default settings:
```json
{
    "cot_ip": "",
    "cot_port": 6969,
    "mavlink_port": 5760
}
```

## Web Interface (http://pi-ip:3000)

### Control Tab
- Service Controls
  - MAVLink to CoT: Start/Stop conversion
  - MediaMTX: Start/Stop streaming
- Configuration
  - CoT IP Address: Target for CoT messages
  - CoT Port: Default 6969
  - MAVLink Port: Default 5760 (TBS input)

### Debug Tab
- Real-time log viewing
  - CoT conversion logs
  - MediaMTX streaming logs

## Network Configuration

### MAVLink
- Input: UDP port 5760 (configurable)
- Expected format: MAVLink telemetry from TBS device

### CoT Output
- Protocol: UDP
- Default port: 6969 (configurable)
- Format: Cursor on Target XML

### MediaMTX
- RTSP: 8554 (TCP), 8000 (UDP/RTP), 8001 (UDP/RTCP)
- RTMP: 1935
- HLS: 8888
- WebRTC: 8889 (HTTP), 8189 (ICE/UDP)
- SRT: 8890 (UDP)

## Service Management

### Control Service
```bash
# Start service
sudo systemctl start tbs-control

# Stop service
sudo systemctl stop tbs-control

# Restart service
sudo systemctl restart tbs-control

# Check status
sudo systemctl status tbs-control

# View logs
sudo journalctl -u tbs-control -f
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   - Check logs: `sudo journalctl -u tbs-control -f`
   - Verify permissions: `sudo chown -R pi:pi /home/pi/tbs_converter`
   - Check log files: `tail -f /var/log/tbs-control.log`

2. **Web Interface Inaccessible**
   - Verify Pi's IP: `ip addr show`
   - Check port 3000: `netstat -tuln | grep 3000`
   - Test local access: `curl http://localhost:3000`

3. **MAVLink Data Issues**
   - Verify TBS settings
   - Check UDP port: `netstat -tuln | grep 5760`
   - Monitor traffic: `tcpdump -i any udp port 5760`

4. **CoT Output Problems**
   - Verify target IP is reachable
   - Check UDP traffic: `tcpdump -i any udp port 6969`
   - Verify XML format in debug logs

### Log Locations
- Service logs: `/var/log/tbs-control.log`
- Error logs: `/var/log/tbs-control.error.log`
- System journal: `journalctl -u tbs-control`
- Web interface: Debug tab

## Security Considerations

### Network Security
- Change default MediaMTX credentials
- Use firewall to restrict access:
```bash
sudo ufw allow 3000/tcp  # Web interface
sudo ufw allow 5760/udp  # MAVLink input
sudo ufw allow 6969/udp  # CoT output
sudo ufw allow 8554/tcp  # RTSP (if needed)
sudo ufw allow 8000/udp  # RTP
sudo ufw allow 8001/udp  # RTCP
sudo ufw allow 1935/tcp  # RTMP
sudo ufw allow 8888/tcp  # HLS
sudo ufw allow 8889/tcp  # WebRTC HTTP
sudo ufw allow 8189/udp  # WebRTC ICE
sudo ufw allow 8890/udp  # SRT
```

### File Permissions
```bash
# Set correct ownership
sudo chown -R pi:pi /home/pi/tbs_converter

# Set appropriate permissions
chmod 644 config.json mediamtx.yml
chmod 755 mediamtx
```

## Maintenance

### Updates
```bash
# Update repository
cd /home/pi/tbs_converter
git pull

# Update dependencies
pip3 install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart tbs-control
```

### Backup
```bash
# Backup configuration
cp config.json config.json.backup
cp mediamtx.yml mediamtx.yml.backup

# Backup entire directory
tar -czf tbs-converter-backup.tar.gz /home/pi/tbs_converter
```

