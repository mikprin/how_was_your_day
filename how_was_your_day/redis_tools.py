import time

# Defines
ALL_USERS = "_telegram_users_"
ACTIVE_USERS = "_active_users_"
GLOBAL_DATABASE_LOCK = "_global_database_lock_"
INTERACTION_TIMEOUT = 86400

# Functions
def add_user_to_redis(redis_connection, user):
    """Add user to redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.rpush(ALL_USERS, user)

def check_if_user_exists(redis_connection, user, collection):
    """Check if user exists in redis"""
    lst = redis_connection.lrange(collection, 0, -1)
    if user in lst:
        return True
    return False

def set_last_interaction(redis_connection, user, timestamp):
    """Set last interaction timestamp for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.set(f"{user}_last_interaction", timestamp)
    
def delete_outdated_interaction(redis_connection, user, timestamp):
    """Delete outdated interaction"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        if timestamp - int(redis_connection.get(f"{user}_last_interaction")) > INTERACTION_TIMEOUT:
            redis_connection.delete(f"{user}_last_interaction")
            redis_connection.delete(f"{user}_conversation")

def delete_interactions(redis_connection, user):
    """Delete interactions for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.delete(f"{user}_last_interaction")
        redis_connection.delete(f"{user}_conversation")
        redis_connection.lrem(ACTIVE_USERS, 0, user)

def add_conversation(redis_connection, user, conversation):
    """Add conversation to redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        if not check_if_user_exists(redis_connection, user, ACTIVE_USERS):
            redis_connection.rpush(ACTIVE_USERS, user)
            redis_connection.rpush(f"{user}_conversation", conversation)
        else:
            redis_connection.rpush(f"{user}_conversation", conversation)

def read_conversation(redis_connection, user):
    """Read conversation from redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        return redis_connection.lrange(f"{user}_conversation", 0, -1)

def databse_garbage_collector(redis_connection):
    """Delete outdated interactions"""
    current_time = int(time.time())
    active_users = redis_connection.lrange(ACTIVE_USERS, 0, -1)
    for user in active_users:
        delete_outdated_interaction(redis_connection, user, current_time)