# -*- coding: utf-8 -*-
"""
smsc.api module.

This module implements the SMSC.ru HTTP API.

:copyright: (c) 2017 by Alexey Shevchenko.
:license: MIT, see LICENSE for more details.
"""
import logging  # noqa: T005
from typing import Any, Dict, List, Optional, Union

import requests  # noqa: T005
from furl import furl

from .exceptions import GetBalanceError, GetCostError, GetStatusError, SendError
from .messages import Message
from .responses import BalanceResponse, CostResponse, SendResponse, StatusResponse

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


class SMSC:
    """
    Class for interaction with smsc.ru API.

    :param str login: Account login name
    :param str password: Password or MD5 hash of password in lower case
    """

    _url = "https://smsc.ru/sys/"

    def __init__(self, login: str, password: str, sender: Optional[str] = None) -> None:  # noqa: D102
        self.__login = login
        self.__password = password
        self.__sender = sender if sender is not None else "SMSC.ru"

    def __str__(self):
        """Represent object as string."""
        return "<%s login='%s' sender='%s'>" % (self.__class__.__name__, self.__login, self.__sender)

    @property
    def __auth(self) -> Dict[str, Any]:
        return {"login": self.__login, "psw": self.__password, "fmt": 3}

    def send(self, to: Union[str, List[str]], message: Message) -> SendResponse:
        """
        Send the message.

        :param Union[str, List[str]] to: Phone number or list of phone numbers
        :param Message message: Concrete message instance for sending
        :return: Returns the API answer wrapped in the `SendResponse` object
        :rtype: SendResponse
        """
        f = furl(SMSC._url).add(path="send.php").add(self.__auth).add({"sender": self.__sender})
        f.add({"cost": 2, "phones": isinstance(to, str) and to or ",".join(to)})
        f.add(message.encode())
        r = requests.get(f.url)
        if r.status_code != 200:
            raise SendError(str([r.status_code, r.headers, r.text]))
        return SendResponse(r.json())

    def get_cost(self, to: Union[str, List[str]], message: Message) -> CostResponse:
        """
        Retrieve cost of the message.

        :param Union[str, List[str]] to: Phone number or list of phone numbers
        :param Message message: Concrete message instance for measure cost
        :return: Returns the API answer wrapped in the `CostResponse` object
        :rtype: CostResponse
        """
        f = furl(SMSC._url).add(path="send.php").add(self.__auth).add({"sender": self.__sender})
        f.add({"cost": 1, "phones": isinstance(to, str) and to or ",".join(to)})
        f.add(message.encode())
        r = requests.get(f.url)
        if r.status_code != 200:
            raise GetCostError(str([r.status_code, r.headers, r.text]))
        return CostResponse(r.json())

    def get_status(self, to: Union[str, List[str]], msg_id: Union[str, List[str]]) -> List[StatusResponse]:
        """
        Get current status of sent message.

        :param Union[str, List[str]] to: Phone number or list of phone numbers
        :param Union[str, List[str]] msg_id: Identificato of sent message or list of them
        :return: Returns the API answer wrapped in the list of `StatusResponse` objects
        :rtype: List[StatusResponse]
        """
        f = furl(SMSC._url).add(path="status.php").add(self.__auth).add({"charset": "utf-8", "all": 2})
        f.add({"phone": isinstance(to, str) and ",".join([to, ""]) or ",".join(to)})
        f.add({"id": isinstance(msg_id, str) and ",".join([msg_id, ""]) or ",".join(msg_id)})
        r = requests.get(f.url)
        if r.status_code != 200:
            raise GetStatusError(str([r.status_code, r.headers, r.text]))
        res = r.json()
        result = []
        for obj in res:
            result.append(StatusResponse(obj))
        return result

    def get_balance(self) -> BalanceResponse:
        """
        Get current account balance.

        :return: Returns the API answer wrapped in the `BalanceResponse` object
        :rtype: BalanceResponse
        """
        f = furl(SMSC._url).add(path="balance.php").add(self.__auth).add({"cur": 1})
        r = requests.get(f.url)
        if r.status_code != 200:
            raise GetBalanceError(str([r.status_code, r.headers, r.text]))
        return BalanceResponse(r.json())
