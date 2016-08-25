import struct

def domaintobyte(domain):
    sections = domain.split('.')
    domainbyte = ''
    for section in sections:
        fmt = 'B%ds' % len(section)
        byte = struct.pack(fmt, len(section), section)
        domainbyte += byte
    domainbyte += '\0'
    return domainbyte

def pack(tid, domain):
    FLAGS = 0x0100
    QUESTIONS = 0x0001 # 1 question
    ANSWERS = 0x0000 # 0 answer
    AUTHORITYRRS = 0x0000
    ADDITIONALRRS = 0x0000
    domainbyte = domaintobyte(domain)
    QUESTIONTYPE = 0x0001 # IPv4
    QUESTIONCLASS = 0x0001 # Internet
    header = struct.pack('!hhhhhh', tid, FLAGS, QUESTIONS, ANSWERS, AUTHORITYRRS, ADDITIONALRRS)
    tail = struct.pack('!hh', QUESTIONTYPE, QUESTIONCLASS)
    msg = header + domainbyte + tail
    return msg

if __name__ == "__main__":
    print repr(pack(0x5c6d, "www.baidu.com"))
