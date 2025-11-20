#!/bin/bash

# Kafka Topics Setup Script
# Creates and configures all necessary Kafka topics for the crypto-viz streaming architecture

set -e

KAFKA_CONTAINER="crypto-viz-kafka"
KAFKA_BOOTSTRAP_SERVER="localhost:9092"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Kafka Topics Setup for Crypto Visualization ===${NC}"

# Function to check if Kafka is ready
check_kafka_ready() {
    echo -e "${YELLOW}Checking if Kafka is ready...${NC}"
    
    for i in {1..30}; do
        if docker exec $KAFKA_CONTAINER kafka-broker-api-versions --bootstrap-server $KAFKA_BOOTSTRAP_SERVER > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Kafka is ready${NC}"
            return 0
        fi
        echo "Waiting for Kafka... ($i/30)"
        sleep 2
    done
    
    echo -e "${RED}✗ Kafka is not ready after 60 seconds${NC}"
    exit 1
}

# Function to create a topic if it doesn't exist
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication_factor=$3
    local retention_ms=$4
    local cleanup_policy=$5
    
    echo -e "${YELLOW}Creating topic: ${topic_name}${NC}"
    
    # Check if topic already exists
    if docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA_BOOTSTRAP_SERVER --list | grep -q "^${topic_name}$"; then
        echo -e "${GREEN}✓ Topic '${topic_name}' already exists${NC}"
        
        # Update topic configuration if needed
        if [[ -n "$retention_ms" ]]; then
            docker exec $KAFKA_CONTAINER kafka-configs --bootstrap-server $KAFKA_BOOTSTRAP_SERVER \
                --entity-type topics --entity-name $topic_name \
                --alter --add-config retention.ms=$retention_ms,cleanup.policy=$cleanup_policy
            echo -e "${GREEN}✓ Updated configuration for '${topic_name}'${NC}"
        fi
    else
        # Create the topic
        local config_args=""
        if [[ -n "$retention_ms" ]]; then
            config_args="--config retention.ms=$retention_ms --config cleanup.policy=$cleanup_policy"
        fi
        
        docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA_BOOTSTRAP_SERVER \
            --create --topic $topic_name \
            --partitions $partitions \
            --replication-factor $replication_factor \
            $config_args
        
        echo -e "${GREEN}✓ Created topic '${topic_name}' with ${partitions} partitions${NC}"
    fi
}

# Function to display topic information
show_topic_info() {
    local topic_name=$1
    echo -e "${YELLOW}Topic Info: ${topic_name}${NC}"
    docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA_BOOTSTRAP_SERVER \
        --describe --topic $topic_name
    echo ""
}

# Main setup
main() {
    check_kafka_ready
    
    echo -e "${GREEN}Creating Kafka topics...${NC}"
    
    # 1. crypto-news topic - for news data with 7 days retention
    create_topic "crypto-news" 3 1 "604800000" "delete"  # 7 days in milliseconds
    
    # 2. crypto-prices topic - for price data with optimized partitioning (6 partitions for better throughput)
    create_topic "crypto-prices" 6 1 "2592000000" "delete"  # 30 days retention
    
    # 3. analytics-data topic - for processed analytics data
    create_topic "analytics-data" 3 1 "1209600000" "delete"  # 14 days retention
    
    # 4. alerts topic - for system alerts and notifications
    create_topic "alerts" 2 1 "259200000" "delete"  # 3 days retention
    
    # 5. Additional topics that might be useful for the crypto streaming architecture
    
    # Dead letter queue for failed messages
    create_topic "dlq-crypto-news" 1 1 "604800000" "delete"  # 7 days retention
    create_topic "dlq-crypto-prices" 1 1 "604800000" "delete"  # 7 days retention
    
    # Audit/logging topic for system monitoring
    create_topic "system-logs" 2 1 "2592000000" "delete"  # 30 days retention
    
    echo -e "${GREEN}=== Topics Created Successfully ===${NC}"
    
    # Display all topics
    echo -e "${YELLOW}Listing all topics:${NC}"
    docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA_BOOTSTRAP_SERVER --list
    echo ""
    
    # Show detailed information for main topics
    show_topic_info "crypto-news"
    show_topic_info "crypto-prices"
    show_topic_info "analytics-data"
    show_topic_info "alerts"
    
    echo -e "${GREEN}=== Kafka Topics Setup Complete ===${NC}"
    echo -e "${YELLOW}Access Kafka UI at: http://localhost:8081${NC}"
}

# Run main function
main "$@"