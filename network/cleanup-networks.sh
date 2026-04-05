#!/bin/bash

echo "🧹 Cleaning up networks..."

networks="oltp-network kafka-network connect-network spark-network storage-network quality-network catalog-network ml-network data-platform-network"

for network in $networks; do
    if docker network inspect "$network" >/dev/null 2>&1; then
        docker network rm "$network"
        echo "  ✅ Removed $network"
    else
        echo "  ⚠️  Network $network not found"
    fi
done

echo "✅ Cleanup complete"
