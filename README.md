# NestiqDNS

> **Note:** The majority of the code in this project is AI-generated.

NestiqDNS is a lightweight, self-hosted Dynamic DNS (DDNS) server and API. It provides a DNS server that dynamically updates DNS records via a simple web API, similar to No-IP or DynDNS, and stores records in a lightweight in-memory remote dictionary. This remote dictionary partially follows the Redis protocol, allowing familiar commands, but does not require a real Redis server. NestiqDNS is suitable for home labs, self-hosters, and anyone needing dynamic DNS updates for their domains without the overhead of running Redis.

## Features
- Dynamic DNS server using [dnslib](https://github.com/paulc/dnslib)
- RESTful web API for updating DNS records (compatible with No-IP/ChangeDNS clients)
- Lightweight remote dictionary backend (no actual Redis server required)
- Simple, single-file runner

## Requirements
- Python 3.8+
- No external database required (uses built-in remote dictionary)
- See `requirements.txt` for Python dependencies

## Installation
1. Clone the repository:
   ```powershell
   git clone <repo-url>
   cd NestiqDNS
   ```
2. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set up a `.env` file (optional, defaults provided):
   ```env
   REDIS_HOST="127.0.0.1"
   REDIS_PORT=6379
   DNS_ADDRESS="0.0.0.0"
   DNS_PORT=53
   WEB_ADDRESS="0.0.0.0"
   WEB_PORT=8080
   ```

## Usage
Start the DNS and web API server:
```powershell
python run_all.py
```

- The DNS server listens on the address/port specified in `.env` (default: 0.0.0.0:53).
- The web API listens on the address/port specified in `.env` (default: 0.0.0.0:8080).

## API Endpoints
### Update DNS Record (No-IP compatible)
```
GET/POST /nic/update?hostname=<hostname>&myip=<ip>
```
- Example:
  ```
  curl "http://localhost:8080/nic/update?hostname=example.home&myip=192.168.1.100"
  ```

### List All Records
```
GET /records
```
- Example:
  ```
  curl http://localhost:8080/records
  ```

### Who Am I (Client IP)
```
GET /whoami
```
- Example:
  ```
  curl http://localhost:8080/whoami
  # Response: 192.168.1.50 (your public IP)
  ```

## Running NestiqDNS with Docker and Docker Compose

You can run NestiqDNS easily using Docker or Docker Compose. This is useful for quick deployment, isolation, and running the service on any system that supports Docker.

### Using the Dockerfile

1. Build the Docker image:
   ```shell
   docker build -t nestiqdns .
   ```
2. Run the container:
   ```shell
   docker run -d \
     --name nestiqdns \
     -p 53:53/udp \
     -p 8080:8080 \
     --env-file .env \
     nestiqdns
   ```
   - This will start NestiqDNS with DNS on port 53/udp and the web API on port 8080.
   - You can customize environment variables by editing the `.env` file or passing `-e` flags.

### Using Docker Compose

1. Make sure `docker-compose.yml` is present in your project directory.
2. Start the services:
   ```shell
   docker-compose up -d
   ```
   - This will build and start the NestiqDNS service as defined in `docker-compose.yml`.
   - The service will use the ports and environment variables specified in the compose file.
3. To stop the services:
   ```shell
   docker-compose down
   ```

> **Tip:** You can edit the `docker-compose.yml` file to change port mappings, environment variables, or add volumes for persistent configuration.

## Configuring Inadyn for NestiqDNS

You can use [inadyn](https://github.com/troglobit/inadyn), a popular Dynamic DNS client, to automatically update your DNS records with NestiqDNS.
For more details, see the [inadyn documentation](https://github.com/troglobit/inadyn#configuration).

### Example `inadyn.conf` for NestiqDNS

Below is a sample configuration for `inadyn` to work with NestiqDNS. This setup uses the `custom` provider type, which allows you to specify the endpoints and parameters needed for NestiqDNS compatibility.

```conf
# inadyn.conf example for NestiqDNS
custom NestiqDNS {
  username        = dummy                # Username (not required by default, but must be present)
  password        = dummy                # Password (not required by default, but must be present)
  checkip-server  = 192.168.1.1:8080     # NestiqDNS API address for IP check
  checkip-path    = /whoami              # Path to get your public IP
  checkip-ssl     = false                # Use HTTP (not HTTPS)
  ddns-server     = 192.168.1.1:8080     # NestiqDNS API address for DDNS updates
  ddns-path       = "/nic/update?hostname=%h&myip=%i" # No-IP compatible update endpoint
  ssl             = false                # Use HTTP (not HTTPS)
  hostname        = example.home         # The hostname you want to update
}
```

- Replace `192.168.1.1:8080` with the address and port where your NestiqDNS API is running.
- Replace `example.home` with your desired hostname.
- The username and password fields are required by inadyn but are not used by NestiqDNS unless you enable authentication.
- The `ddns-path` and `checkip-path` are set to match the endpoints provided by NestiqDNS.

This configuration tells inadyn to:
- Use the `/whoami` endpoint to determine your public IP address.
- Use the `/nic/update` endpoint to update your DNS record in NestiqDNS.
- Communicate over HTTP (not HTTPS) by default.

> **Note:** NestiqDNS does not require authentication.

## Using NestiqDNS with AdGuard Home

You can configure AdGuard Home to forward DNS queries for specific domains to your NestiqDNS server. This is useful if you want AdGuard Home to resolve certain hostnames using your self-hosted dynamic DNS records.

### Steps to Forward a Domain to NestiqDNS

1. Open the AdGuard Home web interface (usually at `http://<adguard-ip>:3000`).
2. Go to **Settings** > **DNS settings**.
3. Scroll down to the **Upstream DNS servers** section (the exact name may vary by version).
4. Add a new upstream DNS server in the following format:
    - `[/yourdomain/]IP:PORT`
    - For example, to forward all `.home` domains to your NestiqDNS server at `127.0.0.1:53`, add:
      - `[/home/]127.0.0.1:53`
5. Save the changes.

#### Example
To forward all queries for the `.home` domain to a NestiqDNS server running on the same machine:
- **Upstream DNS server:** `[/home/]127.0.0.1:53`

Now, AdGuard Home will send all DNS queries for `.home` domains to your NestiqDNS instance for resolution.

> **Tip:** Make sure your NestiqDNS server is running and accessible from AdGuard Home. If running on different machines, ensure network/firewall rules allow traffic on the DNS port (default: 53).

## Notes
- No actual Redis server is required; NestiqDNS uses its own in-memory remote dictionary that partially implements the Redis protocol for storage and API compatibility.
- The DNS server must be run with appropriate permissions to bind to port 53 (may require Administrator on Windows).
- For production, consider running behind a reverse proxy and using a production WSGI server for the API.

