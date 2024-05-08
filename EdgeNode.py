import sys
import eventlet
import socketio
import time
from typing import Any
from ultralytics import YOLO
from Logger import Logger
from utils.constants import CLOUD_ADDRESS
from utils.helper_functions import get_device_id, predict_images


class EdgeNode:
    """
    Represents an edge node that receives data from IoT devices, processes it, and sends it to the cloud.
    """

    def __init__(
        self,
        device_id: str,
        port: int = 10000,
        cloud_addr: str = CLOUD_ADDRESS,
    ):
        """
        Initialize the EdgeNode instance.

        Args:
            device_id (str): The unique identifier of the edge node.
            port (int, optional): The port on which the edge node will run. Defaults to 10000.
            cloud_addr (str, optional): The address of the cloud server. Defaults to CLOUD_ADDRESS.
        """
        self.device_id = device_id
        self.cloud_addr = cloud_addr
        self.port = port
        self.sio_client = socketio.Client()
        self.sio_server = socketio.Server()
        self.app = socketio.WSGIApp(self.sio_server)
        self.logger = Logger(name=f"EdgeNode-{device_id}").get_logger()
        self.model = YOLO("yolov8m.pt")
        self.transtime = 0
        self.proctime = 0

    def process_iot_data(self, device_id: str, data: Any):
        """
        Receive data from an IoT device, process it, and send it to the cloud.

        Args:
            device_id (str): The identifier of the IoT device.
            data (Dict[str, int]): The data received from the IoT device.
        """
        self.logger.info(
            f"Received data from IoT device {device_id}: {len(data)} image paths"
        )
        start_time = time.time()
        # Process the data
        data = predict_images(list(data), self.model)
        self.proctime += time.time() - start_time
        start_time = time.time()
        self.sio_client.emit(
            "recv",
            data={"data": data},
        )
        self.transtime += time.time() - start_time
        self.sio_client.emit(
            "recv",
            data={
                "transtime": self.transtime,
                "proctime": self.proctime,
                "data": None,
            },
        )

    def run(self):
        """
        Run the edge node.
        """
        try:
            # Connect to the cloud
            self.sio_client.connect(
                self.cloud_addr, headers={"device_id": self.device_id}
            )
            self.logger.info(f"Connected to cloud ({self.cloud_addr})")
            # Start serving the WSGI app
            eventlet.wsgi.server(eventlet.listen(("", self.port)), self.app)
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    # Get arguments from the command line (device ID)
    device_id = sys.argv[1] if len(sys.argv) > 1 else "edge-1"
    edge_node = EdgeNode(device_id=device_id)

    @edge_node.sio_server.event
    def connect(sid, environ):
        device_id = get_device_id(environ) or sid
        edge_node.sio_server.save_session(sid, {"device_id": device_id})
        edge_node.logger.info(f"IoT device {device_id} connected, session ID: {sid}")

    @edge_node.sio_server.event
    def disconnect(sid):
        session = edge_node.sio_server.get_session(sid)
        device_id = session["device_id"]
        edge_node.logger.info(f"IoT device {device_id} disconnected")

    @edge_node.sio_server.event
    def recv(sid, data):
        session = edge_node.sio_server.get_session(sid)
        device_id = session["device_id"]
        # Check if the data is transtime or data batch
        if "acc_transtime" in data and data["acc_transtime"] is not None:
            edge_node.transtime += data["acc_transtime"]
            edge_node.logger.info(
                f"Accumulated transmission time from IoT device {device_id}: {data['acc_transtime']}s"
            )
            return
        edge_node.process_iot_data(session["device_id"], data["data"])

    try:
        # Run the edge node
        edge_node.run()
    except KeyboardInterrupt or SystemExit or Exception as e:
        if isinstance(e, Exception):
            edge_node.logger.error(f"An error occurred: {e}")
        edge_node.logger.info("Edge node stopped.")
        edge_node.sio_client.disconnect()
        edge_node.sio_server.shutdown()
        sys.exit(0)
