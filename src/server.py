from flask import Flask, render_template, jsonify, request
import subprocess
import os
import json
import psutil
from threading import Thread
import asyncio
from mavlink_to_cot import MavlinkToCot

app = Flask(__name__, 
    template_folder='../templates',  # Look for templates one directory up
    static_folder='../static'        # Look for static files one directory up
)

class ServiceManager:
    def __init__(self):
        self.mavlink_process = None
        self.mediamtx_process = None
        self.config = self.load_config()
        self.cot_logs = []
        self.mediamtx_logs = []
        self.error_state = {'mavlink': None, 'mediamtx': None}
        # Start MediaMTX by default
        self.start_mediamtx()
        
    def load_config(self):
        try:
            with open('config/config.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Default configuration
            config = {
                'cot_ip': '',
                'cot_port': 6969,
                'mavlink_port': 5760
            }
            self.save_config(config)
            return config
            
    def save_config(self, config):
        # Ensure config directory exists
        os.makedirs('config', exist_ok=True)
        with open('config/config.json', 'w') as f:
            json.dump(config, f, indent=4)

    def log_error(self, service, error):
        """Log error and store it in error state"""
        error_msg = f"Error in {service}: {str(error)}"
        if service == 'mavlink':
            self.cot_logs.append(error_msg)
            self.error_state['mavlink'] = error_msg
        else:
            self.mediamtx_logs.append(error_msg)
            self.error_state['mediamtx'] = error_msg

    def start_mavlink(self):
        if not self.config['cot_ip']:
            self.log_error('mavlink', "CoT IP address not configured")
            return False

        try:
            if self.mavlink_process is None:
                def log_callback(message):
                    self.cot_logs.append(message)
                    if len(self.cot_logs) > 1000:
                        self.cot_logs = self.cot_logs[-1000:]

                self.mavlink_process = MavlinkToCot(
                    mavlink_port=self.config['mavlink_port'],
                    cot_ip=self.config['cot_ip'],
                    cot_port=self.config['cot_port'],
                    log_callback=log_callback
                )
                Thread(target=self._run_mavlink).start()
                self.error_state['mavlink'] = None
                return True
        except Exception as e:
            self.log_error('mavlink', e)
            self.mavlink_process = None
            return False
        return False

    def _run_mavlink(self):
        """Protected method to run mavlink process with error handling"""
        try:
            asyncio.run(self.mavlink_process.run())
        except Exception as e:
            self.log_error('mavlink', e)
            self.mavlink_process = None

    def stop_mavlink(self):
        if self.mavlink_process:
            self.mavlink_process = None
            return True
        return False

    def start_mediamtx(self):
        try:
            if self.mediamtx_process is None:
                # Check if mediamtx exists
                if not os.path.exists('./video/mediamtx'):
                    self.log_error('mediamtx', "MediaMTX executable not found")
                    return False

                self.mediamtx_process = subprocess.Popen(
                    ['./mediamtx'],  # Just run the executable
                    cwd='./video',    # Set working directory to where mediamtx and its config are
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Start output monitoring threads
                Thread(target=self._monitor_mediamtx_output, args=(self.mediamtx_process.stdout,)).start()
                Thread(target=self._monitor_mediamtx_output, args=(self.mediamtx_process.stderr,)).start()
                
                self.error_state['mediamtx'] = None
                return True
        except Exception as e:
            self.log_error('mediamtx', e)
            self.mediamtx_process = None
            return False
        return False

    def _monitor_mediamtx_output(self, pipe):
        """Monitor MediaMTX output streams"""
        try:
            for line in iter(pipe.readline, b''):
                # Parse and format the line
                text = line.decode().strip()
                
                # Skip empty lines
                if not text:
                    continue
                    
                # Format timestamp and level
                parts = text.split(' ', 3)  # Split into [date, time, level, message]
                if len(parts) >= 4:
                    date, time, level, message = parts
                    # Color-code the level
                    if 'ERR' in level:
                        formatted = f"🔴  {time}  {message}"  # Added extra spacing
                    elif 'WAR' in level:
                        formatted = f"⚠️  {time}  {message}"  # Added extra spacing
                    elif 'INF' in level:
                        formatted = f"ℹ️  {time}  {message}"  # Added extra spacing
                    else:
                        formatted = f"    {time}  {message}"  # Added extra spacing
                else:
                    formatted = text

                # Add to logs with newline
                self.mediamtx_logs.append(formatted + "\n")  # Add newline
                if len(self.mediamtx_logs) > 1000:
                    self.mediamtx_logs = self.mediamtx_logs[-1000:]
                
        except Exception as e:
            self.log_error('mediamtx', f"Output monitoring error: {e}")

    def stop_mediamtx(self):
        if self.mediamtx_process:
            self.mediamtx_process.terminate()
            self.mediamtx_process = None
            return True
        return False

    def get_status(self):
        return {
            'mavlink_running': self.mavlink_process is not None,
            'mediamtx_running': self.mediamtx_process is not None if self.mediamtx_process else False,
            'config': self.config,
            'errors': self.error_state
        }

    def get_logs(self):
        return {
            'cot': self.cot_logs[-1000:],  # Keep last 1000 lines
            'mediamtx': self.mediamtx_logs[-1000:]  # Keep last 1000 lines
        }

manager = ServiceManager()

@app.route('/')
def index():
    return render_template('index.html', status=manager.get_status())

@app.route('/api/status')
def status():
    return jsonify(manager.get_status())

@app.route('/api/mavlink/start', methods=['POST'])
def start_mavlink():
    success = manager.start_mavlink()
    return jsonify({'success': success})

@app.route('/api/mavlink/stop', methods=['POST'])
def stop_mavlink():
    success = manager.stop_mavlink()
    return jsonify({'success': success})

@app.route('/api/mediamtx/start', methods=['POST'])
def start_mediamtx():
    success = manager.start_mediamtx()
    return jsonify({'success': success})

@app.route('/api/mediamtx/stop', methods=['POST'])
def stop_mediamtx():
    success = manager.stop_mediamtx()
    return jsonify({'success': success})

@app.route('/api/config', methods=['POST'])
def update_config():
    config = request.json
    manager.save_config(config)
    manager.config = config
    return jsonify({'success': True})

@app.route('/api/logs')
def get_logs():
    return jsonify(manager.get_logs())

if __name__ == '__main__':
    # Initialize manager which will start MediaMTX
    manager = ServiceManager()
    app.run(host='0.0.0.0', port=3000) 