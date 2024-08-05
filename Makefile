all: controller exporter miniserve

controller:
	cd ../jumpstarter-router && go run ./cmd/mock

exporter:
	sleep 3 && jmp exporter

miniserve:
	miniserve --interfaces 127.0.0.1 /home/nickcao/Downloads
