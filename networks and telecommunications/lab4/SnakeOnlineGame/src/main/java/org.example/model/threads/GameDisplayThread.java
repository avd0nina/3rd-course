package org.example.model.threads;

import org.example.model.Model;
import java.util.logging.Logger;

public class GameDisplayThread extends Thread {
    private static final Logger logger = Logger.getLogger(GameDisplayThread.class.getSimpleName());
    private boolean isRunning = true;
    private final Model model;

    public GameDisplayThread(Model model) {
        this.model = model;
    }

    @Override
    public void run() {
        while (isRunning) {
            try {
                sleep(1000);
            } catch (InterruptedException e) {
                logger.info("Thread interrupted");
            }
            model.showActiveGames();
        }
    }
    public void setStopped() {
        isRunning = false;
    }
}
