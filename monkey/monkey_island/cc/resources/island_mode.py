import json
import logging
from http import HTTPStatus

from flask import request

from monkey_island.cc.event_queue import IIslandEventQueue, IslandEventTopic
from monkey_island.cc.models import IslandMode as IslandModeEnum
from monkey_island.cc.resources.AbstractResource import AbstractResource
from monkey_island.cc.resources.request_authentication import jwt_required
from monkey_island.cc.services import IslandModeService

logger = logging.getLogger(__name__)


class IslandMode(AbstractResource):
    urls = ["/api/island/mode"]

    def __init__(
        self, island_mode_service: IslandModeService, island_event_queue: IIslandEventQueue
    ):
        self._island_mode_service = island_mode_service
        self._island_event_queue = island_event_queue

    @jwt_required
    def put(self):
        try:
            mode = IslandModeEnum(request.json)

            self._island_mode_service.set_mode(mode)
            self._island_event_queue.publish(topic=IslandEventTopic.SET_MODE, event=mode)

            return {}, HTTPStatus.NO_CONTENT
        except (AttributeError, json.decoder.JSONDecodeError):
            return {}, HTTPStatus.BAD_REQUEST
        except ValueError:
            return {}, HTTPStatus.UNPROCESSABLE_ENTITY

    @jwt_required
    def get(self):
        island_mode = self._island_mode_service.get_mode()
        return island_mode.value, HTTPStatus.OK
