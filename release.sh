#!/bin/bash

# 🚀 Schulmanager Online Release Script
# 
# This script automates the HACS-compatible release process:
# 1. Prompts for new version number
# 2. Updates manifest.json with new version (HACS tracks this)
# 3. Commits and pushes changes with proper tagging
# 4. Creates GitHub release with matching tag (required for HACS)
# 5. HACS will detect the new version from manifest.json + GitHub release
#
# Requirements: gh CLI tool installed and authenticated
# HACS Requirements: version in manifest.json must match GitHub release tag

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists git; then
    print_error "Git is not installed or not in PATH"
    exit 1
fi

if ! command_exists gh; then
    print_error "GitHub CLI (gh) is not installed. Please install it first:"
    echo "  - On Ubuntu/Debian: sudo apt install gh"
    echo "  - On macOS: brew install gh"
    echo "  - Or download from: https://github.com/cli/cli/releases"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status >/dev/null 2>&1; then
    print_error "GitHub CLI is not authenticated. Please run: gh auth login"
    exit 1
fi

print_success "Prerequisites check passed"

# Get current directory and manifest path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_PATH="$SCRIPT_DIR/custom_components/schulmanager_online/manifest.json"

# Check if manifest exists
if [ ! -f "$MANIFEST_PATH" ]; then
    print_error "Manifest file not found: $MANIFEST_PATH"
    exit 1
fi

# Get current version from manifest
CURRENT_VERSION=$(grep '"version"' "$MANIFEST_PATH" | sed -E 's/.*"version": "([^"]+)".*/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    print_error "Could not extract current version from manifest.json"
    exit 1
fi

print_info "Current version: $CURRENT_VERSION"

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Working directory has uncommitted changes:"
    git status --short
    echo
    read -p "Do you want to continue? This will commit all changes. (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Aborted by user"
        exit 0
    fi
fi

# Get the latest commits for release notes
print_info "Getting recent commits for release notes..."
RECENT_COMMITS=$(git log --oneline -10 --pretty=format:"- %s" | head -10)

# Suggest next version (increment patch version)
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

SUGGESTED_PATCH=$((PATCH + 1))
SUGGESTED_MINOR=$((MINOR + 1))
SUGGESTED_MAJOR=$((MAJOR + 1))

echo
print_info "Version suggestions:"
echo "  1) Patch release: $MAJOR.$MINOR.$SUGGESTED_PATCH (bug fixes)"
echo "  2) Minor release: $MAJOR.$SUGGESTED_MINOR.0 (new features)"
echo "  3) Major release: $SUGGESTED_MAJOR.0.0 (breaking changes)"
echo "  4) Custom version"

echo
read -p "Select version type (1-4) or press Enter for patch release: " VERSION_CHOICE

case $VERSION_CHOICE in
    1|"")
        NEW_VERSION="$MAJOR.$MINOR.$SUGGESTED_PATCH"
        RELEASE_TYPE="patch"
        ;;
    2)
        NEW_VERSION="$MAJOR.$SUGGESTED_MINOR.0"
        RELEASE_TYPE="minor"
        ;;
    3)
        NEW_VERSION="$SUGGESTED_MAJOR.0.0"
        RELEASE_TYPE="major"
        ;;
    4)
        read -p "Enter custom version (e.g., 1.2.3): " NEW_VERSION
        RELEASE_TYPE="custom"
        
        # Validate version format
        if [[ ! $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            print_error "Invalid version format. Use semantic versioning (e.g., 1.2.3)"
            exit 1
        fi
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

print_info "Selected version: $NEW_VERSION ($RELEASE_TYPE release)"

# Confirm the release
echo
print_warning "This will:"
echo "  • Update manifest.json version to $NEW_VERSION (HACS tracks this)"
echo "  • Commit all changes with message: 'Release v$NEW_VERSION'"
echo "  • Push to origin with tag v$NEW_VERSION"
echo "  • Create GitHub release with matching tag (required for HACS)"
echo "  • HACS will detect the update from manifest.json version + GitHub release"
echo
read -p "Continue with release? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Release cancelled by user"
    exit 0
fi

# Update manifest.json
print_info "Updating manifest.json..."
sed -i.bak "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$NEW_VERSION\"/" "$MANIFEST_PATH"

# Verify the update
UPDATED_VERSION=$(grep '"version"' "$MANIFEST_PATH" | sed -E 's/.*"version": "([^"]+)".*/\1/')
if [ "$UPDATED_VERSION" != "$NEW_VERSION" ]; then
    print_error "Failed to update manifest.json version"
    # Restore backup
    mv "$MANIFEST_PATH.bak" "$MANIFEST_PATH"
    exit 1
fi

# Remove backup file
rm -f "$MANIFEST_PATH.bak"
print_success "Updated manifest.json: $CURRENT_VERSION → $NEW_VERSION"

# Stage and commit changes
print_info "Committing changes..."
git add .
git commit -m "Release v$NEW_VERSION

Updated version in manifest.json from $CURRENT_VERSION to $NEW_VERSION

Recent changes:
$RECENT_COMMITS"

print_success "Committed changes"

# Push to origin with tags (HACS requires matching tags)
print_info "Pushing to GitHub with tags..."
git push origin main
git push origin "v$NEW_VERSION"

print_success "Pushed to origin with tag v$NEW_VERSION"

# Create GitHub release
print_info "Creating GitHub release..."

# Prepare release notes
RELEASE_NOTES="## 🚀 Release v$NEW_VERSION

### Changes in this release:
$RECENT_COMMITS

### 📦 Installation & Updates
- **HACS**: Update automatically through HACS interface (HACS tracks manifest.json version)
- **Manual**: Download and extract to \`custom_components/schulmanager_online/\`

### 🔧 Upgrade Notes
- Restart Home Assistant after installation
- Check logs for any configuration issues
- HACS users will be automatically notified of this update

### 🎯 HACS Compatibility
This release follows HACS standards:
- ✅ Version in manifest.json: $NEW_VERSION
- ✅ GitHub release tag: v$NEW_VERSION
- ✅ Proper repository structure maintained

---
**Full Changelog**: https://github.com/wunsch/schulmanager-online-hass/compare/v$CURRENT_VERSION...v$NEW_VERSION"

# Create the release
gh release create "v$NEW_VERSION" \
    --title "Release v$NEW_VERSION" \
    --notes "$RELEASE_NOTES" \
    --latest

print_success "Created GitHub release: v$NEW_VERSION"

# Show final status
echo
print_success "🎉 Release completed successfully!"
print_info "Release details:"
echo "  • Version: $CURRENT_VERSION → $NEW_VERSION"
echo "  • Tag: v$NEW_VERSION (matches manifest.json version)"
echo "  • Release URL: https://github.com/wunsch/schulmanager-online-hass/releases/tag/v$NEW_VERSION"
echo "  • HACS Status: Will detect update from manifest.json version + GitHub release"

# Optional: Open release in browser
echo
read -p "Open release page in browser? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh release view "v$NEW_VERSION" --web
fi

print_info "Release process completed! 🚀"
