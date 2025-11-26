from context import worker

from worker.worker import WorkerNode

if __name__ == '__main__':
    worker_node = WorkerNode()
    worker_node.run()