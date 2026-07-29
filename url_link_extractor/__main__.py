"""CLI 入口模块，支持 python -m url_link_extractor。"""

from .cli import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
