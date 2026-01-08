# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-01-08

### Added
- **Governance Module**: Implemented `ApprovalQueue` and `PromotionProtocol` for human-in-the-loop agent operations.
- **Scheduler Module**: Added `JobManager` and `recurring_task` tool for scheduled agent activities.
- **MemoryPro**: Enhanced memory system with `Prioritizer` (tiers 1-5) and `Fading` (time-based decay) algorithms.
- **Middleware Pipeline**: Introduced `EnhancedPipeline` for customizable request processing (Routing -> Validation -> TokenTracking -> Execution).
- **Token Budgeting**: A comprehensive accounting system with `TokenBudgetManager` and rigorous `CostEstimator` for OpenAI/Anthropic models.
- **SaaS Server**: Restored and improved the FastAPI server with Lovable-compatible JWT authentication.
- **Deployment**: Added production-ready `Dockerfile` and Google Cloud Platform deployment scripts (`deploy_gcp.sh`).

### Changed
- **BaseAgent**: Refactored `chat()` to use dynamic handler injection via the middleware pipeline.
- **Project Structure**: Organized `langswarm-pro` as a proprietary internal package alongside the open-core.
- **Documentation**: Migrated and updated all developer guides to the main documentation site.
- **Branding**: Unified nomenclature to "LangSwarm" (removed "V2" distinction).

### Fixed
- **Pipeline Integration**: Resolved issues with dynamic routing and token tracking in `BaseAgent`.
- **Dependency Management**: Cleaned up conflicting dependencies in `pyproject.toml`.
