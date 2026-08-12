"""Data model for envoy simulator."""

import json
import logging
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree as et

from awesomeversion import AwesomeVersion

logger = logging.getLogger(__name__)

CYCLE_ENVOY_START = 5  # first 5 request after start are marked as envoy starting


@dataclass(slots=True)
class EnvoySim:
    """All data to run the envoy simulator."""

    data_path: str = "./data"
    serial: str = ""  # use this serial, overrides envoy serial in files
    firmware: str = ""  # store fw after /info is loaded
    verbosity: int = 0  # verbosity level set, can be controlled from API
    path: str = "default"  # fixture folder to use for data
    auth_count: int = 0  # must be >0 to be authorized, auth jwt endpoint adds 1
    envoy_cycling: int = 0  # next replies will simulate restart of envoy
    timeoutsim: bool = False  # simulate timeout by long wait time before response
    sleepers: int = 0  # number of sleeping requests
    ip_sleep_time: int = 450  # sleep this long to simulate timeout
    next_request_status: int = 0  # next request reply status if not 0
    empty_inverter_array: bool = False  # return empty inverter array
    invalid_json: bool = False  # invalid json for next inverter datan request if >0
    next_tariff_status: int = 0  # reply nexttarif endpoint with this status
    sc_sched_status_0: bool = False  # return invalid status 0
    active_eim_0: bool = False  # return active eim 0 in /production

    stream: bool = False  # streaming mode on/off
    stream_interval: float = 2.0  # sleep time between sending stream data

    # fixture files are loaded in cache when read, put,post, delete can change data
    fixture_cache: dict[str, Any] = field(default_factory=dict)  # type: ignore

    # supported endpoints
    envoy_profile: dict[str, str] = field(default_factory=dict)  # type: ignore

    def reset_fixture_cache(self):
        """Reset fixture cache."""
        self.fixture_cache = {}

    def fixture_home(self) -> str:
        """Return folder where fixture folders are."""
        return self.data_path + "/fixtures"

    def fixture_folder(self) -> str:
        """Return current fixture folder."""
        return self.fixture_home() + "/" + self.path

    def load_json(
        self, file: str, cache_it: bool = True, from_cache: bool = True
    ) -> tuple[Any, int, str, bool]:
        """Return file content as json object from cache or file and store in cache."""
        if from_cache and file in self.fixture_cache:
            return self.fixture_cache[file], 200, file, False
        target = self.fixture_folder() + "/" + file
        try:
            with open(target) as f:
                logger.debug(f"loading: {target}")
                content = json.load(f), 200, file, True
                if cache_it:
                    self.fixture_cache[file] = content[0]
                return content
        except FileNotFoundError, IsADirectoryError:
            logger.debug(f"File Not Found {target}")
            return f"fixture {file} notfound", 404, file, False
        except ValueError as err:
            logger.warning(f"Value Error in {target}, {err}")
            return f"value error in {file}", 404, file, False

    def load_text_file(
        self, file: str, cache_it: bool = True, from_cache: bool = True
    ) -> tuple[Any, int, str, bool]:
        """Return html or xml file as text from cache or file and store in cache."""
        if from_cache and file in self.fixture_cache:
            return self.fixture_cache[file], 200, file, False
        target = self.fixture_folder() + "/" + file
        try:
            with open(target) as f:
                logger.debug(f"loading: {target}")
                content = f.read(), 200, file, True
                if cache_it:
                    self.fixture_cache[file] = content[0]
                return content
        except FileNotFoundError, IsADirectoryError:
            if ".xml" not in file:
                logger.debug(f"file Not Found (1): {target}")
                return f"fixture {file} notfound", 404, file, False
            # try again witouth xml extension
            return self.load_text_file(str.replace(file, ".xml", ""))

    def add_info_to_cache(self) -> None:
        """Load info file in cache and patch serial."""
        content = self.load_text_file("info")
        if content[1] == 200:
            # override serial number in data
            tree = et.fromstring(content[0])  # noqa: S314
            sn = tree.find("device/sn")
            if sn is not None and self.serial:
                sn.text = self.serial
                content = et.tostring(tree), content[1], content[2]
                # update cache for serial patch
                self.fixture_cache[content[2]] = content[0]

            # grab firmware and set in model
            fw = tree.find("device/software")
            if fw is not None and fw.text:
                self.firmware = fw.text[1:]

    def authorized(self) -> bool:
        """Return authorized state, before V7 firmware is always authorized."""
        if (major := AwesomeVersion(self.firmware).major) and major < "7":
            return True
        return self.auth_count > 0

    def start_sim(self) -> None:
        """(re-)start simulation."""
        logger.info(f"sim path: {self.path}")

        self.reset_fixture_cache()
        self.add_info_to_cache()
        self.auth_count = 0
        self.timeoutsim = False
        self.sleepers = 0
        self.next_request_status = 0
        self.empty_inverter_array = False
        self.invalid_json = False
        self.next_tariff_status = 0
        self.sc_sched_status_0 = False
        self.active_eim_0 = False

        logger.info(f"sim firmware: {self.firmware}")
        logger.info(f"sim serial: {self.serial}")

    def cycle_envoy(self) -> None:
        """Simulate a restart of the Envoy with some timeouts."""
        self.start_sim()
        self.envoy_cycling = CYCLE_ENVOY_START
