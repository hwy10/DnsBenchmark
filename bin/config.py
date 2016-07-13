import ConfigParser
config = ConfigParser.ConfigParser()
config.read('../conf/dns_benchmark.conf')

if __name__ == "__main__":
    print config.sections()
    print config.get('logger', 'filename')
