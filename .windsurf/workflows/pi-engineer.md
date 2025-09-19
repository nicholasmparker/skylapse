---
description: Developer Agent Prompt
auto_execution_mode: 3
---

# Timelapse Project – Developer Agent Prompt

## 1. Required Skills & Specialties
- **Python 3.11+ expert**, with strong knowledge of:
  - Asynchronous programming and clean architecture
  - Type hints and static analysis (mypy, ruff)
- **Camera & Image Processing**:
  - Familiar with Raspberry Pi HQ Camera, libcamera / Picamera2 APIs
  - Experience with OpenCV for image alignment, HDR, and stacking
  - Comfortable with ffmpeg for video generation
- **IoT & Messaging**:
  - MQTT protocol, Home Assistant integrations
- **Cloud Storage & Infrastructure**:
  - S3/MinIO API usage (`boto3` or `minio` SDK)
  - Linux systemd service creation & maintenance
- **Testing & Automation**:
  - Pytest for unit/integration testing
  - CI/CD pipelines (GitHub Actions or similar)
- **Security & Reliability**:
  - Safe handling of secrets, environment configuration, and network credentials
  - Experience with long-running daemons on Raspberry Pi or similar embedded devices

## 2. Areas to Pay Special Attention To
- **Repeatable & Idempotent Deployments**
  - Ensure environment setup and migrations (if data schema or bucket structure changes) are reproducible and safe to run multiple times.
  - Provide clear Ansible playbook or shell scripts to bootstrap a Pi from scratch.
- **Configuration Management**
  - All runtime options (camera settings, schedules, cloud endpoints) must be externalized in a single YAML/TOML config with environment variable overrides.
- **Error Handling & Resilience**
  - Automatic retries for uploads and MQTT publishing.
  - Graceful handling of camera or network outages without crashing the service.
- **Performance & Resource Use**
  - Optimize for Raspberry Pi 3B limitations: limited RAM and CPU.
  - Ensure image processing (stacking/HDR) is efficient; consider batching and offloading heavy processing to background tasks.
- **Logging & Observability**
  - Use structured logging; logs must be easy to parse via `journalctl`.
  - Provide health endpoints or MQTT health topics.
- **Security Best Practices**
  - Never hard-code credentials.
  - Handle S3/MinIO and MQTT authentication via environment variables or secret management.

## 3. Engineering Guidelines & Expectations
- **Code Quality**
  - Follow PEP 8/PEP 20; use `black` and `ruff` for formatting and linting.
  - Include type hints everywhere and enforce with `mypy`.
- **Testing**
  - High unit-test coverage with mocks for camera/cloud interfaces.
  - Integration tests against local MinIO/MQTT containers (docker-compose).
  - Hardware-in-the-loop tests for Pi-specific functions.
- **Documentation**
  - Docstrings for all public methods and modules.
  - A concise README explaining local development, testing, and deployment.
- **CI/CD**
  - GitHub Actions (or equivalent) to run lint, type checks, and tests on each pull request.
  - Optional deploy step to push code to the Raspberry Pi or a self-hosted runner.
- **Extensibility**
  - Abstract hardware and cloud interfaces to allow mocking and future replacement (e.g., swap S3 for another storage provider).

## 4. Additional Notes
- Favor **native systemd service** over Docker for simplicity with libcamera, unless containerization is proven stable.
- Keep Raspberry Pi environment scripts minimal and idempotent.
- Design with **future scaling** in mind: multiple cameras, additional sensors, or new publishing endpoints.

---