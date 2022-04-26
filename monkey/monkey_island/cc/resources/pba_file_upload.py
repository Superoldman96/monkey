import copy
import logging
from http import HTTPStatus

import flask_restful
from flask import Response, make_response, request, send_file
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from common.config_value_paths import PBA_LINUX_FILENAME_PATH, PBA_WINDOWS_FILENAME_PATH
from monkey_island.cc.resources.auth.auth import jwt_required
from monkey_island.cc.services import IFileStorageService
from monkey_island.cc.services.config import ConfigService

logger = logging.getLogger(__file__)


# Front end uses these strings to identify which files to work with (linux or windows)
LINUX_PBA_TYPE = "PBAlinux"
WINDOWS_PBA_TYPE = "PBAwindows"


class FileUpload(flask_restful.Resource):
    """
    File upload endpoint used to exchange files with filepond component on the front-end
    """

    def __init__(self, file_storage_service: IFileStorageService):
        self._file_storage_service = file_storage_service

    # TODO: Fix references/coupling to filepond
    # TODO: Replace "file_type" with "target_os" or similar
    # TODO: Add comment explaining why this is basically a duplicate of the endpoint in the
    #       PBAFileDownload resource.
    @jwt_required
    def get(self, file_type):
        """
        Sends file to filepond
        :param file_type: Type indicates which file to send, linux or windows
        :return: Returns file contents
        """
        if self._is_pba_file_type_supported(file_type):
            return Response(status=HTTPStatus.UNPROCESSABLE_ENTITY, mimetype="text/plain")

        # Verify that file_name is indeed a file from config
        if file_type == LINUX_PBA_TYPE:
            # TODO: Make these paths Tuples so we don't need to copy them
            filename = ConfigService.get_config_value(copy.deepcopy(PBA_LINUX_FILENAME_PATH))
        else:
            filename = ConfigService.get_config_value(copy.deepcopy(PBA_WINDOWS_FILENAME_PATH))

        try:
            file = self._file_storage_service.open_file(filename)

            # `send_file()` handles the closing of the open file.
            return send_file(file, mimetype="application/octet-stream")
        except OSError as ex:
            error_msg = f"Failed to open file {filename}: {ex}"
            logger.error(error_msg)
            return make_response({"error": error_msg}, 404)

    @jwt_required
    def post(self, file_type):
        """
        Receives user's uploaded file from filepond
        :param file_type: Type indicates which file was received, linux or windows
        :return: Returns flask response object with uploaded file's filename
        """
        if self._is_pba_file_type_supported(file_type):
            return Response(status=HTTPStatus.UNPROCESSABLE_ENTITY, mimetype="text/plain")

        filename = self._upload_pba_file(
            # TODO: This "filepond" string can be changed to be more generic in the `react-filepond`
            # component.
            request.files["filepond"],
            (file_type == LINUX_PBA_TYPE),
        )

        response = Response(response=filename, status=200, mimetype="text/plain")
        return response

    def _upload_pba_file(self, file_storage: FileStorage, is_linux=True):
        """
        Uploads PBA file to island's file system
        :param request_: Request object containing PBA file
        :param is_linux: Boolean indicating if this file is for windows or for linux
        :return: filename string
        """
        filename = secure_filename(file_storage.filename)
        self._file_storage_service.save_file(filename, file_storage.stream)

        ConfigService.set_config_value(
            (PBA_LINUX_FILENAME_PATH if is_linux else PBA_WINDOWS_FILENAME_PATH), filename
        )

        return filename

    @jwt_required
    def delete(self, file_type):
        """
        Deletes file that has been deleted on the front end
        :param file_type: Type indicates which file was deleted, linux of windows
        :return: Empty response
        """
        if self._is_pba_file_type_supported(file_type):
            return Response(status=HTTPStatus.UNPROCESSABLE_ENTITY, mimetype="text/plain")

        filename_path = (
            PBA_LINUX_FILENAME_PATH if file_type == "PBAlinux" else PBA_WINDOWS_FILENAME_PATH
        )
        filename = ConfigService.get_config_value(filename_path)
        if filename:
            self._file_storage_service.delete_file(filename)
            ConfigService.set_config_value(filename_path, "")

        return make_response({}, 200)

    @staticmethod
    def _is_pba_file_type_supported(file_type: str) -> bool:
        return file_type not in {LINUX_PBA_TYPE, WINDOWS_PBA_TYPE}
