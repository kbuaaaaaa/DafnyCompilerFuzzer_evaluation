FROM --platform=linux/x86_64 public.ecr.aws/compfuzzci/compfuzzci-base:latest
COPY entrypoint.sh /compfuzzci/entrypoint.sh
WORKDIR /compfuzzci
ARG COMMIT

RUN git clone https://github.com/dafny-lang/dafny.git

RUN cd dafny && git checkout ${COMMIT}

RUN cd dafny && make exe

RUN cd dafny && make z3-ubuntu

RUN mkdir data

RUN chmod +x entrypoint.sh

ENV PATH="/compfuzzci/dafny/Scripts:${PATH}"
ENV PATH="/root/go/bin:${PATH}"
ENV PATH="/root/.cargo/bin:${PATH}"

ENTRYPOINT ["/compfuzzci/entrypoint.sh"]