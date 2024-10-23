#!/bin/bash

rm /home/user01/mees/Cloud/Results/*
rm /home/user01/mees/Fog/Results/*
rm /home/user01/mees/Edge/Results/*
rm /home/user01/mees/Cloud/nohup*
rm /home/user01/mees/Fog/nohup*
rm /home/user01/mees/Edge/nohup*
rm /home/user01/mees/Wrapper/nohup*

python3.12 -m pip install -r requirements.txt

declare -a APP_PIDS=()

(
  cd /home/user01/mees/Cloud
  export $(grep -v '^#' .env | tr -d '\r' | xargs)
  nohup python3.12 manage.py runserver 0.0.0.0:8200 &
   APP_PID=$!

  APP_PIDS+=($APP_PID)
)

sleep 10

for i in {0..19}; do
    PROCESSOR_TYPE=$((i % 4))
    PORT=$((8100 + i))

    cd /home/user01/mees/Fog
    export $(grep -v '^#' .env | tr -d '\r' | xargs)
    nohup env ADDRESS="localhost:$PORT" PROCESSOR_TYPE="$PROCESSOR_TYPE" python3.12 manage.py runserver 0.0.0.0:$PORT &> nohup$i.out &
     APP_PID=$!

    APP_PIDS+=($APP_PID)
done

sleep 10

for i in {0..89}; do
    PROCESSOR_TYPE=$((i % 7))
    PORT=$((8000 + i))

    cd /home/user01/mees/Edge
    export $(grep -v '^#' .env | tr -d '\r' | xargs)
    nohup env ADDRESS="localhost:$PORT" PROCESSOR_TYPE="$PROCESSOR_TYPE" python3.12 manage.py runserver 0.0.0.0:$PORT &> nohup$i.out &
     APP_PID=$!

    APP_PIDS+=($APP_PID)
done

sleep 10

cd /home/user01/mees/Wrapper
export env CLOUD_ADDRESS="localhost:8200"
python main.py

wait $!

for PID in "${APP_PIDS[@]}"; do
  kill $PID
done