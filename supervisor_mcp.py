# supervisor_mcp.py
import socket
import threading
import json
from controller import Supervisor

HOST, PORT = 'localhost', 5000

class MCPHandler(threading.Thread):
    def __init__(self, conn, addr, supervisor):
        super().__init__()
        self.conn = conn
        self.supervisor = supervisor

    def run(self):
        data = self.conn.recv(4096).decode('utf-8')
        try:
            req = json.loads(data)
            method = req.get('method')
            params = req.get('params', {})
            # dispatch
            if method == 'getTranslation':
                node = self.supervisor.getFromDef(params['def'])
                pos = node.getField('translation').getSFVec3f()
                result = pos
            elif method == 'reset':
                self.supervisor.simulationReset()
                result = 'ok'
            else:
                raise ValueError('Unknown method')
            resp = {'jsonrpc':'2.0','result':result,'id':req.get('id')}
        except Exception as e:
            resp = {'jsonrpc':'2.0','error':{'code':-32601,'message':str(e)},'id':req.get('id')}
        self.conn.sendall((json.dumps(resp) + '\n').encode('utf-8'))
        self.conn.close()

def main():
    sup = Supervisor()
    timestep = int(sup.getBasicTimeStep())

    # 启动 TCP 服务线程
    def serve():
        with socket.socket() as s:
            s.bind((HOST, PORT))
            s.listen()
            while True:
                conn, addr = s.accept()
                MCPHandler(conn, addr, sup).start()

    threading.Thread(target=serve, daemon=True).start()

    # 主循环仅驱动仿真步进
    while sup.step(timestep) != -1:
        pass

if __name__ == '__main__':
    main()
