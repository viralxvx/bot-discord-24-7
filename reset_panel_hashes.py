import redis
from config import REDIS_URL

def main():
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    contador = 0
    for key in redis_client.scan_iter("hash:*"):
        redis_client.delete(key)
        print(f"Borrado: {key}")
        contador += 1
    print(f"¡Listo! {contador} hash de paneles borrados.")

if __name__ == "__main__":
    main()
