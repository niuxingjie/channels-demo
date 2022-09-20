FROM python:3.8.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1 
WORKDIR /channels_demo
COPY .  /channels_demo/
RUN apt-get update \
    && apt-get install gcc libpq-dev git vim -y \
    && git config pull.ff only \
    && python -m pip install --upgrade pip \
    && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]