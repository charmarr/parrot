from theow import action


@action("retry_command")
def retry_command() -> dict:
    """No-op action. Returns success so theow retries the marked function."""
    return {"status": "ok"}
