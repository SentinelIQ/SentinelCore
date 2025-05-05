# Downloading SentinelIQ

## Latest Version

The latest stable version of SentinelIQ is **1.0.0** (March 15, 2024).

### Docker Images

```bash
# Pull the latest version
docker pull sentineliq/sentineliq:1.0.0

# Pull the latest development version
docker pull sentineliq/sentineliq:latest
```

### Source Code

```bash
# Clone the repository
git clone https://github.com/sentineliq/sentineliq.git

# Checkout the latest version
cd sentineliq
git checkout v1.0.0
```

## System Requirements

### Hardware Requirements

* CPU: 4+ cores
* RAM: 16GB minimum (32GB recommended)
* Storage: 100GB minimum
* Network: 1Gbps recommended

### Software Requirements

* Docker 20.10 or later
* Docker Compose 2.0 or later
* Python 3.10 or later
* Git

### Operating System Requirements

* Ubuntu 20.04 LTS or later
* CentOS 8 or later
* RHEL 8 or later

## Installation Methods

### 1. Docker Installation (Recommended)

Follow our [Docker Installation Guide](installation/docker.md) for detailed instructions.

### 2. Kubernetes Deployment

Follow our [Kubernetes Deployment Guide](installation/kubernetes.md) for detailed instructions.

### 3. Manual Installation

Follow our [Step-by-Step Installation Guide](installation/step-by-step.md) for detailed instructions.

## Verifying Your Download

### Docker Image Verification

```bash
# Verify image signature
docker trust inspect sentineliq/sentineliq:1.0.0

# Check image digest
docker image inspect sentineliq/sentineliq:1.0.0
```

### Source Code Verification

```bash
# Verify git tag signature
git verify-tag v1.0.0

# Check commit hash
git show v1.0.0
```

## Next Steps

1. Review the [System Requirements](installation/requirements.md)
2. Follow the [Quick Start Guide](installation/quickstart.md)
3. Configure your [Environment](configuration/database.md)
4. Learn about [User Management](administration/users.md)

## Support

For download assistance:

- Email: support@sentineliq.com
- Documentation: [Installation Guide](installation/quickstart.md)
- Community: [GitHub Discussions](https://github.com/sentineliq/sentineliq/discussions) 