---
trigger: always_on
---

Rules

1. **Never hard-code credentials or secrets.**  
   - All keys, passwords, and tokens must be read from environment variables or a secrets manager.

2. **Code must be reproducible and idempotent.**  
   - Environment setup scripts and deployment playbooks must be safe to run multiple times without side effects.

3. **Tests before merge.**  
   - All new code must have unit tests; integration tests must pass in CI before merging.

4. **No hidden dependencies.**  
   - All Python packages must be declared in pyproject.toml or requirements.lock; no “just pip install” instructions.

5. **Adhere to style & type checks.**  
   - Lint with `ruff`, format with `black`, and type-check with `mypy`—the pipeline fails on violations.

6. **Fail fast, log clearly.**  
   - Any unexpected condition should raise explicit exceptions and be logged with structured context.

7. **Graceful degradation.**  
   - Camera or network outages must not crash the service; retry or backoff logic is required.

8. **Hardware abstraction.**  
   - All direct hardware access (camera, GPIO, etc.) must be wrapped in interfaces so code can run with mocks.

9. **Security & privacy first.**  
   - Do not expose internal network credentials in logs or UI; default to secure protocols (TLS for MQTT/S3).

10. **Document everything.**  
    - Each module and public method must have docstrings; major architectural decisions should be captured in the README or an `ARCHITECTURE.md`.

11. **No SSH-only workflow.**  
    - The Raspberry Pi must be deployable via CI/CD or scripted commands; development should not rely on manual SSH edits.

12. **Keep the Pi stable.**  
    - Systemd service must be robust: auto-restart on failure and not leak resources over time.

### Migrations Rules

13. **Migrations must be repeatable and idempotent.**  
    - Running a migration script multiple times should never corrupt or duplicate data.

14. **Version every migration.**  
    - Each migration must have a unique, ordered identifier (e.g., timestamp or sequential number) and live in a dedicated `migrations/` directory in the repo.

15. **Automate migration execution.**  
    - Provide a single command or CI job to run all pending migrations on the Raspberry Pi.  
    - The process must exit with a clear status code and log which migrations ran.

16. **Dry-run capability.**  
    - Every migration must support a dry-run mode that reports intended changes without applying them.

17. **Backup before destructive changes.**  
    - For operations that remove or rewrite data (e.g., reorganizing S3 folders), require an automated backup or snapshot step and document how to roll back.

18. **Migration logging.**  
    - Log start time, end time, and results of each migration; store logs in a persistent location so they survive service restarts.

19. **No manual, undocumented steps.**  
    - Migrations must never rely on manual editing of files or ad-hoc commands. All steps must be in version control.

20. **Backward compatibility where possible.**  
    - If a new deployment fails mid-migration, the system should continue to operate with the old schema or gracefully roll back.