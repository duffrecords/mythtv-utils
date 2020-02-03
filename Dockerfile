FROM lambci/lambda:build-python3.6 AS builder

COPY app .
COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pwd && ls -l

FROM lambci/lambda:python3.6

ENV HANDLE_ALL_EXCEPTIONS false
ENV LOG_ALL_EVENTS true
ENV disable_hevc true
ENV ideal_hd_movie_size 10.5,17
ENV ideal_hd_tv_show_size 8,17
ENV ideal_movie_size 4,9
ENV ideal_tv_show_size 0.7,1.5
ENV log_level debug
ENV strict_movie_size 1,17
ENV strict_tv_show_size 0.12,17
ENV transmission_host 10.0.0.210
ENV transmission_password password
ENV transmission_user transmission

COPY --from=builder app .

RUN pwd && ls -l