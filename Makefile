.PHONY: help dev-up dev-down dev-migrate dev-test prod-up prod-down prod-migrate

# Environment variables
DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.dev.yml
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yml

help:  ## Show this help
	@echo "Dev Environment:"
	@awk 'BEGIN {FS = ":.*?## "} /^dev-[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "\nProd Environment:"
	@awk 'BEGIN {FS = ":.*?## "} /^prod-[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "\nGeneral:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && !/dev-|prod-/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## Development commands
dev-up:  ## Start dev environment with build
	$(DOCKER_COMPOSE_DEV) up --build

dev-down:  ## Stop dev environment
	$(DOCKER_COMPOSE_DEV) down

dev-migrate:  ## Run dev migrations
	$(DOCKER_COMPOSE_DEV) exec web python manage.py migrate

dev-createsuperuser:  ## Create dev superuser
	$(DOCKER_COMPOSE_DEV) exec web python manage.py createsuperuser

dev-test:  ## Run tests in dev
	$(DOCKER_COMPOSE_DEV) exec web python manage.py test --keepdb

dev-shell:  ## Open Django shell in dev
	$(DOCKER_COMPOSE_DEV) exec web python manage.py shell

## Production commands
prod-up:  ## Start prod environment
	$(DOCKER_COMPOSE_PROD) up --build -d

prod-down:  ## Stop prod environment
	$(DOCKER_COMPOSE_PROD) down

prod-migrate:  ## Run prod migrations
	$(DOCKER_COMPOSE_PROD) exec web python manage.py migrate --no-input

prod-collectstatic:  ## Collect static files in prod
	$(DOCKER_COMPOSE_PROD) exec web python manage.py collectstatic --no-input --clear

prod-restart:  ## Restart prod containers
	$(DOCKER_COMPOSE_PROD) restart

prod-logs:  ## View prod logs
	$(DOCKER_COMPOSE_PROD) logs -f

## General
clean:  ## Remove all unused containers and images
	docker system prune -f 