import copy
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import toml as _toml

if TYPE_CHECKING:  # pragma: no cover
    # import only for linter run
    import io

    from requests import PreparedRequest

    from responses import BaseResponse


class FirstMatchRegistry(object):
    def __init__(self) -> None:
        self._responses: List["BaseResponse"] = []

    @property
    def registered(self) -> List["BaseResponse"]:
        return self._responses

    def reset(self) -> None:
        self._responses = []

    def find(
        self, request: "PreparedRequest"
    ) -> Tuple[Optional["BaseResponse"], List[str]]:
        found = None
        found_match = None
        match_failed_reasons = []
        for i, response in enumerate(self.registered):
            match_result, reason = response.matches(request)
            if match_result:
                if found is None:
                    found = i
                    found_match = response
                else:
                    if self.registered[found].call_count > 0:
                        # that assumes that some responses were added between calls
                        self.registered.pop(found)
                        found_match = response
                        break
                    # Multiple matches found.  Remove & return the first response.
                    return self.registered.pop(found), match_failed_reasons
            else:
                match_failed_reasons.append(reason)
        return found_match, match_failed_reasons

    def add(self, response: "BaseResponse") -> "BaseResponse":
        if any(response is resp for resp in self.registered):
            # if user adds multiple responses that reference the same instance.
            # do a comparison by memory allocation address.
            # see https://github.com/getsentry/responses/issues/479
            response = copy.deepcopy(response)

        self.registered.append(response)
        return response

    def remove(self, response: "BaseResponse") -> List["BaseResponse"]:
        removed_responses = []
        while response in self.registered:
            self.registered.remove(response)
            removed_responses.append(response)
        return removed_responses

    def replace(self, response: "BaseResponse") -> "BaseResponse":
        try:
            index = self.registered.index(response)
        except ValueError:
            raise ValueError(
                "Response is not registered for URL {}".format(response.url)
            )
        self.registered[index] = response
        return response

    def _dump(self, destination: "io.IOBase") -> None:
        data: Dict[str, Any] = {"responses": []}
        for rsp in self.registered:
            try:
                content_length = rsp.auto_calculate_content_length  # type: ignore[attr-defined]
                data["responses"].append(
                    {
                        "response": {
                            "method": rsp.method,
                            "url": rsp.url,
                            "body": rsp.body,  # type: ignore[attr-defined]
                            "status": rsp.status,  # type: ignore[attr-defined]
                            "headers": rsp.headers,
                            "content_type": rsp.content_type,
                            "auto_calculate_content_length": content_length,
                        }
                    }
                )
            except AttributeError as exc:  # pragma: no cover
                raise AttributeError(
                    "Cannot dump response object."
                    "Probably you use custom Response object that is missing required attributes"
                ) from exc
        _toml.dump(data, destination)


class OrderedRegistry(FirstMatchRegistry):
    def find(
        self, request: "PreparedRequest"
    ) -> Tuple[Optional["BaseResponse"], List[str]]:

        if not self.registered:
            return None, ["No more registered responses"]

        response = self.registered.pop(0)
        match_result, reason = response.matches(request)
        if not match_result:
            self.reset()
            self.add(response)
            reason = (
                "Next 'Response' in the order doesn't match "
                f"due to the following reason: {reason}."
            )
            return None, [reason]

        return response, []
