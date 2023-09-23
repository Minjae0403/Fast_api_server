# 나의 python 버전
FROM python:3.11.4

# 작업 장소 지정
WORKDIR /usr/src

RUN apt-get -y update
RUN apt install wget
RUN apt install unzip
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt -y install ./google-chrome-stable_current_amd64.deb
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/` curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN mkdir chrome
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/src/chrome

# ./requirements.txt 를 /requirements.txt 로 복사
COPY ./requirements.txt /requirements.txt

# requirements.txt 를 보고 모듈 전체 설치(-r)
RUN pip install --no-cache-dir -r /requirements.txt

# 이제 app 에 있는 파일들을 /app 에 복사
COPY ./app /app
COPY ./private /private

EXPOSE 3000

WORKDIR /app

# 실행
CMD ["uvicorn", "Crawling_app.py:app", "--host", "0.0.0.0", "--port", "3000"]