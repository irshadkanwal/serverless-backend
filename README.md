# CoachBot Serverless Backend

## Overview
CoachBot is a state machine-based coaching system that delivers structured, professional coaching conversations. The system uses a Finite State Machine (FSM) architecture to manage conversation flow through distinct coaching stages.

## Key Features
- Stage-aware response generation
- Professional coaching standards compliance
- Extensible architecture for future enhancements
- Clear separation of concerns between analysis and coaching

## Running Locally

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 16 with pgvector and AGE extensions (for graph and vector storage)
- GitHub CLI (for PM workflow and issue management)

### Setup
1. Clone the repository
   ```bash
   git clone <repository-url>
   cd serverless-backend
   ```

2. Install GitHub CLI and required extensions
   ```bash
   # Install GitHub CLI (if not already installed)
   # macOS
   brew install gh

   # Linux (Debian/Ubuntu)
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh

   # Authenticate with GitHub
   gh auth login

   # Install required extensions
   gh extensions install yahsan2/gh-sub-issue
   ```

3. Install dependencies using uv
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv sync

   # Activate the virtual environment
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Environment Variables
   Create a `.env` file in the root directory with the following variables:
   ```
   AZURE_API_KEY='project-api-key'
   AZURE_API_ENDPOINT='project-api-endpoint'
   AZURE_API_VESION='2025-03-01-preview'
   DATABASE_URL=postgresql://username:password@localhost:5432/dbname
   ```

5. Database Setup
   ```
   # Run the PostgreSQL container with pgvector and AGE extensions
   cd ci-cd/db
   ./build-deploy.sh
   ```

### Running the API

**Using uv (recommended):**
```bash
# Run with FastAPI CLI (built into fastapi[standard])
uv run fastapi run app/main.py --host 0.0.0.0 --port 8000

# For development with auto-reload
uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Development Commands

**With uv:**
```bash
# Install new dependency
uv add <package-name>

# Install dev dependency
uv add --dev <package-name>

# Update dependencies
uv sync

# Run linting
uv run ruff check app/

# Fix linting issues
uv run ruff check app/ --fix
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency. The hooks are configured to run:
- **ruff linter**: Checks for code quality issues and style violations
- **ruff formatter**: Automatically formats code to maintain consistent style

**Manual hook execution:**
```bash
# Run hooks on staged files
uv run pre-commit run

# Run hooks on all files
uv run pre-commit run --all-files

# Update hook versions
uv run pre-commit autoupdate
```

## Development with Docker
For development with Docker, use:
```
cd ci-cd
docker-compose up
```

## Development Workflow - Trunk-Based Development

This repository follows a **trunk-based development** workflow for simplified collaboration and continuous delivery.

### Core Principles
- **Production-ready main branch**: The `main` branch must ALWAYS be in a deployable state - every commit should be production-ready
- **Single source of truth**: All development flows through the `main` branch
- **Short-lived feature branches**: Feature branches should be merged within 1-2 days maximum
- **Continuous integration**: Every push to `main` triggers automatic deployment to the development environment
- **Release-driven production deployments**: Production deployments are triggered by creating GitHub releases
- **Feature flags over branches**: Use feature flags to control environment-specific features or incomplete work

### Development Standards

#### Creating Feature Branches
```bash
# Always create feature branches from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make your changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push -u origin feature/your-feature-name
```

#### Branch Naming Convention
- `feature/` - New features
- `fix/` - Bug fixes
- `chore/` - Maintenance tasks
- `docs/` - Documentation updates

#### Pull Request Guidelines
- PRs should be small and focused (ideally < 500 lines)
- Must pass all CI checks before merging
- Require at least one code review
- Code must be production-ready before merging (use feature flags if needed)
- Merge to `main` as soon as review is complete
- Delete feature branches after merging

### Deployment Process

#### Development Environment
- **Automatic**: Every merge to `main` automatically deploys to the dev environment
- **Endpoint**: `dev-api.coachbot.ai`
- **Purpose**: Integration testing and feature validation

#### Production Deployment

To deploy to production:

1. **Create a GitHub Release** (via GitHub UI):
   - Go to your repository on GitHub
   - Click on "Releases" in the right sidebar
   - Click "Draft a new release"
   - Click "Choose a tag" → Enter a new version tag (e.g., `v1.0.0`)
   - Select "Create new tag on publish"
   - Target should be `main` branch
   - Add a release title (e.g., "Release v1.0.0")
   - Add release notes describing changes
   - Click "Publish release"
   - This automatically triggers production deployment

2. **Production endpoint**: `api.coachbot.ai`

### Hotfix Process

For critical production issues:

