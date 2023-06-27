.PHONY: all build
FILE=genload.go

build:
	go build -o $(FILE)

docker: build
	docker build --rm -t $(FILE):alpha .

all: build
