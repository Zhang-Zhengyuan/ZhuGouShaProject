import queue
import threading
import time
from typing import Optional, Dict, Tuple
from communicator.comm_event import CommEvent, AckEvent


class Communicator:
    """
    后端 <-> 前端 的简易事件总线 + ACK 确认机制。
    """

    def __init__(self) -> None:
        self.btf_queue: "queue.Queue[CommEvent]" = queue.Queue()
        self.ftb_queue: "queue.Queue[CommEvent]" = queue.Queue()

        self._ack_inbox: "queue.Queue[AckEvent]" = queue.Queue()

        self.event_counter = 0
        self.pending_acks: Dict[int, threading.Event] = {}
        self.ack_results: Dict[int, Tuple[bool, str]] = {}
        self.lock = threading.Lock()

        self._stop_event = threading.Event()

        self.ack_thread = threading.Thread(
            target=self._process_acks, name="comm-ack-thread", daemon=True
        )
        self.ack_thread.start()

    def send_to_frontend(
        self,
        event: CommEvent,
        wait_for_ack: bool = False,
        timeout: float = 30.0,
    ) -> Tuple[Optional[bool], Optional[str]]:
        """
        发送事件到前端；可选择等待 ACK。

        Returns:
            (success: bool | None, message: str | None)
            - wait_for_ack=False 时，返回 (None, None)
            - wait_for_ack=True 时，返回 (True/False, msg)
        """
        if not wait_for_ack:
            with self.lock:
                self.event_counter += 1
                event_id = self.event_counter
                setattr(event, "_event_id", event_id)

            self.btf_queue.put(event)
            return None, None

        with self.lock:
            self.event_counter += 1
            event_id = self.event_counter
            setattr(event, "_event_id", event_id)
            ack_event = threading.Event()
            self.pending_acks[event_id] = ack_event

        self.btf_queue.put(event)

        ack_received = ack_event.wait(timeout=timeout)

        with self.lock:
            self.pending_acks.pop(event_id, None)
            result = self.ack_results.pop(event_id, (False, "ACK timeout"))

        return result

    def send_to_backend(self, event: CommEvent) -> None:
        """
        前端 -> 后端：投递消息到后端消费。
        若为 AckEvent，额外复制一份进 _ack_inbox 供 ACK 线程消费。
        """
        self.ftb_queue.put(event)
        if isinstance(event, AckEvent):
            self._ack_inbox.put(event)

    def receive_from_frontend(self) -> Optional[CommEvent]:
        if self.ftb_queue.empty():
            return None
        return self.ftb_queue.get()

    def receive_from_backend(self) -> Optional[CommEvent]:
        if self.btf_queue.empty():
            return None
        return self.btf_queue.get()

    def get_from_frontend(self, timeout: Optional[float] = None) -> CommEvent:
        return self.ftb_queue.get(timeout=timeout)

    def get_from_backend(self, timeout: Optional[float] = None) -> CommEvent:
        return self.btf_queue.get(timeout=timeout)

    def stop(self, wait: bool = True) -> None:
        """
        停止 ACK 处理线程。
        """
        self._stop_event.set()
        self._ack_inbox.put(None)  # type: ignore
        if wait:
            self.ack_thread.join(timeout=5.0)

    def _process_acks(self) -> None:
        """
        专职处理来自前端的 AckEvent：
        - 若有人等待该 event_id，则写入结果并唤醒；
        - 若无人等待（不需要 ACK），直接丢弃，防泄漏。
        """
        while not self._stop_event.is_set():
            try:
                item = self._ack_inbox.get(timeout=0.5)
                if item is None:
                    continue

                if not isinstance(item, AckEvent):
                    continue

                original_id = getattr(item, "original_event_id", None)
                success = getattr(item, "success", False)
                message = getattr(item, "message", "")

                with self.lock:
                    waiter = self.pending_acks.get(original_id)
                    if waiter is not None:
                        self.ack_results[original_id] = (bool(success), str(message))
                        waiter.set()
                    else:
                        pass

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Communicator] Error processing ACK: {e}")
                time.sleep(0.1)


communicator = Communicator()
