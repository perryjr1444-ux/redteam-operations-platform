/**
 * WebSocket Service for Real-time Tool Execution Streaming
 *
 * Uses native WebSocket (not socket.io) to connect to FastAPI backend
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.handlers = new Map();
    this.reconnectTimeout = null;
    this.connecting = false;
  }

  connect() {
    // Prevent multiple simultaneous connections
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      console.log('[WS] Already connected or connecting');
      return this;
    }

    if (this.connecting) {
      console.log('[WS] Connection already in progress');
      return this;
    }

    this.connecting = true;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/api/ws`;

    console.log('[WS] Connecting to:', url);

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[WS] Connected');
      this.connecting = false;
      this.reconnectAttempts = 0;
      this.emit('connection', { status: 'connected' });
    };

    this.ws.onclose = (event) => {
      console.log('[WS] Disconnected:', event.code, event.reason);
      this.connecting = false;
      this.emit('connection', { status: 'disconnected', reason: event.reason });

      // Attempt reconnect
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * this.reconnectAttempts, 5000);
        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.reconnectTimeout = setTimeout(() => this.connect(), delay);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error);
      this.emit('error', { error });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { type, ...payload } = data;

        // Emit event by type
        if (type) {
          this.emit(type, payload);
        }
      } catch (err) {
        console.error('[WS] Failed to parse message:', err, event.data);
      }
    };

    return this;
  }

  /**
   * Send data to server
   */
  send(type, data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    } else {
      console.error('[WS] Cannot send - not connected');
    }
  }

  /**
   * Execute a single tool
   */
  executeTool(toolName, args = {}, options = {}) {
    return new Promise((resolve, reject) => {
      const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      this.send('execute_tool', {
        execution_id: executionId,
        tool: toolName,
        args,
        options
      });

      // Listen for completion
      const completeHandler = (data) => {
        if (data.execution_id === executionId) {
          this.off('tool_complete', completeHandler);
          this.off('tool_error', errorHandler);
          resolve(data);
        }
      };

      const errorHandler = (data) => {
        if (data.execution_id === executionId) {
          this.off('tool_complete', completeHandler);
          this.off('tool_error', errorHandler);
          reject(data);
        }
      };

      this.on('tool_complete', completeHandler);
      this.on('tool_error', errorHandler);
    });
  }

  /**
   * Execute an attack chain (workflow)
   */
  executeChain(chainId, chainConfig) {
    return new Promise((resolve, reject) => {
      const executionId = `chain_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      this.send('execute_chain', {
        execution_id: executionId,
        chain_id: chainId,
        config: chainConfig
      });

      const completeHandler = (data) => {
        if (data.execution_id === executionId) {
          this.off('chain_complete', completeHandler);
          resolve(data);
        }
      };

      this.on('chain_complete', completeHandler);
    });
  }

  /**
   * Subscribe to events
   */
  on(event, handler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event).add(handler);
  }

  /**
   * Unsubscribe from events
   */
  off(event, handler) {
    if (this.handlers.has(event)) {
      this.handlers.get(event).delete(handler);
    }
  }

  /**
   * Emit event to handlers
   */
  emit(event, data) {
    if (this.handlers.has(event)) {
      this.handlers.get(event).forEach(handler => handler(data));
    }
  }

  /**
   * Disconnect
   */
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Singleton instance
export const wsService = new WebSocketService();
export default wsService;
