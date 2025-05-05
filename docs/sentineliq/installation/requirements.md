# System Requirements

This page details the system requirements for running SentinelIQ in production.

## Hardware Requirements

### Minimum Configuration

* CPU: 4 cores
* RAM: 16GB
* Storage: 100GB
* Network: 1Gbps

### Recommended Configuration

* CPU: 8+ cores
* RAM: 32GB
* Storage: 500GB SSD
* Network: 10Gbps

### High-Performance Configuration

* CPU: 16+ cores
* RAM: 64GB
* Storage: 1TB NVMe SSD
* Network: 10Gbps redundant

## Software Requirements

### Container Runtime

* Docker 20.10 or later
* Docker Compose 2.0 or later

### Programming Language

* Python 3.10 or later

### Additional Tools

* Git
* OpenSSL
* curl or wget

## Operating System Requirements

### Supported Operating Systems

* Ubuntu 20.04 LTS or later
* CentOS 8 or later
* RHEL 8 or later

### System Configuration

* File descriptors: 65535 or higher
* TCP backlog: 65535
* Swap: Disabled or minimal
* SELinux: Permissive or disabled
* System time: Synchronized (NTP)

## Network Requirements

### Ports

* 80/tcp: HTTP (redirects to HTTPS)
* 443/tcp: HTTPS
* 5432/tcp: PostgreSQL (if external)
* 6379/tcp: Redis (if external)
* 9200/tcp: Elasticsearch (if external)

### Firewall Configuration

```bash
# Allow required ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5432/tcp
ufw allow 6379/tcp
ufw allow 9200/tcp
```

## Storage Requirements

### Database Storage

* Type: SSD or NVMe recommended
* IOPS: 3000+ recommended
* Throughput: 100MB/s minimum

### File Storage

* Type: SSD or NVMe recommended
* Capacity: 100GB minimum
* Backup space: 2x primary storage

## Browser Requirements

### Supported Browsers

* Chrome 90+
* Firefox 90+
* Safari 14+
* Edge 90+

### Browser Configuration

* JavaScript: Enabled
* Cookies: Enabled
* Local Storage: Enabled
* Screen Resolution: 1920x1080 minimum

## Additional Requirements

### Email Server

* SMTP server with TLS support
* Valid email account
* Proper DNS configuration

### SSL Certificate

* Valid SSL certificate
* Strong key (2048 bits minimum)
* Modern cipher support

### Backup Storage

* Capacity: 3x primary storage
* Type: Separate physical storage
* Network: Dedicated backup network recommended

## Verification

Run the system verification script:

```bash
docker compose exec web python manage.py check_requirements
```

## Next Steps

1. Follow the [Quick Start Guide](quickstart.md)
2. Configure your [Environment](../configuration/database.md)
3. Set up [Monitoring](../operations/monitoring.md)

## Support

For requirements assistance:

- Email: support@sentineliq.com
- Documentation: [Installation Guide](quickstart.md)
- Community: [GitHub Discussions](https://github.com/sentineliq/sentineliq/discussions) 