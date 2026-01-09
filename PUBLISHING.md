# Publishing Guide: Scott's Claude Code Plugin

Complete step-by-step instructions for publishing your Claude Code plugin to GitHub and making it available for others to install.

## Prerequisites

- [ ] GitHub account
- [ ] Git installed locally
- [ ] Repository renamed to `scott-cc` ✅
- [ ] All configuration files updated ✅

## Step 1: Create GitHub Repository

### 1.1 Create New Repository on GitHub

1. Go to https://github.com/new
2. Fill in the details:
   - **Repository name**: `scott-cc`
   - **Description**: "Scott's personal Claude Code setup with 14 productivity commands and 11 specialized AI agents for modern web development"
   - **Visibility**: Public (so others can install it)
   - **Initialize**: ❌ Don't add README, .gitignore, or license (we already have these)
3. Click "Create repository"

### 1.2 Push Your Local Repository

Once the GitHub repository is created, run these commands:

```bash
cd /path/to/scott-cc

# Add the GitHub remote
git remote add origin https://github.com/citadelgrad/scott-cc.git

# Push your code
git push -u origin main
```

If you encounter authentication issues:
- Use a Personal Access Token instead of password
- Or set up SSH keys (recommended): https://docs.github.com/en/authentication/connecting-to-github-with-ssh

## Step 2: Verify Installation Works

Test that your plugin can be installed:

```bash
# Install from your GitHub repo
/plugin install citadelgrad/scott-cc

# Verify commands are available (note: commands are namespaced)
/scott-cc:code-explain
/scott-cc:feature-plan

# Verify agents are available (they'll activate automatically based on context)
```

To uninstall and test again:
```bash
/plugin uninstall scott-cc
```

## Step 3: Share Your Plugin

Your README already includes your GitHub username, so users can copy-paste commands directly!

### Option A: Share Direct Installation Command

Share this command with others:

```bash
/plugin install citadelgrad/scott-cc
```

### Option B: Submit to Community Marketplaces

#### Claude Code Plugins Marketplace
1. Visit https://claudecodemarketplace.com/
2. Follow their submission guidelines
3. Share your plugin details

#### CC Plugins Curated Marketplace
1. Visit https://github.com/ccplugins/marketplace
2. Fork the repository
3. Add your plugin to their `marketplace.json`
4. Create a Pull Request with this format:

```json
{
  "name": "scott-cc",
  "source": "citadelgrad/scott-cc",
  "description": "Personal Claude Code configuration with 14 productivity commands and 11 specialized AI agents for modern web development",
  "version": "1.0.0",
  "author": "Scott",
  "tags": ["productivity", "python", "nextjs", "supabase", "typescript", "react", "development"]
}
```

#### Claude Code Plugins Plus
1. Visit https://github.com/jeremylongshore/claude-code-plugins-plus
2. Follow their contribution guidelines
3. Submit your plugin details

### Option C: Share on Social Media

Example post:

```
Just published my Claude Code setup as a plugin!

14 slash commands + 11 specialized AI agents for productive web development

Install with:
/plugin install citadelgrad/scott-cc

Features:
- API scaffolding (/api-new)
- Code optimization (/code-optimize)
- Feature planning (/feature-plan)
- Tech research agent
- Architecture agents
- Security & performance agents

Perfect for Next.js, React, TypeScript, and Supabase projects!

GitHub: https://github.com/citadelgrad/scott-cc
```

## Step 5: Maintain Your Plugin

### Updating Your Plugin

When you make changes to your local setup:

```bash
cd /path/to/scott-cc

# Make your changes to commands/ or agents/ directories
# Then commit and push

git add .
git commit -m "Add new command: scott-cc:new-command-name"

# Update version in .claude-plugin/plugin.json
# Bump version: 1.0.0 -> 1.1.0

git add .claude-plugin/plugin.json
git commit -m "Bump version to 1.1.0"

git push
```

Users can update to the latest version:
```bash
/plugin update scott-cc
```

### Versioning Guidelines

- **1.0.x** - Bug fixes and minor tweaks
- **1.x.0** - New commands or agents added
- **x.0.0** - Major restructuring or breaking changes

## Troubleshooting

### Issue: Plugin Won't Install

Check:
- Repository is public on GitHub
- `.claude-plugin/plugin.json` exists in the repo root
- JSON files have valid syntax (no trailing commas, proper quotes)

### Issue: Commands Don't Appear

Check:
- `commands/` directory exists at plugin root (not inside `.claude/`)
- Command files have `.md` extension
- Command files are not empty
- Commands are namespaced (e.g., `/scott-cc:command-name`)

### Issue: Agents Don't Activate

Check:
- `agents/` directory exists at plugin root (not inside `.claude/`)
- Agent files have proper frontmatter with `name` and `description`
- Agents activate based on context, not commands

## Advanced: Creating Releases

For major versions, create GitHub releases:

1. Go to your repo: https://github.com/citadelgrad/scott-cc
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `v1.0.0 - Initial Release`
5. Description: List of features/changes
6. Click "Publish release"

Users can install specific versions:
```bash
/plugin install citadelgrad/scott-cc@v1.0.0
```

## Success Metrics

Track your plugin's success:
- ⭐ GitHub stars
- 👁️ GitHub watchers
- 🍴 GitHub forks
- 💬 Issues and discussions
- 📊 Clone/download counts (GitHub Insights)

## Getting Help

If you run into issues:
- Claude Code Docs: https://docs.claude.com/en/docs/claude-code/plugin-marketplaces
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Community: Search for Claude Code plugins on GitHub

---

**Congratulations!** Once published, your plugin will be available for the Claude Code community to use and learn from. Happy sharing! 🎉
