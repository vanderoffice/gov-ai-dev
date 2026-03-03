# Contributing to gov-ai-dev

## About
Multi-agent AI systems for California government citizen services. Powers BizBot, CommentBot, KiddoBot, WiseBot, and WaterBot.

## ⚠️ Production Systems
This repo contains LIVE production bots. Please:
- Test changes thoroughly before submitting PRs
- Never modify workflow files without coordination
- Document any changes to bot behavior

## Reporting Issues
- Use GitHub Issues for bugs and feature requests
- Include bot name, error messages, and reproduction steps
- Mark security issues as confidential

## Pull Requests
1. Fork the repository
2. Create a feature branch from `main`
3. Make changes with clear commit messages
4. Test locally with sample data
5. Submit PR against `main` branch

## Development Setup
1. Clone the repo
2. Set up Python virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Copy environment template and add credentials
5. Run tests: `pytest`

## Bot Structure
Each bot has:
- `/bots/{bot_name}/` - Bot-specific code
- Shared utilities in `/shared/`
- n8n workflow integrations

## Questions?
Open a GitHub Issue or Discussion.