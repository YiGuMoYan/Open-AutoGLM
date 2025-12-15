import traceback
from PyQt6.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
from phone_agent.agent import PhoneAgent, AgentConfig
from phone_agent.model import ModelConfig

class AgentWorker(QThread):
    """Worker thread for running the agent to keep UI responsive."""
    
    # Signals to update UI - All include device_id as first arg
    signal_thinking = pyqtSignal(str, str)  # device_id, content
    signal_action = pyqtSignal(str, dict, str)  # device_id, action_dict, screenshot_base64
    signal_step_complete = pyqtSignal(str, bool, str)  # device_id, success, message
    signal_error = pyqtSignal(str, str) # device_id, error message
    signal_finished = pyqtSignal(str, str) # device_id, final result
    signal_log = pyqtSignal(str, str) # device_id, general logs
    signal_takeover_request = pyqtSignal(str, str) # device_id, message

    def __init__(self, device_id, model_config_dict, agent_config_dict, task):
        super().__init__()
        self.device_id = device_id
        self.model_config_dict = model_config_dict
        self.agent_config_dict = agent_config_dict
        self.task = task
        self.agent = None
        
        # Synchronization for manual takeover
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        self.is_paused = False

    def run(self):
        try:
            # Reconstruct configs
            model_config = ModelConfig(**self.model_config_dict)
            agent_config = AgentConfig(**self.agent_config_dict)
            
            # Create agent with callback
            self.agent = PhoneAgent(
                model_config=model_config,
                agent_config=agent_config,
                event_callback=self._handle_agent_event,
                takeover_callback=self._handle_takeover_callback
            )
            
            self.signal_log.emit(self.device_id, f"Task started on {self.device_id}: {self.task}")
            result = self.agent.run(self.task)
            
        except Exception as e:
            traceback.print_exc()
            self.signal_error.emit(self.device_id, str(e))

    def _handle_agent_event(self, event_type, data):
        """Callback to bridge Agent events to Qt Signals."""
        try:
            if event_type == "thinking":
                self.signal_thinking.emit(self.device_id, data.get("content", ""))
            elif event_type == "action":
                self.signal_action.emit(self.device_id, data.get("action", {}), data.get("screenshot", ""))
            elif event_type == "error":
                self.signal_error.emit(self.device_id, data.get("error", "Unknown error"))
            elif event_type == "finished":
                self.signal_finished.emit(self.device_id, data.get("result", ""))
        except Exception as e:
            print(f"Error in event handler: {e}")

    def _handle_takeover_callback(self, message):
        """Called when agent requests manual takeover."""
        self.signal_takeover_request.emit(self.device_id, message)
        
        # Block thread until resumed
        self.mutex.lock()
        self.is_paused = True
        try:
            # Wait until wake_one() is called
            self.cond.wait(self.mutex)
        finally:
            self.is_paused = False
            self.mutex.unlock()

    def resume(self):
        """Resume execution from paused state."""
        self.mutex.lock()
        if self.is_paused:
            self.cond.wakeOne()
        self.mutex.unlock()

    def stop(self):
        """Request agent to stop (not fully implemented in agent yet, but we can terminate thread safe-ish)."""
        if self.isRunning():
            # Ensure we don't block on wait condition if stopped while paused
            self.resume()
            self.terminate()
