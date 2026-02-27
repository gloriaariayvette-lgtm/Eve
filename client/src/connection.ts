/**
 * WebSocket client — connects to Eve server, dispatches messages to handlers.
 */

export interface ServerMessage {
  type: string;
  data: Record<string, unknown>;
  timestamp: number;
}

export type MessageHandler = (msg: ServerMessage) => void;

export class Connection {
  private ws: WebSocket | null = null;
  private handlers = new Map<string, MessageHandler[]>();
  private reconnectDelay = 1000;
  private maxReconnectDelay = 10000;
  private url: string;

  constructor(url?: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = url ?? `${protocol}//${window.location.host}/ws`;
  }

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[WS] Connected to Eve server');
        this.reconnectDelay = 1000;
        this.emit('_connected', { type: '_connected', data: {}, timestamp: Date.now() / 1000 });
      };

      this.ws.onmessage = (event) => {
        try {
          const msg: ServerMessage = JSON.parse(event.data);
          this.emit(msg.type, msg);
        } catch (e) {
          console.warn('[WS] Failed to parse message:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('[WS] Disconnected, reconnecting in', this.reconnectDelay, 'ms');
        this.emit('_disconnected', { type: '_disconnected', data: {}, timestamp: Date.now() / 1000 });
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
      };

      this.ws.onerror = (err) => {
        console.error('[WS] Error:', err);
      };
    } catch (e) {
      console.error('[WS] Connection failed:', e);
      setTimeout(() => this.connect(), this.reconnectDelay);
    }
  }

  on(type: string, handler: MessageHandler): void {
    const list = this.handlers.get(type) ?? [];
    list.push(handler);
    this.handlers.set(type, list);
  }

  send(type: string, data: Record<string, unknown> = {}): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type,
        data,
        timestamp: Date.now() / 1000,
      }));
    }
  }

  sendUserInput(text: string): void {
    this.send('user_input', { text });
  }

  sendTracking(trackingData: Record<string, unknown>): void {
    this.send('user_tracking', trackingData);
  }

  get connected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private emit(type: string, msg: ServerMessage): void {
    const handlers = this.handlers.get(type) ?? [];
    for (const h of handlers) {
      try {
        h(msg);
      } catch (e) {
        console.error(`[WS] Handler error for "${type}":`, e);
      }
    }
  }
}
