"""Example Reaper extension. Run only after reviewing and trusting this file."""


class HelloWorld:
    def __init__(self, host_api):
        self.host_api = host_api

    def on_load(self, context):
        self.host_api.log(f"loaded by {context.host_id}")

    def run(self, operation, arguments):
        return {
            "plugin": "hello-world",
            "operation": operation,
            "message": str(arguments.get("message", "Hello from Reaper"))[:500],
        }

    def on_event(self, event, payload):
        return {"received": event, "keys": sorted(payload.keys())}

    def on_unload(self, context):
        self.host_api.log("unloaded")


def create_plugin(host_api):
    return HelloWorld(host_api)
