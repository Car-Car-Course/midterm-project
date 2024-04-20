import abc
import csv
import logging
import re
from typing import Optional, Tuple, cast

import requests
import socketio

log = logging.getLogger("scoreboard")


class Scoreboard(abc.ABC):
    """
    The Scoreboard class connects to the server socket and enables updating score by sending UID.
    """

    @abc.abstractmethod
    def add_UID(self, UID_str: str) -> Tuple[int, float]:
        """Send {UID_str} to server to update score. Returns (score, time_remaining)."""
        pass

    @abc.abstractmethod
    def get_current_score(self) -> Optional[int]:
        """Fetch current score from server. Returns current score."""
        pass


class ScoreboardFake(Scoreboard):
    """
    Fake scoreboard. Check uid with fakeUID.csv
    """

    def __init__(self, teamname, filepath):
        self.total_score = 0
        self.team = teamname
        log.info(f"Using fake scoreboard!")
        log.info(f"{self.team} is playing game!")

        self._read_UID_file(filepath)

        self.visit_list = set()

    def _read_UID_file(self, filepath: str):
        self.uid_to_score = {}
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)
            for row in rows[1:]:
                uid, score = row
                self.uid_to_score[uid] = int(score)
        log.info("Successfully read the UID file!")

    def add_UID(self, UID_str: str) -> Tuple[int, float]:
        log.debug(f"Adding UID: {UID_str}")

        if not isinstance(UID_str, str):
            raise ValueError(f"UID format error! (expected: str) (got: {UID_str})")

        if not re.match(r"^[0-9A-Fa-f]{8}$", UID_str):
            raise ValueError(
                f"UID format error! (expected: 8 hex digits) (got: {UID_str})"
            )

        if UID_str not in self.uid_to_score:
            log.info(f"This UID is not in the list: {UID_str}")
            return 0, 0
        elif UID_str in self.visit_list:
            log.info(f"This UID has been visited: {UID_str}")
            return 0, 0
        else:
            point = self.uid_to_score[UID_str]
            self.total_score += point
            log.info(f"A treasure is found! You got {point} points.")
            self.visit_list.add(UID_str)
            return point, 0

    def get_current_score(self):
        return int(self.total_score)


class ScoreboardServer(Scoreboard):
    """
    The Scoreboard class connects to the server socket and enables updating score by sending UID.
    """

    def __init__(self, teamname: str, host=f"http://localhost:3000", debug=False):
        self.teamname = teamname
        self.ip = host

        log.info(f"{self.teamname} wants to play!")
        log.info(f"connecting to server......{self.ip}")

        # create socket.io instance and connect to server
        self.socket = socketio.Client(logger=debug, engineio_logger=debug)
        self.socket.register_namespace(TeamNamespace("/team"))
        self.socket.connect(self.ip)
        self.sid = self.socket.get_sid(namespace="/team")

        # start game
        log.info("Game is starting.....")
        self._start_game(self.teamname)

    def _start_game(self, teamname: str):
        payload = {"teamname": teamname}
        res = self.socket.call("start_game", payload, namespace="/team")
        log.info(res)

    def add_UID(self, UID_str: str) -> Tuple[int, float]:
        """Send {UID_str} to server to update score. Returns nothing."""
        log.debug(f"Adding UID: {UID_str}")

        if not isinstance(UID_str, str):
            raise ValueError(f"UID format error! (expected: str) (got: {UID_str})")

        if not re.match(r"^[0-9A-Fa-f]{8}$", UID_str):
            raise ValueError(
                f"UID format error! (expected: 8 hex digits) (got: {UID_str})"
            )

        res = self.socket.call("add_UID", UID_str, namespace="/team")
        if not res:
            log.error("Failed to add UID")
            return 0, 0
        res = cast(dict, res)
        message = res.get("message", "No message")
        score = res.get("score", 0)
        time_remaining = res.get("time_remaining", 0)
        log.info(message)
        return score, time_remaining

    def get_current_score(self) -> Optional[int]:
        try:
            log.debug(f"{self.ip}/current_score?sid={self.sid}")
            res = requests.get(self.ip + "/current_score", params={"sid": self.sid})
            return res.json()["current_score"]
        except Exception as e:
            log.error(f"Failed to fetch current score: {e}")
            return None


class TeamNamespace(socketio.ClientNamespace):
    def on_connect(self):
        client = cast(socketio.Client, self.client)
        log.info(f"Connected with sid {client.get_sid(namespace='/team')}")

    def on_UID_added(self, message):
        log.info(message)

    def on_disconnect(self):
        log.info("Disconnected from server")


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.DEBUG)

    try:
        # scoreboard = ScoreboardServer("TeamName2", "http://140.112.175.18:5000")
        scoreboard = ScoreboardFake("TeamName", "data/fakeUID.csv")
        time.sleep(1)

        score, time_remaining = scoreboard.add_UID("10BA617E")
        current_score = scoreboard.get_current_score()
        log.info(f"Current score: {current_score}")
        time.sleep(1)

        score, time_remaining = scoreboard.add_UID("556D04D6")
        current_score = scoreboard.get_current_score()
        log.info(f"Current score: {current_score}")
        time.sleep(1)

        score, time_remaining = scoreboard.add_UID("12345678")
        current_score = scoreboard.get_current_score()
        log.info(f"Current score: {current_score}")

    except KeyboardInterrupt:
        exit(1)
