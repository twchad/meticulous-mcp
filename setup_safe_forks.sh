#!/bin/bash
# Setup script for safe fork workflow
# This script will:
# 1. Rename existing 'origin' to 'upstream' 
# 2. Set push URL to prevent accidental pushes to upstream
# 3. Optionally add your fork as 'origin' if you have one

set -e

echo "🔧 Setting up safe fork workflow..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

setup_repo() {
    local repo_dir=$1
    local repo_name=$2
    
    if [ ! -d "$repo_dir/.git" ]; then
        echo -e "${YELLOW}⚠️  $repo_name is not a git repo, skipping...${NC}"
        return
    fi
    
    cd "$repo_dir"
    
    echo -e "\n${GREEN}📦 Setting up $repo_name${NC}"
    
    # Check if origin exists
    if git remote get-url origin >/dev/null 2>&1; then
        ORIGIN_URL=$(git remote get-url origin)
        echo "  Current origin: $ORIGIN_URL"
        
        # Check if it's already renamed to upstream
        if git remote get-url upstream >/dev/null 2>&1; then
            echo -e "  ${GREEN}✅ Upstream already configured${NC}"
        else
            # Rename origin to upstream
            echo "  🔄 Renaming 'origin' to 'upstream'..."
            git remote rename origin upstream
            
            # Set push URL to prevent accidental pushes (using a no-op URL)
            echo "  🔒 Setting push URL to prevent accidental pushes..."
            git remote set-url --push upstream "no_push_configured"
            
            echo -e "  ${GREEN}✅ Protected: pushes to upstream will fail${NC}"
        fi
        
        # Check if user has a fork (you can customize this)
        echo -e "\n  ${YELLOW}💡 To add your fork as 'origin', run:${NC}"
        echo "     git remote add origin https://github.com/YOUR_USERNAME/$repo_name.git"
        echo "     git remote set-url --push origin https://github.com/YOUR_USERNAME/$repo_name.git"
    else
        echo -e "  ${YELLOW}⚠️  No origin remote found${NC}"
    fi
    
    cd ..
}

# Setup each repo
setup_repo "espresso-profile-schema" "espresso-profile-schema"
setup_repo "pyMeticulous" "pyMeticulous"
setup_repo "python-sdk" "python-sdk"

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\n${YELLOW}📝 Next steps:${NC}"
echo "1. Create forks on GitHub for each repo (if you haven't already)"
echo "2. Add your forks as 'origin' remote:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
echo "3. Set push URL:"
echo "   git remote set-url --push origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
echo -e "\n${GREEN}🔒 Safety: Pushes to upstream will now fail with 'no_push_configured'${NC}"

