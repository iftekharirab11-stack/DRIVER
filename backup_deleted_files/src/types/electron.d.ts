declare module 'electron' {
  interface IpcMainEvent {
    sender: { id: number };
    reply: (channel: string, ...args: any[]) => void;
  }
  namespace ipcMain {
    function handle(channel: string, listener: (...args: any[]) => any): void;
    function removeHandler(channel: string, listener?: (...args: any[]) => any): void;
    function removeAllListeners(channel?: string): void;
  }
}
