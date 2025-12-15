import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from phone_agent.agent import PhoneAgent, AgentConfig
from phone_agent.model import ModelConfig

class AgentWorker(QThread):
    """Worker thread for running the agent to keep UI responsive."""
    
    # Signals to update UI
    signal_thinking = pyqtSignal(str)  # content
    signal_action = pyqtSignal(dict, str)  # action_dict, screenshot_base64
    signal_step_complete = pyqtSignal(bool, str)  # success, message
    signal_error = pyqtSignal(str) # error message
    signal_finished = pyqtSignal(str) # final result
    signal_log = pyqtSignal(str) # general logs

    def __init__(self, model_config_dict, agent_config_dict, task):
        super().__init__()
        self.model_config_dict = model_config_dict
        self.agent_config_dict = agent_config_dict
        self.task = task
        self.agent = None

    def run(self):
        try:
            # Reconstruct configs
            model_config = ModelConfig(**self.model_config_dict)
            agent_config = AgentConfig(**self.agent_config_dict)
            
            # Create agent with callback
            self.agent = PhoneAgent(
                model_config=model_config,
                agent_config=agent_config,
                event_callback=self._handle_agent_event
            )
            
            self.signal_log.emit(f"Task started: {self.task}")
            result = self.agent.run(self.task)
            
        except Exception as e:
            traceback.print_exc()
            self.signal_error.emit(str(e))

    def _handle_agent_event(self, event_type, data):
        """Callback to bridge Agent events to Qt Signals."""
        try:
            if event_type == "thinking":
                self.signal_thinking.emit(data.get("content", ""))
            elif event_type == "action":
                self.signal_action.emit(data.get("action", {}), data.get("screenshot", ""))
            elif event_type == "error":
                self.signal_error.emit(data.get("error", "Unknown error"))
            elif event_type == "finished":
                self.signal_finished.emit(data.get("result", ""))
        except Exception as e:
            print(f"Error in event handler: {e}")

    def stop(self):
        """Request agent to stop (not fully implemented in agent yet, but we can terminate thread safe-ish)."""
        if self.isRunning():
            self.terminate()
