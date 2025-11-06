"""Package management utilities."""
import sys
import subprocess
from importlib.metadata import version, PackageNotFoundError

REQUIRED_PACKAGES = {
    'moviepy': 'moviepy',
    'PyQt6': 'PyQt6',
    'librosa': 'librosa',
    'Pillow': 'Pillow'
}

def check_package(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        version(package_name)
        return True
    except PackageNotFoundError:
        return False

def install_package(package_name: str) -> bool:
    """Install a package using pip."""
    try:
        subprocess.check_call([
            sys.executable, 
            '-m', 
            'pip', 
            'install', 
            package_name
        ])
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install_dependencies() -> bool:
    """Check and install all required packages."""
    missing_packages = []
    
    # Check all required packages
    for package_name in REQUIRED_PACKAGES:
        if not check_package(package_name):
            missing_packages.append(REQUIRED_PACKAGES[package_name])
    
    if not missing_packages:
        return True
    
    print("\nInstalling missing dependencies...")
    success = True
    
    # Install missing packages
    for package in missing_packages:
        print(f"Installing {package}...")
        if not install_package(package):
            print(f"Failed to install {package}")
            success = False
    
    return success