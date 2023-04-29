#!/bin/bash

# Change directory to script's directory
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )"

# Run gunicorn from local virtual environment
./.venv/bin/gunicorn --error-logfile gunicorn-error.log --reload -b localhost:5050 app:app
