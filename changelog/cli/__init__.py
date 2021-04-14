from changelog.cli import config
from changelog.cli.main import app

app.add_typer(config.app)

__all__ = ["app"]
