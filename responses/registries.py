class PopFirstKeepLastRegistry(object):
    def __init__(self, responses=None):
        self._responses = list(responses or [])

    def __len__(self):
        return len(self._responses)

    def __iter__(self):
        for index, response in self._matching_order():
            yield response

    def __contains__(self, response):
        return response in self._responses

    def clear(self):
        self._responses.clear()

    def index(self, response):
        for index, match in self._matching_order():
            if response == match:
                return index
        raise ValueError("Response is not registered for URL {}".format(response.url))

    def _matching_order(self):
        return enumerate(self._responses)

    def find_match(self, request):
        found = None
        found_match = None
        match_failed_reasons = []
        for i, response in self._matching_order():
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
