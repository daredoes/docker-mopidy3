DOCKER_IMAGE=mopidy3
DOCKER_REPO=daredoes
TAG_NAME=develop

run:
	docker run -d \
    -p 3000:9001 \
    -p 6680:6680 \
    --privileged \
    -v /Users/dare/Git/docker-mopidy3/config:/config \
    $(DOCKER_REPO)/$(DOCKER_IMAGE)


build:
	docker build --platform=linux/amd64 -t $(DOCKER_REPO)/$(DOCKER_IMAGE) .
	# docker build --platform=linux/arm64 -t $(DOCKER_REPO)/$(DOCKER_IMAGE) .

push:
	docker tag $(DOCKER_REPO)/$(DOCKER_IMAGE) $(DOCKER_REPO)/$(DOCKER_IMAGE):$(TAG_NAME)
	docker push $(DOCKER_REPO)/$(DOCKER_IMAGE):$(TAG_NAME)

.PHONY: build push 
