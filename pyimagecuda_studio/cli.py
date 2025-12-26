import sys
import argparse
from PySide6.QtWidgets import QApplication

from .gui.main_window import MainWindow
from . import VERSION_VERBOSE


def main():
    """
    Main entry point for the CLI command
    This function is called when you run:
    - pyimagecuda-studio
    - pics
    - python -m pyimagecuda_studio
    """
    parser = argparse.ArgumentParser(
        prog='pyimagecuda-studio',
        description='Node-based image processing powered by CUDA'
    )
    
    parser.add_argument('--version', '-v', action='store_true', help='Show version')
    
    args = parser.parse_args()
    
    if args.version:
        print(VERSION_VERBOSE)
        return 0
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())