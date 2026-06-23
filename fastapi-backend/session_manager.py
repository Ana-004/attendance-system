#Timer Engine

import redis
import json
from datetime import datetime
from config import settings

r = redis.from_url(settings.REDIS_URL)