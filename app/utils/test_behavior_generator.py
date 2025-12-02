#!/usr/bin/env python3
"""
Test Data Generator for User Behavior Classification
====================================================
Generate diverse user behavior patterns để test classification logic
"""

import json
import random
import time
import sys
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

def create_producer(bootstrap_servers='localhost:9092', max_retries=5):
    """Create Kafka producer with retry logic"""
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print(f"✅ Connected to Kafka at {bootstrap_servers}")
            return producer
        except NoBrokersAvailable:
            if attempt < max_retries - 1:
                print(f"⏳ Waiting for Kafka... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print("❌ Failed to connect to Kafka")
                raise

def generate_bouncer_session(user_id, session_id, base_time):
    """
    🔴 Bouncer: 1-2 events, < 1 minute
    Insight: Landing page không hấp dẫn? Sai target audience?
    """
    events = []
    timestamp = base_time
    
    # Very few events (1-2)
    event_count = random.randint(1, 2)
    
    for i in range(event_count):
        events.append({
            "event_time": (timestamp + timedelta(seconds=i * 10)).isoformat(),
            "event_type": "view",
            "product_id": random.randint(1001000, 1001100),
            "category_id": random.choice([2053013555631882655, 2053013558920217191]),
            "category_code": random.choice([
                "electronics.smartphone",
                "appliances.kitchen.refrigerators"
            ]),
            "brand": random.choice(["samsung", "apple", "xiaomi"]),
            "price": round(random.uniform(50, 200), 2),
            "user_id": user_id,
            "user_session": session_id
        })
    
    return events

def generate_browser_session(user_id, session_id, base_time):
    """
    🟡 Browser: 3-10 events, 1-10 minutes, cart but no purchase
    Insight: Thiếu trust? Giá cao? So sánh competitor?
    """
    events = []
    timestamp = base_time
    
    # Multiple views (3-10)
    view_count = random.randint(3, 10)
    viewed_products = []
    
    for i in range(view_count):
        product_id = random.randint(1001000, 1001200)
        viewed_products.append(product_id)
        
        events.append({
            "event_time": (timestamp + timedelta(minutes=i * 0.8)).isoformat(),
            "event_type": "view",
            "product_id": product_id,
            "category_id": random.choice([2053013555631882655, 2053013558920217191]),
            "category_code": random.choice([
                "electronics.smartphone",
                "electronics.tablet",
                "electronics.audio.headphone"
            ]),
            "brand": random.choice(["samsung", "apple", "xiaomi", "huawei"]),
            "price": round(random.uniform(100, 500), 2),
            "user_id": user_id,
            "user_session": session_id
        })
    
    # Add to cart (1-3 items) but NO purchase
    cart_count = random.randint(1, min(3, len(viewed_products)))
    for product_id in random.sample(viewed_products, cart_count):
        events.append({
            "event_time": (timestamp + timedelta(minutes=view_count * 0.8 + 1)).isoformat(),
            "event_type": "cart",
            "product_id": product_id,
            "category_id": 2053013555631882655,
            "category_code": "electronics.smartphone",
            "brand": "samsung",
            "price": round(random.uniform(100, 500), 2),
            "user_id": user_id,
            "user_session": session_id
        })
    
    return events

def generate_engaged_shopper_session(user_id, session_id, base_time):
    """
    🟢 Engaged Shopper: 10-30 events, 10-30 minutes, multiple carts + purchases
    Insight: Target customer lý tưởng - cần nurture
    """
    events = []
    timestamp = base_time
    
    event_count = random.randint(10, 30)
    viewed_products = []
    
    # Generate diverse events
    for i in range(event_count):
        product_id = random.randint(1001000, 1001300)
        
        # Weighted event types: 60% view, 25% cart, 15% purchase
        event_type = random.choices(
            ["view", "cart", "purchase"],
            weights=[60, 25, 15]
        )[0]
        
        if event_type == "view":
            viewed_products.append(product_id)
        
        events.append({
            "event_time": (timestamp + timedelta(minutes=i * 0.9)).isoformat(),
            "event_type": event_type,
            "product_id": product_id,
            "category_id": random.choice([
                2053013555631882655,
                2053013558920217191,
                2053013554415534427
            ]),
            "category_code": random.choice([
                "electronics.smartphone",
                "electronics.tablet",
                "appliances.kitchen.washer",
                "computers.notebook"
            ]),
            "brand": random.choice(["samsung", "apple", "lg", "hp"]),
            "price": round(random.uniform(50, 800), 2),
            "user_id": user_id,
            "user_session": session_id
        })
    
    return events

def generate_power_user_session(user_id, session_id, base_time):
    """
    🔵 Power User: 30+ events, 30+ minutes, multiple purchases, cross-category
    Insight: VIP customer - cần loyalty program
    """
    events = []
    timestamp = base_time
    
    event_count = random.randint(30, 50)
    
    # High purchase rate (20% of events)
    for i in range(event_count):
        product_id = random.randint(1001000, 1001500)
        
        # Event type distribution: 50% view, 30% cart, 20% purchase
        event_type = random.choices(
            ["view", "cart", "purchase"],
            weights=[50, 30, 20]
        )[0]
        
        # Cross-category browsing (VIP explores more)
        category_code = random.choice([
            "electronics.smartphone",
            "electronics.tablet",
            "electronics.audio.headphone",
            "computers.notebook",
            "appliances.kitchen.washer",
            "appliances.kitchen.refrigerators",
            "electronics.video.tv"
        ])
        
        events.append({
            "event_time": (timestamp + timedelta(minutes=i * 1.2)).isoformat(),
            "event_type": event_type,
            "product_id": product_id,
            "category_id": random.choice([
                2053013555631882655,
                2053013558920217191,
                2053013554415534427,
                2053013565983425517
            ]),
            "category_code": category_code,
            "brand": random.choice(["samsung", "apple", "lg", "sony", "hp", "dell"]),
            "price": round(random.uniform(100, 1500), 2),
            "user_id": user_id,
            "user_session": session_id
        })
    
    return events

def main():
    """Generate test behavior patterns"""
    
    # Parse arguments
    bootstrap_servers = sys.argv[1] if len(sys.argv) > 1 else 'localhost:9092'
    topic = sys.argv[2] if len(sys.argv) > 2 else 'ecommerce_events'
    
    print("=" * 70)
    print("🧪 USER BEHAVIOR TEST DATA GENERATOR")
    print("=" * 70)
    print(f"Kafka Server: {bootstrap_servers}")
    print(f"Topic: {topic}")
    print("")
    
    # Create producer
    producer = create_producer(bootstrap_servers)
    
    # Session generators with target counts
    generators = [
        (generate_bouncer_session, "bouncer", "🔴", 15),
        (generate_browser_session, "browser", "🟡", 15),
        (generate_engaged_shopper_session, "engaged_shopper", "🟢", 10),
        (generate_power_user_session, "power_user", "🔵", 8)
    ]
    
    total_events = 0
    base_time = datetime.now()
    
    for generator, segment_name, emoji, count in generators:
        print(f"\n{emoji} Generating {count} {segment_name.upper()} sessions...")
        
        for i in range(count):
            user_id = random.randint(100000, 999999)
            session_id = f"{segment_name}_{user_id}_{int(time.time())}_{i}"
            
            # Generate events for this session
            session_time = base_time + timedelta(seconds=random.randint(0, 300))
            events = generator(user_id, session_id, session_time)
            
            # Send events to Kafka
            for event in events:
                producer.send(topic, value=event)
                total_events += 1
            
            print(f"  ✓ User {user_id}: {len(events)} events (session: {session_id[:30]}...)")
            
            # Small delay between sessions
            time.sleep(0.2)
    
    # Flush producer
    producer.flush()
    producer.close()
    
    print("\n" + "=" * 70)
    print(f"✅ Generated {total_events} events from {sum(g[3] for g in generators)} sessions")
    print("=" * 70)
    print("\nBreakdown:")
    for generator, segment_name, emoji, count in generators:
        print(f"  {emoji} {segment_name.capitalize()}: {count} sessions")
    
    print("\n💡 Next steps:")
    print("  1. Wait ~30 seconds for Spark to process")
    print("  2. Run: ./deploy/scripts/query_behavior_segments.sh")
    print("  3. Check MongoDB for classified segments")

if __name__ == "__main__":
    main()
