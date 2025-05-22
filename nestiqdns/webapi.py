from flask import Flask, request, Response, jsonify
import re
import ipaddress
import redis
import threading

class WebAPIServer:
    def __init__(self, host='0.0.0.0', port=5000, db_host='127.0.0.1', db_port=6379):
        self.host = host
        self.port = port
        self.db_host = db_host
        self.db_port = db_port
        self.db = None
        self.app = Flask(__name__)
        self._thread = None
        self._server_running = threading.Event()
        self._register_routes()

    def _register_routes(self):
        @self.app.route('/nic/update', methods=['GET', 'POST'])
        def nic_update():
            # Extract parameters according to No-IP/ChangeDNS API
            hostname = request.args.get('hostname')
            myip = request.args.get('myip')

            # Basic validation (real implementation should update DNS)
            if not hostname:
                return Response('nohost', status=400)

            # Hostname validation: must be a valid DNS name
            hostname_regex = re.compile(r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$')
            if not hostname_regex.match(hostname):
                return Response('nohost', status=400)

            # If myip is not provided, use the remote address
            if not myip:
                # Common headers used by proxies to forward the client IP
                header_keys = [
                    'X-Forwarded-For',
                    'X-Real-IP',
                    'CF-Connecting-IP',
                    'Forwarded',
                    'Forwarded-For',
                    'True-Client-IP',
                    'X-Client-IP',
                    'X-Cluster-Client-IP',
                    'Fastly-Client-Ip',
                    'X-Forwarded',
                    'X-Forwarded-Host',
                    'X-ProxyUser-Ip',
                    'X-Original-Forwarded-For',
                ]
                for key in header_keys:
                    ip = request.headers.get(key)
                    if ip:
                        # X-Forwarded-For can be a comma-separated list, take the first one
                        myip = ip.split(',')[0].strip()
                        break
                else:
                    myip = request.remote_addr

            # IP address validation (IPv4 and IPv6)
            try:
                ipaddress.ip_address(myip)
            except ValueError:
                return Response('badip', status=400)

            # Simulate update logic
            # In a real implementation, update the DNS record here
            try:
                r = redis.Redis(host=self.db_host, port=self.db_port, db=0)
                r.set(hostname, myip)
            except Exception as e:
                return Response('dnserr', status=500)

            return Response(f'good {myip}', status=200)

        @self.app.route('/records', methods=['GET'])
        def records():
            try:
                r = redis.Redis(host=self.db_host, port=self.db_port, db=0)
                keys = r.keys()
                data = {}
                for key in keys:
                    value = r.get(key)
                    data[key.decode('utf-8')] = value.decode('utf-8') if value else None

                return jsonify(data)
            except Exception as e:
                print(f"Error accessing Redis: {e}")
                return Response('dnserr', status=500)

        @self.app.route('/whoami', methods=['GET'])
        def whoami():
            # Extract client IP from headers or request, similar to /nic/update
            header_keys = [
                'X-Forwarded-For',
                'X-Real-IP',
                'CF-Connecting-IP',
                'Forwarded',
                'Forwarded-For',
                'True-Client-IP',
                'X-Client-IP',
                'X-Cluster-Client-IP',
                'Fastly-Client-Ip',
                'X-Forwarded',
                'X-Forwarded-Host',
                'X-ProxyUser-Ip',
                'X-Original-Forwarded-For',
            ]
            client_ip = None
            for key in header_keys:
                ip = request.headers.get(key)
                if ip:
                    client_ip = ip.split(',')[0].strip()
                    break
            else:
                client_ip = request.remote_addr
            return Response(client_ip, mimetype='text/plain')

    def start_thread(self):
        if self._thread and self._thread.is_alive():
            return  # Already running
        def run():
            self._server_running.set()
            self.app.run(host=self.host, port=self.port, threaded=True, use_reloader=False)
        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop_thread(self):
        # Flask's built-in server does not support programmatic shutdown cleanly
        # This is a placeholder for future extension if using a production server
        self._server_running.clear()
        # No-op: Flask dev server cannot be stopped programmatically
        # Could be implemented with a custom WSGI server
        pass

# used by gunuicorn
app = WebAPIServer().app

# Only run directly if this file is executed as a script
if __name__ == '__main__':
    api = WebAPIServer()
    api.start_thread()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        api.stop_thread()
