"""Launch worktree code against explicitly selected application data.

Credentials stay outside the repository. Does not perform inference on startup.
"""
import os
from pathlib import Path


def main():
    data = Path(os.environ['AUTONOVEL_APP_DATA_DIR']).resolve()
    config = Path(os.environ['AUTONOVEL_LOCAL_CONFIG']).resolve()
    from dotenv import load_dotenv
    load_dotenv(config, override=False)
    # The separate settings file prevents touching the existing application .env.
    from src import settings
    settings.ENV_FILE = config
    import uvicorn
    uvicorn.run('src.api:app', host='127.0.0.1', port=8000, workers=1)


if __name__ == '__main__':
    main()
