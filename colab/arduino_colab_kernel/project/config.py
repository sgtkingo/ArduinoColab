import os

# Local path to arduino-cli (can be in PATH or in the package)
ARDUINO_CLI_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "arduino-cli.exe")
)

LOCAL_MODE = "local"  # local mode (default)
REMOTE_MODE = "remote"  # remote mode (e.g. for cloud IDEs)

DEFAULT_REMOTE_HOST = "localhost"  # default remote server host (for REMOTE_MODE)
DEFAULT_REMOTE_PORT = 5000  # default remote server port (for REMOTE_MODE)
DEFAULT_REMOTE_URL = f"http://{DEFAULT_REMOTE_HOST}:{DEFAULT_REMOTE_PORT}"  # default remote server URL (for REMOTE_MODE)

DEFAULT_PROJECT_NAME = "sketch"
DEFAULT_PROJECTS_DIR = "./projects"
DEFAULT_LOGS_DIR = "logs"

DEFAULT_SERIAL_CONFIG = {
    "baudrate": 115200,
    "timeout": 0.1,
    "encoding": "utf-8",
    "autostrip": True,
}