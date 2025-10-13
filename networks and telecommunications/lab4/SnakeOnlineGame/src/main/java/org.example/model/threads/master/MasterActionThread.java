package org.example.model.threads.master;

import org.example.model.FieldInfo;
import org.example.model.Movement;
import java.util.ArrayList;
import java.util.List;

public class MasterActionThread extends Thread {
    private boolean isRunning = true;
    private final int delay;
    private final FieldInfo fieldInfo;
    private final List<Movement> movementQueue;

    public MasterActionThread(FieldInfo fieldInfo, int delay) {
        this.fieldInfo = fieldInfo;
        this.delay = delay;
        movementQueue = new ArrayList<>();
    }

    @Override
    public void run() {
        while (isRunning) {
            try {
                sleep(delay);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            synchronized (movementQueue) {
                List<Integer> playersID = new ArrayList<>();
                for (int i = movementQueue.size() - 1; i >= 0; --i) {
                    Movement movement = movementQueue.get(i);
                    boolean moveMade = false;
                    for (Integer playerID : playersID) {
                        if (movement.playerID() == playerID) {
                            movementQueue.remove(movement);
                            moveMade = true;
                            break;
                        }
                    }
                    if (!moveMade) {
                        playersID.add(movement.playerID());
                        fieldInfo.makeMove(movement);
                    }
                }
                movementQueue.clear();
                movementQueue.notifyAll();
            }
            fieldInfo.updateField();
        }
    }

    public void addMove(Movement movement) {
        synchronized (movementQueue) {
            movementQueue.add(movement);
            movementQueue.notifyAll();
        }
    }

    public void setStopped() {
        isRunning = false;
    }
}
