# backends/remote_client_backend.py
from __future__ import annotations
import base64, requests, os, io, zipfile
from typing import Optional, Iterable, Dict, Any, Union, List

from arduino_colab_kernel.backends.protocol import Backend
from arduino_colab_kernel.board.board import Board

class RemoteBackend(Backend):
    """
    HTTP client backend – serializes Board via board.export() and calls the remote server.

    Attributes:
        remote_url (str): Base URL of the remote server.
        session (requests.Session): HTTP session with authentication.
    """
    def __init__(self, remote_url: str, token: str):
        """
        Initializes the RemoteBackend.

        Args:
            remote_url (str): Base URL of the remote server.
            token (str): Authentication token for the server.

        Raises:
            Exception: If session initialization fails.
        """
        self.remote_url = remote_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": token})

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a POST request to the remote server.

        Args:
            path (str): API endpoint path.
            payload (Dict[str, Any]): JSON payload to send.

        Returns:
            Dict[str, Any]: JSON response from the server.

        Raises:
            requests.RequestException: If the request fails.
            Exception: If the response is not valid JSON.
        """
        try:
            r = self.session.post(f"{self.remote_url}{path}", json=payload, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise RuntimeError(f"Remote POST to {path} failed: {e}")

    def _zip_directory(self, dir_path: str) -> bytes:
        """
        Zips the contents of a directory into a bytes object.

        Args:
            dir_path (str): Path to the directory.

        Returns:
            bytes: The zipped directory as bytes.

        Raises:
            Exception: If zipping fails.
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, dir_path)
                    zf.write(abs_path, rel_path)
        return buf.getvalue()

    def _prepare_sketch_payload(self, sketch_source: str) -> Dict[str, str]:
        """
        Prepares the sketch payload for remote POST. Zips and base64-encodes if directory.

        Args:
            sketch_source (str): Path to the sketch directory or .ino file.

        Returns:
            Dict[str, str]: Payload with either 'sketch_b64' or 'sketch_zip_b64'.

        Raises:
            FileNotFoundError: If the path does not exist.
            Exception: If zipping or encoding fails.
        """
        if not os.path.exists(sketch_source):
            raise FileNotFoundError(f"Sketch source '{sketch_source}' does not exist.")
        if os.path.isdir(sketch_source):
            # Zip the directory and base64 encode
            zipped = self._zip_directory(sketch_source)
            return {"sketch_zip_b64": base64.b64encode(zipped).decode("ascii")}
        elif os.path.isfile(sketch_source):
            # Read the file and base64 encode
            with open(sketch_source, "rb") as f:
                content = f.read()
            return {"sketch_b64": base64.b64encode(content).decode("ascii")}
        else:
            raise RuntimeError(f"Invalid sketch source: {sketch_source}")

    def compile(self, board: Board, sketch_source: str,
                extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        """
        Compiles the sketch on the remote server.

        Args:
            board (Board): Board configuration.
            sketch_source (str): Path to the sketch directory or .ino file.
            extra_args (Optional[Iterable[str]]): Additional CLI arguments.

        Returns:
            Dict[str, Any]: Compilation result from the server.

        Raises:
            Exception: If the remote call fails or sketch_source is invalid.
        """
        try:
            payload = {
                "board": board.export(),
                "extra_args": list(extra_args) if extra_args else []
            }
            payload.update(self._prepare_sketch_payload(sketch_source))
            return self._post("/compile", payload)
        except Exception as e:
            raise RuntimeError(f"Remote compile failed: {e}")

    def upload(self, board: Board, sketch_source: str,
               extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        """
        Uploads the sketch to the board via the remote server.

        Args:
            board (Board): Board configuration.
            sketch_source (str): Path to the sketch directory or .ino file.
            extra_args (Optional[Iterable[str]]): Additional CLI arguments.

        Returns:
            Dict[str, Any]: Upload result from the server.

        Raises:
            Exception: If the remote call fails or sketch_source is invalid.
        """
        try:
            payload = {
                "board": board.export(),
                "extra_args": list(extra_args) if extra_args else []
            }
            payload.update(self._prepare_sketch_payload(sketch_source))
            return self._post("/upload", payload)
        except Exception as e:
            raise RuntimeError(f"Remote upload failed: {e}")

    def open_serial(self, board: Board) -> None:
        """
        Opens the serial port on the remote server.

        Args:
            board (Board): Board configuration.

        Raises:
            Exception: If the remote call fails.
        """
        try:
            self._post("/serial/open", {"board": board.export()})
        except Exception as e:
            raise RuntimeError(f"Remote open_serial failed: {e}")

    def close_serial(self, board: Board) -> None:
        """
        Closes the serial port on the remote server.

        Args:
            board (Board): Board configuration.

        Raises:
            Exception: If the remote call fails.
        """
        try:
            self._post("/serial/close", {"board": board.export()})
        except Exception as e:
            raise RuntimeError(f"Remote close_serial failed: {e}")

    def read_serial(self, board: Board, size: int = -1) -> bytes:
        """
        Reads bytes from the serial port on the remote server.

        Args:
            board (Board): Board configuration.
            size (int): Number of bytes to read (-1 for all available).

        Returns:
            bytes: Bytes read from the serial port.

        Raises:
            Exception: If the remote call fails or decoding fails.
        """
        try:
            data = self._post("/serial/read", {"board": board.export(), "size": size})
            b64 = data.get("data_b64") or ""
            return base64.b64decode(b64.encode("ascii")) if b64 else b""
        except Exception as e:
            raise RuntimeError(f"Remote read_serial failed: {e}")
    
    def readlines_serial(self, board: Board, size: int = 1) -> List[str]:
        """
        Reads lines from the serial port on the remote server.

        Args:
            board (Board): Board configuration.
            size (int): Number of lines to read.

        Returns:
            List[str]: List of lines read.

        Raises:
            Exception: If the remote call fails.
        """
        try:
            data = self._post("/serial/readlines", {"board": board.export(), "size": size})
            lines = data.get("lines") or []
            return list(lines) if isinstance(lines, list) else []
        except Exception as e:
            raise RuntimeError(f"Remote readlines_serial failed: {e}")

    def write_serial(self, board: Board, data: Union[bytes, str], append_newline: bool = True) -> int:
        """
        Writes data to the serial port on the remote server.

        Args:
            board (Board): Board configuration.
            data (Union[bytes, str]): Data to write.
            append_newline (bool): Whether to append a newline.

        Returns:
            int: Number of bytes written.

        Raises:
            Exception: If the remote call fails.
        """
        try:
            if isinstance(data, str):
                b64 = base64.b64encode(data.encode("utf-8")).decode("ascii")
            else:
                b64 = base64.b64encode(data).decode("ascii")
            out = self._post("/serial/write", {"board": board.export(), "data_b64": b64, "append_newline": append_newline})
            return int(out.get("written", 0))
        except Exception as e:
            raise RuntimeError(f"Remote write_serial failed: {e}")
