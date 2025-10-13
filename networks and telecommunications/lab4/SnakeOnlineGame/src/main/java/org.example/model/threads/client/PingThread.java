package org.example.model.threads.client;

import java.util.logging.Logger;

public class PingThread extends Thread {
    private static final Logger logger = Logger.getLogger(PingThread.class.getSimpleName());
    private boolean isRunning = true;
    private final ClientThread parentThread;
    private final int delay;

    public PingThread(ClientThread parent, int delay) {
        this.parentThread = parent;
        this.delay = delay;
    }

    @Override
    public void run() {
        while (isRunning) {
            try {
                sleep(delay);
            } catch (InterruptedException e) {
                logger.info("{}: Ping thread interrupted");
            }
            parentThread.sendPing();
        }
    }

    public void setStopped() {
        isRunning = false;
    }
}
