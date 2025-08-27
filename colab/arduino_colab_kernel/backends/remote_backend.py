# backends/remote_client_backend.py
from __future__ import annotations
import base64, requests
from typing import Optional, Iterable, Dict, Any, Union, List

from arduino_colab_kernel.backends.protocol import Backend
from arduino_colab_kernel.board.board import Board

class RemoteBackend(Backend):
    """HTTP klient – serializuje Board přes board.export() a volá server."""
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": token})

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.session.post(f"{self.base_url}{path}", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()

    def compile(self, board: Board, sketch_source: str,
                extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        return self._post("/compile", {
            "board": board.export(),  # <<<<< jednotný přenos Boardu
            "sketch_b64": base64.b64encode(sketch_source.encode("utf-8")).decode("ascii"),
            "extra_args": list(extra_args) if extra_args else []
        })

    def upload(self, board: Board, sketch_source: str,
               extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        return self._post("/upload", {
            "board": board.export(),
            "sketch_b64": base64.b64encode(sketch_source.encode("utf-8")).decode("ascii"),
            "extra_args": list(extra_args) if extra_args else []
        })

    def open_serial(self, board: Board) -> None:
        self._post("/serial/open", {"board": board.export()})

    def close_serial(self, board: Board) -> None:
        self._post("/serial/close", {"board": board.export()})

    def read_serial(self, board: Board, size: int = -1) -> bytes:
        data = self._post("/serial/read", {"board": board.export(), "size": size})
        b64 = data.get("data_b64") or ""
        return base64.b64decode(b64.encode("ascii")) if b64 else b""
    
    def readlines_serial(self, board: Board, size: int = 1) -> List[str]:
        data = self._post("/serial/readlines", {"board": board.export(), "size": size})
        lines = data.get("lines") or []
        return list(lines) if isinstance(lines, list) else []

    def write_serial(self, board: Board, data: Union[bytes, str], append_newline: bool = True) -> int:
        if isinstance(data, str):
            b64 = base64.b64encode(data.encode("utf-8")).decode("ascii")
        else:
            b64 = base64.b64encode(data).decode("ascii")
        out = self._post("/serial/write", {"board": board.export(), "data_b64": b64, "append_newline": append_newline})
        return int(out.get("written", 0))
