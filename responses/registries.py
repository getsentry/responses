from collections import deque


class PopFirstKeepLastRegistry(object):
    def __init__(self, responses=None):
        self._responses = list(responses or [])

    def __len__(self):
        return len(self._responses)

    def __iter__(self):
        return self._responses.__iter__()

    def __contains__(self, response):
        return response in self._responses

    def clear(self):
        try:
            self._responses.clear()
        except AttributeError:
            # python 2 does not know clear
            del self._responses[:]

    def index(self, response):
        try:
            return self._responses.index(response)
        except ValueError:
            raise ValueError(
                "Response is not registered for URL {}".format(response.url)
            )

    def find_match(self, request):
        found = None
        found_match = None
        match_failed_reasons = []
        for i, response in enumerate(self._responses):
            match_result, reason = response.matches(request)
            if match_result:
                if found is None:
                    found = i
                    found_match = response
                else:
                    # Multiple matches found.  Remove & return the first response.
                    return self._responses.pop(found), match_failed_reasons
            else:
                match_failed_reasons.append((response, reason))
        return found_match, match_failed_reasons

    def add(self, response):
        self._responses.append(response)

    def remove(self, response):
        while response in self._responses:
            self._responses.remove(response)

    def replace(self, response):
        index = self.index(response)
        self._responses[index] = response


class InsertionOrderRegistry(PopFirstKeepLastRegistry):
    def find_match(self, request):
        match_failed_reasons = []
        for response in self._responses:
            success, reason = response.matches(request)
            if success:
                return response, match_failed_reasons
            match_failed_reasons.append((response, reason))
        return None, match_failed_reasons


class StrictOrderRegistry(PopFirstKeepLastRegistry):
    def __init__(self, responses=None):
        self._responses = deque(responses or [])

    def find_match(self, request):
        response = self._responses.popleft()
        success, reason = response.matches(request)
        if success:
            return response, []
        self._responses.appendleft(response)
        return None, [(response, reason)]
