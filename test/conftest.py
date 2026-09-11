import os
import tempfile
from pathlib import Path

os.environ["DATABASE_PATH"] = str(Path(tempfile.gettempdir()) / "revoralq_pytest.db")
os.environ["RAW_ARCHIVE_PATH"] = str(Path(tempfile.gettempdir()) / "revoralq_raw")
