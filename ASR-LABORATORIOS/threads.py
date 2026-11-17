from multiprocessing import Process
from threading import Thread
from random import randint
from time import gmtime, sleep

shared_x = randint(10, 99)


def sleeping(name):
    global shared_x
    t = gmtime()
    s = randint(1, 20)
    print(f"{t.tm_min}:{t.tm_sec} {name} is going to sleep for {s} seconds", flush=True)
    sleep(s)
    t = gmtime()
    shared_x = shared_x + 1
    print(f"{t.tm_min}:{t.tm_sec} {name} has woken up, seeing shared_x being {shared_x}", flush=True)


def sleeper(name):
    print(name, "sees shared_x being", shared_x, flush=True)
    sleeplist = [Thread(target=sleeping, args=(name + " " + str(i),)) for i in range(3)]
    for thread in sleeplist:
        thread.start()
    for thread in sleeplist:
        thread.join()
    print(name, "sees shared_x being", shared_x, flush=True)


if __name__ == "__main__":
    p = Process(target=sleeper, args=("eve",))
    q = Process(target=sleeper, args=("bob",))
    p.start()
    q.start()
    p.join()
    q.join()
