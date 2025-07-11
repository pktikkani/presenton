#!/bin/bash

echo "Starting production server..."

service nginx start
service redis-server start
node /app/start.js
