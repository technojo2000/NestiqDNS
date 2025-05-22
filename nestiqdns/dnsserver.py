from dnslib.server import DNSServer, BaseResolver, DNSLogger
from dnslib import RR, QTYPE, A

import redis


class DynamicDNSLogger(DNSLogger):
    def log_recv(self, *args, **kwargs):
        pass
    def log_send(self, *args, **kwargs):
        pass
    def log_request(self, *args, **kwargs):
        pass
    def log_reply(self, *args, **kwargs):
        pass
    def log_truncated(self, *args, **kwargs):
        pass
    def log_error(self, *args, **kwargs):
        pass
    def log_data(self, *args, **kwargs):
        pass
    def log(self, *args, **kwargs):
        pass


class DynamicResolver(BaseResolver):
    def __init__(self, db_host, db_port):
        # example:
        # {"example.local": "192.168.1.100"}
        # the trailing "." is not required
        self.records = redis.Redis(
            host=db_host,
            port=db_port,
            db=0
        )

    def _clean_name(self, name):
        # Helper to remove trailing dot from domain names
        return name[:-1] if name.endswith(".") else name        

    def add_record(self, name, ip):
        name = self._clean_name(name)    
        self.records.set(name, ip)
        return self.records.get(name)

    def remove_record(self, name):
        name = self._clean_name(name)         
        self.records.delete(name)

    def clear_records(self):
        self.records.flushdb()

    def update_record(self, name, ip):
        self.add_record(name, ip)      

    def get_record(self, name):
        name = self._clean_name(name)      
        return self.records.get(name)

    def get_records(self):
        keys = self.records.keys()
        data = {}
        for key in keys:
            value = self.records.get(key)
            data[key.decode('utf-8')] = value.decode('utf-8') if value else None
        return data

    def resolve(self,request,handler):
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        reply = request.reply()

        if qtype == "A":
            name = str(qname)
            name = self._clean_name(name)
            # check if the record exists
            if self.records.exists(name):
                ip = self.records.get(name)
                if ip:
                    ip = ip.decode('utf-8')
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(ip), ttl=60))

        # return the reply, empty if no record found
        return reply
    

class DNSServer:
    def __init__(self, address="0.0.0.0", port=53, db_host="127.0.0.1", db_port=6379):
        self.address = address
        self.port = port
        self.logger = DynamicDNSLogger()
        self.resolver = DynamicResolver(db_host, db_port)
        # Fix: use dnslib.server.DNSServer, not this class
        from dnslib.server import DNSServer as LibDNSServer
        self.server = LibDNSServer(self.resolver, port=self.port, address=self.address, logger=self.logger)

    def start_thread(self):
        print(f"Starting DNS server on {self.address}:{self.port}")
        self.server.start_thread()

    def stop_thread(self):
        print("Stopping DNS server")
        self.server.stop()