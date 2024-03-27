import logging
import sys

import numpy as np
import pandas
import requests
import socketio

log = logging.getLogger(__name__)


class ScoreboardFake:
    """
    Fake scoreboard. Check uid with fakeUID.csv
    """

    def __init__(self, teamname, filepath):
        raw_data = np.array(pandas.read_csv(filepath))  # .values

        self.total_score = 0
        self.team = teamname

        log.info(f"{self.team} is playing game!")

        self.card_list = [int(a, 16) for a in raw_data.T[0]]

        # data member specific for Game: self.cardValue, self.visitList
        self.visit_list = list()
        self.card_value = dict()
        for i in range(len(raw_data)):
            self.card_value[self.card_list[i]] = raw_data[i][1]
        log.info("Successfully read the UID file!")

    def add_UID(self, UID_str):
        UID = int(UID_str, 16)  # hex to dec

        if UID not in self.card_list:
            log.info("This UID doesn't exist in the UID list file:", hex(UID))
        else:
            if UID in self.visit_list:
                log.info("This UID is already visited:", hex(UID))
            else:
                point = self.card_value[UID]
                self.total_score += point
                log.info(f"A treasure is found! You got {point} points.")
                log.info("Current score: " + str(self.total_score))
                self.visit_list.append(UID)

    def get_current_score(self):
        return int(self.total_score)


class TeamNamespace(socketio.ClientNamespace):
    def on_connect(self):
        log.info(f"Connected with sid {self.client.get_sid(namespace='/team')}")

    def on_game_started(self, data):
        teamname = data["teamname"]
        log.info(f"Game started! Playing game as {teamname}")

    def on_UID_added(self, message):
        log.info(message)


class Scoreboard:
    """
    The Scoreboard class connects to the server socket and enables updating score by sending UID.
    """

    def __init__(self, team_name: str, host: str, debug: bool = False):
        self.totalScore = 0
        self.team_name = team_name
        self.game = 0
        self.ip = host

        log.info(f"{self.team_name} wants to play!")
        log.info(f"connecting to server {self.ip}......")

        # create socket.io instance and connect to server
        self.socket = socketio.Client(logger=debug, engineio_logger=debug)
        self.socket.register_namespace(TeamNamespace("/team"))
        self.socket.connect(self.ip)
        self.sid = self.socket.get_sid(namespace="/team")

        # start game
        log.info("Game is starting.....")
        self._start_game(self.team_name)

    def _start_game(self, teamname: str):
        payload = {"teamname": teamname}
        self.socket.emit("start_game", payload, namespace="/team")

    def add_UID(self, UID_str: str):
        """Send {UID_str} to server to update score. Returns nothing."""
        UID_len = len(UID_str)
        log.info("In add_UID, UID = {}".format(UID_str))
        if not isinstance(UID_str, str):
            log.info(f"    UID type error! (Your type: {type(UID_str)}, expected: str)")
        if UID_len != 8:
            log.info(f"    UID length error! (Your length: {UID_len}, expected: 8)")
        self.socket.emit("add_UID", UID_str, namespace="/team")

    def get_current_score(self):
        try:
            log.info(f"{self.ip}/current_score?sid={self.sid}")
            r = requests.get(self.ip + "/current_score", params={"sid": self.sid})
            return r.json()["current_score"]
        except Exception as e:
            log.info(f"Failed to fetch current score: {e}")
            return None


if __name__ == "__main__":
    import time

    try:
        scoreboard = Scoreboard("TeamName2", "http://140.112.175.18:5000")
        # myScoreboard = ScoreboardFake("TeamName","data/fakeUID.csv")
        time.sleep(6)
        scoreboard.add_UID("61C9931C")
        scoreboard.add_UID("D1874019")
        scoreboard.add_UID("12346578")
        log.info("score:", scoreboard.get_current_score())
    except KeyboardInterrupt:
        sys.exit(1)
