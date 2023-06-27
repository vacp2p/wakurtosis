# Specify the parent go version
FROM golang:1.20

# Copy the binary and the source code
ADD ./genload /go/bin/genload
ADD ./genload.go /go/src/genload.go

# add mod deps and an output directory
ADD go.mod go.sum /go/src/
RUN mkdir -p /go/bin/output

EXPOSE 8080

ENTRYPOINT [ "/go/bin/genload" ]
