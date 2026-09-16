cd src/backend

# Keep the executable virtual environment on local storage.
export UV_PROJECT_ENVIRONMENT="/data/smb-ewald/polar-web-app/backend-venv"
#mkdir -p "$(dirname "$UV_PROJECT_ENVIRONMENT")"

# Let uv install/use a supported Python version and create the environment.
#uv python install 3.11
uv run --python 3.11 alembic upgrade head

cd ..
cd ..
sqlite3 -readonly database/polar-app.sqlite3   'SELECT version_num FROM alembic_version;'
