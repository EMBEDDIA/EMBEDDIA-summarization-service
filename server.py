import argparse
import logging.handlers
from pathlib import Path
import sys
from typing import Any, Dict

from main import summarize as run_model

import bottle
import bottle_swagger
import yaml
from sentence_transformers import SentenceTransformer

# CLI parameters
parser = argparse.ArgumentParser(description="Run the Dockerized Comment Analysis API skeleton.")
parser.add_argument("port", type=int, default=8080, help="port number to attach to")
args = parser.parse_args()
sys.argv = sys.argv[0:1]

# Set up logging to two streams:
# - Logging to a rotating server.log logfile. Max file size is 5 megs, and at most three files are kept. By default
#   logs only events at INFO or higher (as disk IO takes a bunch of time)
# - Logging to STDOUT. By default logs levels DEBUG and higher.
log = logging.getLogger("root")
log.setLevel(logging.INFO)  # General log level. Overwrites below, consider setting to INFO for production.
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)  # STDOUT log level
log.addHandler(stream_handler)

rotating_file_handler = logging.handlers.RotatingFileHandler(
    Path(__file__).parent / "server.log",
    mode="a",
    maxBytes=5 * 1024 * 1024,  # 5 megs
    backupCount=2,
    encoding=None,
    delay=0,
)
rotating_file_handler.setFormatter(formatter)
rotating_file_handler.setLevel(logging.INFO)  # File logging level
log.addHandler(rotating_file_handler)

# Bottle
app = bottle.Bottle()

# Swagger
with open(Path(__file__).parent / "swagger.yml", "r") as file_handle:
    swagger_def = yaml.load(file_handle, Loader=yaml.FullLoader)
app.install(
    bottle_swagger.SwaggerPlugin(
        swagger_def, serve_swagger_ui=True, swagger_ui_suburl="/documentation/", validate_requests=False
    )
)


def allow_cors(opts):
    def decorator(func):
        """ This is a decorator which enables CORS for specified endpoint. """

        def wrapper(*args, **kwargs):
            bottle.response.headers["Access-Control-Allow-Origin"] = "*"
            bottle.response.headers["Access-Control-Allow-Methods"] = ", ".join(opts)
            bottle.response.headers["Access-Control-Allow-Headers"] = (
                "Origin, Accept, Content-Type, X-Requested-With, " "X-CSRF-Token"
            )

            # Only respond with body for non-OPTIONS
            if bottle.request.method != "OPTIONS":
                return func(*args, **kwargs)

        return wrapper

    return decorator


@app.route("/summarize", method=["POST", "OPTIONS"])
@allow_cors(["POST", "OPTIONS"])
def summarize() -> Dict[str, Any]:
    """ Main API entry point.

    NB: Any changes to the output of this function (e.g. renaming "sentiments", needs to be reflected to swagger.yml
    """
    parameters = bottle.request.json

    log.info(f"Received request to /summarize")
    log.debug(f"params={parameters}")

    if not parameters:
        bottle.response.status = 400
        return {"errors": ["Missing or empty request body"]}

    errors = []
    comments = parameters.get("comments")
    if not comments:
        errors.append("Invalid or missing comment list.")

    count = min(2, len(comments))
    if "count" in parameters:
        try:
            count = int(parameters.get("count"))
        except Exception:
            errors.append("Invalid count")

    if errors:
        bottle.response.status = 400
        return {"errors": errors}

    try:
        return {"summary": run_model(comments, n=count)}
    except Exception as ex:
        log.error(ex)
        bottle.response.status = 500
        return {"errors": ["Internal error during summarization"]}


@app.route("/health", method=["GET", "OPTIONS"])
@allow_cors(["GET", "OPTIONS"])
def health() -> Dict[str, Any]:
    return {"version": "1.0.0"}


if __name__ == "__main__":
    log.info(f"Checking that Transformer model is present")
    SentenceTransformer("xlm-r-100langs-bert-base-nli-stsb-mean-tokens")
    log.info(f"Starting server at {args.port}")
    bottle.run(app, server="meinheld", host="0.0.0.0", port=args.port)
    log.info("Stopping")
