cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
python stream.py $@