FROM python:3.11 as requirements-stage

WORKDIR /tmp

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py

# 安装最新版本的Poetry 2.x
RUN python install-poetry.py --yes

ENV PATH="${PATH}:/root/.local/bin"

# 确认Poetry版本
RUN poetry --version

# 安装export插件（Poetry 2.x需要单独安装这个插件）
RUN poetry self add poetry-plugin-export

# 导出依赖
RUN poetry export --output requirements.txt --without-hashes

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
