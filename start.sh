#!/bin/sh

# Script para arrancar redis y el servidor al mismo tiempo
redis-server &
python main.py