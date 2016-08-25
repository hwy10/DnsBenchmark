import struct
def dns_unpack(data):
    tidchars = data[0:2]
    tid = struct.unpack('!h', data[0:2])[0]
    flags = struct.unpack('!h', data[2:4])[0]
    error_msg = flags & 0x000F
    # question data[4:6]
    # answers = struct.unpack('!h', data[6:8])[0]
    # authorityRRs data[8:10]
    # additionalRRs data[10:12]
    return (tid, error_msg)

if __name__ == "__main__":
    print dns_unpack(b'\\m\x85\x80\x00\x01\x00\x02\x00\x00\x00\x00\x04test\x04test\x03com\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x0e\x10\x00\x04\x05\x05\x05\x05\xc0\x0c\x00\x01\x00\x01\x00\x00\x0e\x10\x00\x04\x02\x02\x02\x02')
        
