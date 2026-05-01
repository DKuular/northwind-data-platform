cd servers/server-01-oltp && docker compose up -d && cd ../..
cd servers/server-02-kafka && docker compose up -d && cd ../..
cd servers/server-03-kafka-connect && docker compose up -d && cd ../..
#cd servers/server-04-spark && docker compose up -d && cd ../..
cd servers/server-05-storage && docker compose up -d && cd ../..
#cd servers/server-06-quality && docker compose up -d && cd ../..
#cd servers/server-07-catalog && docker compose up -d && cd ../..
#cd servers/server-08-ml && docker compose up -d && cd ../..