import sys
from src.cli import main

if __name__ == "__main__":
    sys.argv.insert(1, "generate-report")
    main()
