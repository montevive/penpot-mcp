#!/bin/bash
# Helper script to install missing linting dependencies

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to create and activate a virtual environment
create_venv() {
    echo -e "${YELLOW}Creating virtual environment in '$1'...${NC}"
    python3 -m venv "$1"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment.${NC}"
        echo "Make sure python3-venv is installed."
        echo "On Ubuntu/Debian: sudo apt install python3-venv"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment created successfully.${NC}"
    
    # Activate the virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source "$1/Scripts/activate"
    else
        # Unix/Linux/MacOS
        source "$1/bin/activate"
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to activate virtual environment.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment activated.${NC}"
    
    # Upgrade pip to avoid issues
    pip install --upgrade pip
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Warning: Could not upgrade pip, but continuing anyway.${NC}"
    fi
}

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}You are not in a virtual environment.${NC}"
    
    # Check if a virtual environment already exists
    if [ -d ".venv" ]; then
        echo "Found existing virtual environment in .venv directory."
        read -p "Would you like to use it? (y/n): " use_existing
        
        if [[ $use_existing == "y" || $use_existing == "Y" ]]; then
            create_venv ".venv"
        else
            read -p "Create a new virtual environment? (y/n): " create_new
            
            if [[ $create_new == "y" || $create_new == "Y" ]]; then
                read -p "Enter path for new virtual environment [.venv]: " venv_path
                venv_path=${venv_path:-.venv}
                create_venv "$venv_path"
            else
                echo -e "${RED}Cannot continue without a virtual environment.${NC}"
                echo "Using system Python is not recommended and may cause permission issues."
                echo "Please run this script again and choose to create a virtual environment."
                exit 1
            fi
        fi
    else
        read -p "Would you like to create a virtual environment? (y/n): " create_new
        
        if [[ $create_new == "y" || $create_new == "Y" ]]; then
            read -p "Enter path for new virtual environment [.venv]: " venv_path
            venv_path=${venv_path:-.venv}
            create_venv "$venv_path"
        else
            echo -e "${RED}Cannot continue without a virtual environment.${NC}"
            echo "Using system Python is not recommended and may cause permission issues."
            echo "Please run this script again and choose to create a virtual environment."
            exit 1
        fi
    fi
else
    echo -e "${GREEN}Using existing virtual environment: $VIRTUAL_ENV${NC}"
fi

# Install development dependencies
echo -e "${YELLOW}Installing linting dependencies...${NC}"
pip install -r requirements-dev.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
fi

echo -e "${GREEN}Dependencies installed successfully.${NC}"

# Install pre-commit hooks
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
pre-commit install

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install pre-commit hooks.${NC}"
    exit 1
fi

echo -e "${GREEN}Pre-commit hooks installed successfully.${NC}"

echo -e "\n${GREEN}Setup completed!${NC}"
echo "You can now run the linting script with:"
echo "  ./lint.py"
echo "Or with auto-fix:"
echo "  ./lint.py --autofix"
echo ""
echo "Remember to activate your virtual environment whenever you open a new terminal:"
echo "  source .venv/bin/activate  # On Linux/macOS"
echo "  .venv\\Scripts\\activate     # On Windows" 