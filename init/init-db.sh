#!/bin/bash
set -e

NEURALGRAPH_URL="${NEURALGRAPH_URL:-http://localhost:3000}"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

execute_query() {
    local query="$1"
    response=$(curl -s -X POST "${NEURALGRAPH_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "{\"query\": $(echo "$query" | jq -Rs .)}")
    
    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        return 0
    else
        echo "$response" | jq -r '.error // "Unknown error"'
        return 1
    fi
}

log_info "Initializing Newsletter Schema..."

# Create topics
log_info "Creating topics..."
execute_query 'CREATE (t:Topic {name: "Rust", slug: "rust", description: "Rust programming language"})'
execute_query 'CREATE (t:Topic {name: "Graph Databases", slug: "graph-databases", description: "Graph data modeling and queries"})'
execute_query 'CREATE (t:Topic {name: "AI/ML", slug: "ai-ml", description: "Artificial intelligence and machine learning"})'
execute_query 'CREATE (t:Topic {name: "Performance", slug: "performance", description: "Optimization and benchmarking"})'
execute_query 'CREATE (t:Topic {name: "Distributed Systems", slug: "distributed-systems", description: "Distributed computing and consensus"})'
execute_query 'CREATE (t:Topic {name: "Vector Search", slug: "vector-search", description: "Similarity search and embeddings"})'

log_info "Schema initialized!"

# Verify
log_info "Verifying..."
curl -s -X POST "${NEURALGRAPH_URL}/api/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "MATCH (t:Topic) RETURN t.name, t.slug"}' | jq

log_info "Done!"
