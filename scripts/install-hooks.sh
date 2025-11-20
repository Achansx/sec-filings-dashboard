#!/bin/bash

# SEC Filings Dashboard - Pre-commit Hooks Installation Script
# This script installs and configures pre-commit hooks

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_header "Pre-commit Hooks Installation"

# Step 1: Check Python installation
print_info "Checking Python installation..."

if ! command_exists python3; then
    print_error "Python 3 is not installed!"
    print_info "Please install Python 3.11+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION is installed"

# Step 2: Check pip installation
print_info "Checking pip installation..."

if ! command_exists pip3; then
    print_error "pip3 is not installed!"
    print_info "Please install pip and try again."
    exit 1
fi

print_success "pip is installed"

# Step 3: Install pre-commit
print_info "Installing pre-commit..."

if command_exists pre-commit; then
    print_warning "pre-commit is already installed"
    CURRENT_VERSION=$(pre-commit --version | cut -d' ' -f2)
    print_info "Current version: $CURRENT_VERSION"
else
    pip3 install pre-commit
    print_success "pre-commit installed"
fi

# Step 4: Install pre-commit hooks
print_info "Installing git hooks..."

pre-commit install

print_success "Git hooks installed"

# Step 5: Install commit-msg hook (optional)
print_info "Installing commit-msg hook for conventional commits..."

pre-commit install --hook-type commit-msg || print_warning "commit-msg hook installation skipped"

# Step 6: Run hooks against all files (optional)
print_header "Initial Hook Verification"

print_info "Would you like to run pre-commit hooks against all existing files?"
print_warning "This may take a few minutes and will auto-fix some issues."
echo ""

read -p "Run pre-commit on all files? (y/N): " run_all

if [[ "$run_all" =~ ^[Yy]$ ]]; then
    print_info "Running pre-commit on all files..."
    pre-commit run --all-files || {
        print_warning "Some hooks failed or made changes"
        print_info "This is normal for the first run. Files have been auto-formatted."
        print_info "Review the changes and commit them."
    }
else
    print_info "Skipping initial run. Hooks will run on your next commit."
fi

# Step 7: Summary
print_header "Installation Complete!"

print_success "Pre-commit hooks are now active!"
echo ""
print_info "What happens now:"
echo "  • Hooks will run automatically before each commit"
echo "  • Code will be formatted and checked for issues"
echo "  • Commits will be blocked if critical issues are found"
echo ""
print_info "Manual commands:"
echo "  • Run hooks manually: pre-commit run --all-files"
echo "  • Update hooks: pre-commit autoupdate"
echo "  • Skip hooks (not recommended): git commit --no-verify"
echo ""
print_info "Configured hooks:"
echo "  ✓ Code formatting (Black, isort)"
echo "  ✓ Linting (flake8, mypy)"
echo "  ✓ Security checks (bandit, detect-secrets)"
echo "  ✓ File checks (trailing whitespace, large files, etc.)"
echo "  ✓ YAML/JSON validation"
echo "  ✓ Dockerfile linting (hadolint)"
echo "  ✓ Shell script linting (shellcheck)"
echo ""
print_success "Happy coding!"
