import dns_packer
import dns_unpacker
from logger import logger
from config import config
import random
import socket
import time
import multiprocessing
from ctypes import Structure, c_double, c_int
from multiprocessing.sharedctypes import Value, Array

def current_time():

    ## get microsecond

    return time.time() * 1000

class Response_type(Structure):
    _fields_ = [("send_start", c_double), ("send_end", c_double), ("recv_start", c_double), ("recv_end", c_double), ("err_count", c_int)]

def worker(process_id, server, port, domain, request_num, responses, start_signal, timeout):
    
    ## init

    logger.info("Worker %d starts, task: %s, %d, %s, %d" % (process_id, server, port, domain, request_num))
    sockets = []
    for i in range(request_num):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0) # non-blocking
        tid = random.randint(-32768, 32767)
        msg = dns_packer.pack(tid, domain)
        sockets.append((sock, msg))

    ## ensure threads start send packages together
        
    with start_signal.get_lock():
        start_signal.value -= 1

    while start_signal.value > 0:
        pass

    ## main work
    
    logger.info("Worker %d init finished, task: %s, %d, %s, %d" % (process_id, server, port, domain, request_num))
    error_num = 0
    send_start = current_time()
    count = request_num
    for sock, msg in sockets:
        sock.sendto(msg, (server, port))
    send_end = current_time()
    receive_start = -1
    receive_end = -1
    i = 0
    finished = [False for i in range(request_num)]
    while count > 0 :
        try:
            if not finished[i]:
                c = sockets[i][0].recv(4096)
                tid, err_msg = dns_unpacker.dns_unpack(c)
                if err_msg != 0:
                    error_num += 1
                receive_end = current_time()
                if receive_start < 0:
                    receive_start = receive_end
                finished[i] = True
                count -= 1
        except socket.error:

            ## handle timeout
            
            if send_end + timeout < current_time():
                error_num += 1
                finished[i] = True
                count -= 1
        finally:
            i = (i + 1) % request_num

    ## aggregate
    
    error_rate = float(error_num) / request_num
    time_cost = str(receive_end - send_start) if error_rate < 1 else "N/A"
    logger.info("Worker %d ends, time_cost: %s ms, error_rate: %f " % (process_id, time_cost, error_rate))
    with responses.get_lock():
        responses[process_id].err_count += error_num
        responses[process_id].send_start = send_start
        responses[process_id].send_end = send_end
        responses[process_id].recv_start = receive_start
        responses[process_id].recv_end = receive_end

if __name__ == "__main__":

    ## reading config
    
    server = config.get("basic", "server") if config.has_option("basic", "server") else "127.0.0.1"
    port = config.getint("basic", "port") if config.has_option("basic", "port") else 53
    threads = config.getint("basic", "threads") if config.has_option("basic", "threads") else 1
    domain = config.get("basic", "domain") if config.has_option("basic", "domain") else "test.test.com"
    request_num = config.getint("basic", "request_num") if config.has_option("basic", "request_num") else 10
    timeout = config.getint("basic", "timeout") if config.has_option("basic", "timeout") else 10000 # microsecond
    logger.info("Dns Benchmark starts, task: %s : %d, %s, %d * %d" % (server, port, domain, threads, request_num))
    print "Dns Benchmark starts, task: %s : %d, %s, %d * %d" % (server, port, domain, threads, request_num)
    
    ## init sockets
    
    print "init"
    processes = []
    start_signal = Value('d', threads, lock = True)

    ## start processings
    
    print "start"
    responses = Array(Response_type, threads, lock = True)
    for i in range(threads):
        process = multiprocessing.Process(target = worker, args = (i, server, port, domain, request_num, responses, start_signal, timeout))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
    
    ## aggregate results

    print "aggregate"
    now = current_time()
    send_start = reduce(lambda x, y: min(x, y.send_start), responses, now)
    send_end = reduce(lambda x, y: max(x, y.send_end), responses, 0)
    receive_start = reduce(lambda x, y: min(x, y.recv_start), filter(lambda x: x.recv_start > 0, responses), now)
    receive_end = reduce(lambda x, y: max(x, y.recv_end), filter(lambda x: x.recv_end > 0, responses), 0)
    err_count = reduce(lambda x, y: x + y.err_count, responses, 0)

    total = threads * request_num
    time_cost = str(receive_end - send_start) if receive_end > send_start else "N/A"
    err_rate = str(float(err_count) / total) if total > 0 else "N/A"
    print "time cost: %s ms, err rate: %s" % (time_cost, err_rate)
    logger.info("Dns Benchmark ends, time_cost: %s ms, err_rate: %s" % (time_cost, err_rate))
    print "send start: %f, send end: %f, recv start: %f, recv end: %f" % (send_start, send_end, receive_start, receive_end)
    logger.info("send start: %f, send end: %f, recv start: %f, recv end: %f" % (send_start, send_end, receive_start, receive_end))

