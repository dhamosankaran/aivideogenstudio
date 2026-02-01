# ISSUE-004: Startup Automation

**ID**: ISSUE-2026-01-19-004  
**Type**: DevOps  
**Priority**: P0-Critical  
**Status**: Planned  
**Created**: 2026-01-19  
**Effort**: 1 hour

## Summary
Create scripts to start/stop the entire application with a single command.

## Context
Currently requires manual steps: activate venv, start backend, start frontend in separate terminals. This is error-prone and slows development.

## Acceptance Criteria
- [ ] `./start.sh` starts both backend and frontend
- [ ] `./stop.sh` gracefully shuts down both services
- [ ] Health check loop (wait for backend before starting frontend)
- [ ] Logs output to `logs/startup.log`
- [ ] Works on macOS (primary platform)
- [ ] README updated with single-command instructions

## Implementation Notes
- Use bash script with background processes
- Store PIDs in `.pids/` directory
- Trap SIGINT/SIGTERM for graceful shutdown
- Check if ports 8000/5173 are already in use

## Dependencies
- None

## Next Action
**Status**: Ready for implementation
