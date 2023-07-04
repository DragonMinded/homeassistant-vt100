import json
import os
from flask import Flask, Response


def monitoring_thread(port: int, version: str) -> None:
    app = Flask("monitoring thread")

    @app.route("/")
    def monitor() -> Response:
        return Response(
            response=json.dumps(
                {
                    "type": "vt-100",
                    "version": version,
                }
            ),
            status=200,
            mimetype="application/json",
        )

    try:
        print(f"Listening on port {port} for monitoring HTTP requests.")

        # Kinda stupid that we can't disable this. I don't care that this is non-production,
        # its literally a monitoring port for a local-only VT-100 controlling terminal.
        import sys

        f = open(os.devnull, "w")
        sys.stdout = f
        sys.stderr = f

        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        # Silently exit without spewing
        pass
