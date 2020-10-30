import multiprocessing
import signal
import traceback
import types


def cprint(text):
    """Print with cpu number"""
    print("{0}: {1}".format(get_cpu(), text))


def get_cpu():
    """Return cpu number"""
    proc = multiprocessing.current_process()
    return int(proc.name.split("-")[1] if "-" in proc.name else "0")


class Pool(object):
    """self-written pool class which exits gracefully on keyboard exit"""

    def do_worker(self):
        """let a work go through the queue until it encounters None"""
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        cpu = get_cpu()
        while True:
            try:
                job = self.job_queue.get()
                if job is None:
                    self.result_in.send(None)
                    break
                function, args, kwargs = job
                result = function(*args, **kwargs)
                if isinstance(result, types.GeneratorType):
                    for sub_result in result:
                        self.result_in.send((sub_result, cpu))
                else:
                    self.result_in.send((result, cpu))
            except KeyboardInterrupt:
                pass
            except Exception as error:
                self.result_in.send(
                    (traceback.format_exc() if self.do_traceback else error,
                     cpu))

    def listener(self, output):
        """Monitor result queue and write to stdout"""

        count = 0
        while True:
            try:
                result = self.result_out.recv()
                if result is None:
                    count += 1
                    if count == self.processes:
                        break
                else:
                    result, cpu = result
                    output.write("{0} (cpu {1})\n".format(result, cpu))
                output.flush()
            except KeyboardInterrupt:
                pass

    def __init__(self, processes, do_traceback=False):
        """Main loop"""
        self.job_queue = multiprocessing.Queue()
        self.result_in, self.result_out = multiprocessing.Pipe()
        self.do_traceback = do_traceback
        self.processes = processes

        self.workers = []

        for _count in range(processes):
            worker = multiprocessing.Process(target=self.do_worker)
            worker.start()
            self.workers.append(worker)

    def add_listener(self, output):
        """Add a listener to the queue"""
        worker = multiprocessing.Process(target=self.listener,
                                         args=(output,))
        worker.start()
        self.workers.append(worker)

    def apply_async(self, function, args=None, kwargs=None):
        """Put job in the queue"""
        self.job_queue.put((function,
                            [] if args is None else args,
                            {} if kwargs is None else kwargs))

    def close(self):
        """Close the pool"""
        for _count in range(self.processes):
            self.job_queue.put(None)

    def join(self):
        """Wait for all workers to finish"""
        try:
            for worker in self.workers:
                worker.join()
        except KeyboardInterrupt:
            print("Gracefully exit due to keyboard interrupt")
            for worker in self.workers:
                worker.terminate()
                worker.join()
        except Exception:
            for worker in self.workers:
                worker.terminate()
                worker.join()

            raise
