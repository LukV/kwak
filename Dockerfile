FROM python:3.13-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app

# Install dependencies
RUN uv venv --python=python3.13 \
    && .venv/bin/uv sync --frozen --no-cache

# Add .venv to PATH and make kwak CLI the default entry
ENV PATH="/app/.venv/bin:$PATH"

# Default command (can be overridden)
ENTRYPOINT ["kwak"]
CMD ["--help"]


# RUN uv sync --frozen --no-cache

# # Run the application.
# CMD ["/app/.venv/bin/fastapi", "run", "src/api/app.py", "--port", "80"]
