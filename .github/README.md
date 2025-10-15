# GitHub Actions Workflows

## build-executables.yml

Automatically builds executables for Windows, macOS, and Linux whenever you push code or create a release tag.

### What it Does

1. **On every push to main/master:**
   - Builds executables for all three platforms
   - Makes them available as downloadable artifacts (kept for 30 days)

2. **On version tags (v*.*):**
   - Builds executables for all three platforms
   - Creates a GitHub Release
   - Attaches the executables as downloadable ZIP files
   - Adds release notes automatically

### How to Use

#### Get Artifacts from a Build

1. Go to the "Actions" tab in your GitHub repo
2. Click on a completed workflow run
3. Scroll down to "Artifacts"
4. Download:
   - `DXF2Laser-Windows.zip`
   - `DXF2Laser-macOS.zip`
   - `DXF2Laser-Linux.zip`

#### Create a Release

```bash
# Tag your version
git tag v1.0.0 -m "First release"
git push origin v1.0.0
```

This will:
- Trigger the build workflow
- Build for all platforms
- Create a release on the "Releases" page
- Users can download the executables directly

#### Manual Trigger

1. Go to Actions tab
2. Click "Build Executables"
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow" button

### Build Time

- Windows: ~8-10 minutes
- macOS: ~8-10 minutes
- Linux: ~8-10 minutes
- Total: ~10-12 minutes (runs in parallel)

### Cost

**FREE** for public repositories with unlimited minutes.

For private repositories:
- 2,000 minutes/month free
- ~30 minutes per complete build (all platforms)
- ~66 builds per month for free

### Troubleshooting

#### Build Fails

Check the logs:
1. Go to Actions tab
2. Click the failed workflow
3. Click the failed job
4. Read error messages

Common issues:
- Missing dependencies in `requirements.txt`
- Syntax error in spec files
- Missing logo.png file

#### No Artifacts

- Wait for build to complete (green checkmark)
- Artifacts expire after 30 days
- Check you're on the right workflow run

#### Release Not Created

- Only created on tags starting with 'v'
- Check tag exists: `git tag`
- Check tag was pushed: `git ls-remote --tags origin`

### Versioning

Follow semantic versioning:

```bash
# Bug fixes: 1.0.0 -> 1.0.1
git tag v1.0.1 -m "Fix coordinate bug"

# New features: 1.0.1 -> 1.1.0
git tag v1.1.0 -m "Add arc support"

# Breaking changes: 1.1.0 -> 2.0.0
git tag v2.0.0 -m "New UI"

# Push all tags
git push origin --tags
```

### Customizing

To modify the workflow, edit `build-executables.yml`:

- Change Python version: Update `python-version: '3.11'`
- Add dependencies: Update before build steps
- Change retention: Update `retention-days: 30`
- Modify release notes: Update `body:` section

### Status Badge

Add to your README:

```markdown
![Build Status](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build-executables.yml/badge.svg)
```

Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub username and repository name.

