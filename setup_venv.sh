# Create a local virtual environment in .venv and install everything in requirements.txt
#   bash setup_venv.sh            create .venv, install requirements.txt
#   bash setup_venv.sh --clean    wipe any existing .venv first, then set up fresh
#   bash setup_venv.sh --test     also run the test suite once setup finishes
#
# Activate with:
#   source .venv/bin/activate
#
# Decativate with:
#   deactivate

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

VENV_DIR=".venv"
MIN_PYTHON="3.9"
CLEAN=0
RUN_TESTS=0

for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=1 ;;
        --test)  RUN_TESTS=1 ;;
        -h|--help)
            grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "error: unknown option '$arg' (use --clean, --test, or --help)" >&2
            exit 1
            ;;
    esac
done

if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 not found on PATH" >&2
    exit 1
fi

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "error: Python ${MIN_PYTHON}+ required, found $(python3 --version)" >&2
    exit 1
fi

if [[ "$CLEAN" -eq 1 && -d "$VENV_DIR" ]]; then
    echo "Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
fi

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment in $VENV_DIR (Python $(python3 --version | cut -d' ' -f2))..."
    # --upgrade-deps keeps pip/setuptools inside the venv current (needs Python 3.9+, which we just checked)
    python3 -m venv --upgrade-deps "$VENV_DIR"
else
    echo "Reusing existing virtual environment in $VENV_DIR (use --clean to rebuild from scratch)"
fi

echo "Installing dependencies from requirements.txt..."
"$VENV_DIR/bin/python" -m pip install --quiet -r requirements.txt

echo
echo "Installed:"
"$VENV_DIR/bin/python" -m pip list --format=columns | tail -n +3

if [[ "$RUN_TESTS" -eq 1 ]]; then
    echo
    echo "Running tests..."
    "$VENV_DIR/bin/python" -m pytest -v tester.py
fi

echo
echo "Done. Activate with:  source $VENV_DIR/bin/activate"
