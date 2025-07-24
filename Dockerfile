FROM python:3.12-slim


ENV TZ=Europe/Moscow


WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv pip install --system --no-cache -r pyproject.toml

COPY . .

CMD ["python", "bot.py"]
