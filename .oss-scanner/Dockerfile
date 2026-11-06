FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# The scanner expects the complete checkout at /src. All installation and
# building happens here, while network access is still available.
WORKDIR /src
COPY . /src
RUN python -m pip install --no-cache-dir -c .oss-scanner/constraints.txt -e ".[dev]" build hatchling \
    && python -m build --no-isolation --outdir /opt/tabulint-dist \
    && python -m pytest -q \
    && python -m mypy

CMD ["bash"]
