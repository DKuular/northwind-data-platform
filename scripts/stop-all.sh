cd servers/server-01-oltp && docker compose down && cd ../..
cd servers/server-02-kafka && docker compose down && cd ../..
cd servers/server-03-kafka-connect && docker compose down && cd ../..
cd servers/server-04-spark && docker compose down && cd ../..
cd servers/server-05-storage && docker compose down && cd ../..
cd servers/server-06-quality && docker compose down && cd ../..
cd servers/server-07-catalog && docker compose down && cd ../..
cd servers/server-08-ml && docker compose down && cd ../..