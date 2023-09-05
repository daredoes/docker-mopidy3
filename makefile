DOCKER_IMAGE=mopidy3
DOCKER_REPO=daredoes
TAG_NAME=stable
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

fresh-run:
	docker run -d \
    -p 9001:9001 \
    -p 6680:6680 \
    -p 6600:6600 \
    -p 4953:4953 \
    -p 731:731 \
    -v $(ROOT_DIR)/music:/media \
    $(DOCKER_REPO)/$(DOCKER_IMAGE)

run:
	docker run -d \
    -p 9001:9001 \
    -p 6680:6680 \
    -p 6600:6600 \
    -p 4954:4954 \
    -p 731:731 \
    -v $(ROOT_DIR)/web.py:/web.py \
    -v $(ROOT_DIR)/cache:/home/cache \
    -v $(ROOT_DIR)/config:/etc/mopidy \
    -v $(ROOT_DIR)/share:/home/.local/share/mopidy \
    -v $(ROOT_DIR)/data:/data \
    -v $(ROOT_DIR)/music:/media \
    $(DOCKER_REPO)/$(DOCKER_IMAGE)


build:
	docker build --platform=linux/amd64 -t $(DOCKER_REPO)/$(DOCKER_IMAGE) .
	# docker build --platform=linux/arm64 -t $(DOCKER_REPO)/$(DOCKER_IMAGE) .

push:
	docker tag $(DOCKER_REPO)/$(DOCKER_IMAGE) $(DOCKER_REPO)/$(DOCKER_IMAGE):$(TAG_NAME)
	docker push $(DOCKER_REPO)/$(DOCKER_IMAGE):$(TAG_NAME)

.PHONY: build push 
