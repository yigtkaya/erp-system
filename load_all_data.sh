#!/bin/bash
echo "Starting data loading process..."

echo "Loading customers..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_customers

echo "Loading inventory data..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_inventory_data

echo "Loading raw materials..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_raw_materials

echo "Loading standard parts..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_standard_parts

echo "Loading single parts..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_single_parts

echo "Loading montaged products..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_montaged_products

echo "Loading semi-finished products..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_semi_finished_products

echo "Loading manufacturing processes..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_processes

echo "Loading machines..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_machines

echo "Copying orders CSV file to container..."
docker cp data/orders.csv $(docker compose -f docker-compose.prod.yml ps -q web):/home/app/web/orders.csv

echo "Loading orders..."
docker compose -f docker-compose.prod.yml exec web python manage.py load_orders /home/app/web/orders.csv

echo "Data loading completed!"
