FROM continuumio/miniconda3
ENV PYTHONUNBUFFERED 1

# copy conda spec to beuild invironment
COPY ./environment.yaml /tmp/environment.yaml
COPY ./efu_app /efu_app
WORKDIR /efu_app

# expose port 8000 when we run a container
EXPOSE 8000

# environment variable
# in command line override variable
# example:
#   docker build --build_arg DEV=true .
ARG BUILD_TYPE=0

SHELL ["/bin/bash", "--login", "-c"]

RUN python --version

# create environment
RUN conda env create -f /tmp/environment.yaml

RUN echo "source activate py39dj_dk" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

#ENV PATH /scripts:/opt/conda/envs/py39dj_dk/bin:$PATH
ENV PATH /opt/conda/envs/py39dj_dk/bin:$PATH

RUN echo "$PATH"

RUN rm -rf /tmp

RUN adduser --disabled-password  --no-create-home django-user

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
RUN chown -R django-user:django-user /vol
RUN chmod -R 755 /vol
#RUN chmod -R +x /scripts

USER django-user