1. **Create hotfix from main**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-fix
   ```

2. **Make the fix**:
   ```bash
   # Fix the issue
   git add .
   git commit -m "hotfix: fix critical production issue"
   git push -u origin hotfix/critical-fix
   ```

3. **Fast-track PR**:
   - Create PR with `hotfix` label
   - Get expedited review
   - Merge to `main` immediately after approval

4. **Create patch release** (via GitHub UI):
   - Go to GitHub → Releases → "Draft a new release"
   - Click "Choose a tag" → Enter patch version (e.g., `v1.0.1`)
   - Select "Create new tag on publish"
   - Target: `main` branch
   - Title: "Hotfix v1.0.1"
   - Describe the critical fix in release notes
   - Click "Publish release" to trigger production deployment

### Rollback Process

If a production deployment causes issues:

1. **Quick rollback via GitHub Release**:
   - Go to GitHub → Releases
   - Click "Draft a new release"
   - Click "Choose a tag" → Select the last known good tag (e.g., `v1.0.0`)
   - Target: The existing tag (not main)
   - Title: "Rollback to v1.0.0"
   - Add notes explaining the rollback reason
   - Click "Publish release"
   - This will redeploy the previous stable version

2. **Or revert and release**:
   ```bash
   # Revert the problematic commit
   git checkout main
   git pull origin main
   git revert <commit-hash>
   git push origin main
   ```
   Then create a new release via GitHub UI with an incremented version

### CI/CD Pipeline

| Environment | Trigger | Branch/Event | URL |
|------------|---------|--------------|-----|
| Development | Push | `main` | `dev-api.coachbot.ai` |
| Production | GitHub Release | Release published | `api.coachbot.ai` |

## Project Management with Claude Code

This project includes integrated project management commands through Claude Code's `/pm` commands. These tools help manage features from requirements through implementation using a structured workflow.

### Context Management for Better Quality

To ensure Claude Code provides the most accurate and relevant assistance:

**Start each session with:**
```bash
/context:prime
```
This loads the complete project context including dependencies, standards, and recent changes.

**Update context regularly:**
```bash
/context:update
```
Run this command:
- After pulling new changes from git
- After switching branches
- After significant code modifications
- When Claude seems to lack recent context

**Why this matters:**
- Ensures Claude has up-to-date project understanding
- Improves code suggestions and architectural decisions
- Maintains awareness of recent changes and dependencies
- Reduces errors from outdated context

### PM Workflow Overview

The PM workflow follows this sequence:
1. **Requirements** → Create and review Product Requirements Document (PRD)
2. **Planning** → Parse PRD into technical epic with implementation plan
3. **Decomposition** → Break epic into specific GitHub issues
4. **Synchronization** → Create GitHub issues for team collaboration
5. **Implementation** → Work on issues with automatic branch management
6. **Completion** → Close issues and update project state

### Step-by-Step PM Workflow

#### 1. Create Product Requirements Document
```bash
# Create a new PRD for your feature
/pm:prd-new FEATURE-NAME

# Review and edit the generated PRD until satisfied
# The PRD will be created in .claude/prds/FEATURE-NAME.md
```

**Next steps:**
- Review the generated PRD thoroughly
- Edit the document to match your requirements
- Commit the PRD to a feature branch and open a PR
- **Important**: Only PRDs are committed to the repository - all other PM state remains local

#### 2. Parse PRD into Technical Epic
```bash
# After PRD branch is merged, create technical implementation plan
/pm:prd-parse FEATURE-NAME

# This creates a technical epic in .claude/epics/FEATURE-NAME/
# Review the epic overview locally - it won't be committed
```

#### 3. Decompose Epic into Issues
```bash
# Break the epic into specific, actionable GitHub issues
/pm:epic-decompose FEATURE-NAME

# This creates individual issue files in .claude/epics/FEATURE-NAME/issues/
# Each issue includes acceptance criteria and implementation guidance
```

#### 4. Sync Issues to GitHub
```bash
# Create GitHub issues for team review and context
/pm:epic-sync

# This creates actual GitHub issues that the team can review, comment on, and assign
# Issues are linked to the local PM state for tracking
```

#### 5. Start Working on Issues
```bash
# Begin implementation of a specific issue with analysis
/pm:issue-start ISSUE-NUMBER --analyze

# This will:
# - Analyze the issue requirements and codebase context
# - Create or switch to an appropriate feature branch
# - Provide implementation guidance
```

**Implementation workflow:**
- Make your changes following the analysis guidance
- Commit changes to the feature branch
- Open a PR when the issue is complete

#### 6. Stacked Development (Optional)
For complex features requiring multiple related issues:

```bash
# After completing one issue, branch from current feature branch
git checkout -b feature/FEATURE-NAME-issue-2

# Continue with next issue
/pm:issue-start NEXT-ISSUE-NUMBER --analyze

# Create stacked PRs and rebase when previous PRs merge
```

#### 7. Close Completed Issues
```bash
# After PR is merged, close the GitHub issue and update local state
/pm:issue-close ISSUE-NUMBER

# This updates both GitHub and local PM tracking
```

### PM Command Reference

| Command | Purpose |
|---------|---------|
| `/pm:prd-new NAME` | Create new Product Requirements Document |
| `/pm:prd-parse NAME` | Convert PRD to technical epic |
| `/pm:epic-decompose NAME` | Break epic into GitHub issues |
| `/pm:epic-sync` | Sync issues to GitHub |
| `/pm:issue-start NUM --analyze` | Start working on an issue |
| `/pm:issue-close NUM` | Close issue and update state |
| `/pm:status` | Show current PM status |
| `/pm:epic-status` | Show epic progress |

### Important Notes

- **Repository commits**: Only PRDs in `.claude/prds/` are committed to the repository
- **Local state**: All epic and issue tracking in `.claude/epics/` remains local to your machine
- **GitHub integration**: Issues are created and managed through GitHub API for team collaboration
- **Branch management**: PM commands automatically handle feature branch creation and switching

### Best Practices

#### Maintaining Production-Ready Main
- **Never break main**: Every commit to `main` must be deployable to production at any time
- **Test before merging**: Run all tests locally and ensure CI passes
- **No partial features**: If a feature isn't complete, wrap it in a feature flag rather than leaving it broken
- **Immediate fixes**: If `main` breaks, fixing it is the team's #1 priority

#### Additional Best Practices
- **Small, frequent commits**: Make integration easier and reduce merge conflicts
- **Automated testing**: Ensure comprehensive test coverage before merging
- **Monitor deployments**: Check deployment status after merging to `main`
- **Communicate breaks**: If you must merge something risky, communicate with the team
- **Rollback readiness**: Always be prepared to rollback quickly if issues arise
