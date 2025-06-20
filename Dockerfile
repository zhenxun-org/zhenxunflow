FROM python:3.11 as requirements-stage

WORKDIR /tmp

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py

# 安装指定版本的Poetry 1.x (1.6.1是稳定的版本)
RUN python install-poetry.py --version 1.6.1 --yes

ENV PATH="${PATH}:/root/.local/bin"

# 确认Poetry版本
RUN poetry --version

# 使用Poetry安装依赖，然后用pip freeze生成requirements.txt
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi \
    && pip freeze > requirements.txt

FROM python:3.11-slim-bullseye

# 设置时区
ENV TZ=Asia/Shanghai

# 安装依赖
COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt
RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install -y --no-install-recommends git \
  && pip install --no-cache-dir --upgrade -r /app/requirements.txt \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/* \
  && rm /app/requirements.txt

COPY bot.py .env /app/
COPY src /app/src/

CMD ["python", "/app/bot.py"]
