import os


class Plugin:
    name = "auth"

    def register(self, hooks):
        self._session_id = hooks.get("_session_id", "")
        hooks.setdefault("check_auth", []).append(self.check_auth)

    def execute(self, context):
        return self.check_auth(context.get("token", ""))

    def check_auth(self, token):
        expected = os.environ.get("MUSCAL_API_KEY", "")
        if not expected:
            expected = self._session_id
        if not expected:
            return True
        return token == expected
