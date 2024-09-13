FROM --platform=linux/x86_64 public.ecr.aws/compfuzzci/compfuzzci-base:latest
ARG COMMIT

# Install Dafny
RUN git clone https://github.com/dafny-lang/dafny.git
RUN cd dafny && \
    git checkout ${COMMIT}\
    make exe && \
    make z3-ubuntu

# Prepare for fuzzing
RUN chmod +x entrypoint.sh
ENV PATH="/compfuzzci/dafny/Scripts:${PATH}"

ENTRYPOINT ["/compfuzzci/entrypoint.sh"]