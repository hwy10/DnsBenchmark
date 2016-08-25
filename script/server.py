from logger import logger
from config import config
from Queue import Queue
from manager import DnsBenchmarkManager
import manager
import time
import subprocess
import shlex

def current_time():
    
    ## get microsecond

    return time.time() * 1000

if __name__ == "__main__":
    logger.info("Dns Benchmark server starts")
    
    ## fetch ip list

    ip_list = []
    if config.has_option("basic", "ip_list_filename"):
        ip_list_filename = config.get("basic", "ip_list_filename")
        with open(ip_list_filename, 'r') as ip_list_file:
            ips = ip_list_file.readlines()
            for ip in ips:
                ip_list.append(ip)
    else:
        ip_list = ['127.0.0.1']

    ## fetch configs

    ip = config.get("server", "ip") if config.has_option("server", "ip") else "127.0.0.1"
    port = config.getint("server", "port") if config.has_option("server", "port") else 50000
    authkey = config.get("server", "authkey") if config.has_option("server", "authkey") else "secret"
    
    address = (ip, port)

    ## start server

    server = DnsBenchmarkManager(address=('', port), authkey=authkey)
    
    # manager.task = server.dict()
    manager.task = {}
    manager.task['server'] = config.get("target", "server") if config.has_option("target", "server") else "127.0.0.1"
    manager.task['port'] = config.getint("target", "port") if config.has_option("target", "port") else 53
    manager.task['threads'] = config.getint("basic", "threads") if config.has_option("basic", "threads") else 1
    manager.task['domain'] = config.get("basic", "domain") if config.has_option("basic", "domain") else "test.test.com"
    manager.task['request_num'] = config.getint("basic", "request_num") if config.has_option("basic", "request_num") else 10
    manager.task['timeout'] = config.getint("basic", "timeout") if config.has_option("basic", "timeout") else 10000 # microsecond
    manager.ready_count.init(len(ip_list))

    server.start()
    
    logger.info("Dns Benchmark starts, task: %s : %d, %s, %d * %d" % (manager.task['server'], manager.task['port'], manager.task['domain'], manager.task['threads'], manager.task['request_num']))
    print "Dns Benchmark starts, task: %s : %d, %s, %d * %d" % (manager.task['server'], manager.task['port'], manager.task['domain'], manager.task['threads'], manager.task['request_num'])

    logger.info("Dns Benchmark server starts, address: %s, port: %d" % (ip, port))
    print "Dns Benchmark server starts, address: %s, port: %d" % (ip, port)
    
    ## start organizer

    organizer = DnsBenchmarkManager(address=address, authkey=authkey)
    organizer.connect()

    logger.info("Dns Benchmark organizer starts, address: %s, port: %d" % (ip, port))
    print "Dns Benchmark organizer starts, address: %s, port: %d" % (ip, port)
    client_count = len(ip_list)

    ## ssh to clents

    ssh_user = config.get('basic', 'ssh_user') if config.has_option('basic', 'ssh_user') else 'dnsbenchmark'
    image_name = config.get('basic', 'image_name') if config.has_option('basic', 'image_name') else 'hwy10/dnsbenchmark'
    work_file = config.get('basic', 'work_file') if config.has_option('basic', 'work_file') else '/DNSBenchmark/script/client.py'
    sp_list = []

    for client_ip in ip_list:
        client_ip = client_ip.strip()
        if client_ip == '':
            continue
        print "connecting %s@%s" % (ssh_user, client_ip)
        command = "ssh %s@%s docker pull %s; docker run %s python %s %s %s %s" % (ssh_user, client_ip, image_name, image_name, work_file, ip, port, authkey)
        sp_list.append(subprocess.Popen(shlex.split(command)))

    while True:
        count = 0
        for sp in sp_list:
            if sp.poll() is not None:
                count += 1
        if count == client_count:
            break

    count = 0
    for sp in sp_list:
        if sp.poll() == 0:
            count += 1
    
    ready_count = organizer.get_ready_count()
    for i in range(client_count - count):
        ready_count.set(-1)

    logger.info("task hand over finished, success %d/%d" % (count, client_count))
    print "task hand over finished, success %d/%d" % (count, client_count)

    client_count = count

    ## wait for results

    queue = organizer.get_queue()
    while queue.qsize() < client_count:
        time.sleep(0.5)
    
    print "queue full"

    responses = []
    while not queue.empty():
        responses.append(queue.get())

    ## aggregate results

    print "aggregate"
    now = current_time()
    send_start = reduce(lambda x, y: min(x, y['send_start']), responses, now)
    send_end = reduce(lambda x, y: max(x, y['send_end']), responses, 0)
    receive_start = reduce(lambda x, y: min(x, y['recv_start']), filter(lambda x: x['recv_start'] > 0, responses), now)
    receive_end = reduce(lambda x, y: max(x, y['recv_end']), filter(lambda x: x['recv_end'] > 0, responses), 0)
    error_rate = reduce(lambda x, y: x + float(y['err_rate']) if x != "N/A" and y != "N/A" else "N/A", responses, 0)
        
    total = len(ip_list)
    time_cost = str(receive_end - send_start) if receive_end > send_start else "N/A"
    err_rate = str(float(error_rate) / total) if total > 0 and error_rate != "N/A" else "N/A"
    print "time cost: %s ms, err rate: %s" % (time_cost, err_rate)
    logger.info("Dns Benchmark ends, time_cost: %s ms, err_rate: %s" % (time_cost, err_rate))
    print "send start: %f, send end: %f, recv start: %f, recv end: %f" % (send_start, send_end, receive_start, receive_end)
    logger.info("send start: %f, send end: %f, recv start: %f, recv end: %f" % (send_start, send_end, receive_start, receive_end))

