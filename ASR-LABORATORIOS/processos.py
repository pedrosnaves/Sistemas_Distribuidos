from multiprocessing import Process
from random import randint
from time import gmtime, sleep


def sleeper(name):
    t = gmtime()
    s = randint(1, 20)
    print(f"{t.tm_min}:{t.tm_sec} {name} is going to sleep for {s} seconds", flush=True)
    sleep(s)
    t = gmtime()
    print(f"{t.tm_min}:{t.tm_sec} {name} has woken up", flush=True)


if __name__ == "__main__":
    p = Process(target=sleeper, args=("eve",))
    q = Process(target=sleeper, args=("bob",))
    p.start()
    q.start()
    p.join()
    q.join()
