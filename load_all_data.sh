#!/bin/bash
echo "Starting data loading process..."
echo "Loading inventory data..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_inventory_data
echo "Loading raw materials..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_raw_materials
echo "Loading standard parts..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_standard_parts
echo "Loading single parts..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_single_parts
echo "Loading montaged products..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_montaged_products
echo "Loading semi-finished products..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_semi_finished_products
echo "Loading manufacturing processes..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_processes
echo "Loading machines..."
docker compose -f docker-compose.dev.yml exec web python manage.py load_machines
echo "Data loading completed!"
