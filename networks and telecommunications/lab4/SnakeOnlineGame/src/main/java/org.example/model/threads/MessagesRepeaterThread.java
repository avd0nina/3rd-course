package org.example.model.threads;

import protobuf.SnakesProto;
import java.util.List;

public class MessagesRepeaterThread extends Thread {
    private boolean isRunning = true;
    private final int delay;
    private final List<SnakesProto.GameMessage> messagesQueue;
    private final GameThread thread;

    public MessagesRepeaterThread(GameThread thread, List<SnakesProto.GameMessage> messagesQueue, int delay) {
        this.messagesQueue = messagesQueue;
        this.thread = thread;
        this.delay = delay;
    }

    @Override
    public void run() {
        while (isRunning) {
            try {
                sleep(delay);
            } catch (InterruptedException ignored) {
            }
            synchronized (messagesQueue) {
                for (SnakesProto.GameMessage message : messagesQueue) {
                    thread.repeatMessage(message);
                }
                messagesQueue.notifyAll();
            }
        }
    }

    public void setStopped() {
        isRunning = false;
    }
}
