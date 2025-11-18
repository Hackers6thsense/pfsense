import os
import time
from metasploit.client import MetasploitRPC, RpcError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

class MetasploitError(Exception):
    pass

class MetasploitClient:
    def __init__(self):
        self.host = os.getenv("MSF_RPC_HOST", "127.0.0.1")
        self.port = int(os.getenv("MSF_RPC_PORT", "55553"))
        self.user = os.getenv("MSF_RPC_USER", "msf")
        self.password = os.getenv("MSF_RPC_PASS", "msf")
        self.token = os.getenv("MSF_RPC_TOKEN", None)
        self.client = self.connect()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True,
           retry=retry_if_exception_type((ConnectionError, Exception)))
    def connect(self):
        client = MetasploitRPC(self.host, self.port)
        if self.token:
            client.login_token(self.token)
        else:
            client.login(self.user, self.password)
        return client

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True,
           retry=retry_if_exception_type((RuntimeError, RpcError)))
    def run_module(self, modtype, name, options):
        # modtype: "exploit", "auxiliary", etc.
        job_id = self.client.call('module.execute', [modtype, name, options]).get('job_id')
        if not job_id:
            raise RuntimeError("Failed to launch module")
        return job_id

    def wait_for_job(self, job_id, timeout=300):
        start = time.time()
        while time.time() - start < timeout:
            jobs = self.client.call('job.list')
            if str(job_id) not in jobs:
                return True
            time.sleep(1)
        raise MetasploitError(f"Timeout waiting for Metasploit job {job_id}")