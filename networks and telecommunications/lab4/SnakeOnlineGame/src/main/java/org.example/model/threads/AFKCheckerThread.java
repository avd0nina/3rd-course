package org.example.model.threads;

import org.example.model.threads.client.ClientThread;
import org.example.model.threads.master.MasterThread;
import protobuf.SnakesProto;
import java.util.ArrayList;
import java.util.List;

public class AFKCheckerThread extends Thread {
    private boolean isRunning = true;
    private final int delay;
    private ClientThread clientThread;
    private MasterThread masterThread;
    private final List<Integer> sendersID;
    private SnakesProto.NodeRole role;

    public AFKCheckerThread(ClientThread thread, int delay) {
        this.clientThread = thread;
        this.delay = delay;
        sendersID = new ArrayList<>();
    }

    public AFKCheckerThread(MasterThread thread, int delay) {
        this.masterThread = thread;
        this.delay = delay;
        sendersID = new ArrayList<>();
    }

    public void setRole(SnakesProto.NodeRole role) {
        this.role = role;
    }

    @Override
    public void run() {
        while (isRunning) {
            try {
                sleep(delay);
            } catch (InterruptedException ignored) {
            }
            switch (role) {
                case MASTER: {
                    var playersID = masterThread.getPlayersID();
                    List<Integer> exitedPlayers = new ArrayList<>();
                    synchronized (sendersID) {
                        for (Integer playerID : playersID) {
                            boolean alive = false;
                            for (Integer ID : sendersID) {
                                if (playerID.equals(ID)) {
                                    alive = true;
                                    break;
                                }
                            }
                            if (!alive) {
                                exitedPlayers.add(playerID);
                            }
                        }
                        for (Integer ID : exitedPlayers) {
                            masterThread.setPlayerZombie(ID);
                        }
                        sendersID.clear();
                        sendersID.notifyAll();
                    }
                    break;
                }
                case NORMAL: {
                    var playersID = clientThread.getPlayersID();
                    List<Integer> exitedPlayers = new ArrayList<>();
                    synchronized (sendersID) {
                        for (Integer playerID : playersID) {
                            boolean alive = false;
                            for (Integer ID : sendersID) {
                                if (playerID.equals(ID)) {
                                    alive = true;
                                    break;
                                }
                            }
                            if (!alive) {
                                exitedPlayers.add(playerID);
                            }
                        }
                        int masterID = clientThread.getMasterID();
                        for (Integer ID : exitedPlayers) {
                            if (ID == masterID) {
                                clientThread.changeMaster();
                                break;
                            }
                        }
                        sendersID.clear();
                        sendersID.notifyAll();
                    }
                    break;
                }
                case DEPUTY: {
                    var playersID = clientThread.getPlayersID();
                    List<Integer> exitedPlayers = new ArrayList<>();
                    synchronized (sendersID) {
                        for (Integer playerID : playersID) {
                            boolean alive = false;
                            for (Integer ID : sendersID) {
                                if (playerID.equals(ID)) {
                                    alive = true;
                                    break;
                                }
                            }
                            if (!alive) {
                                exitedPlayers.add(playerID);
                            }
                        }
                        int masterID = clientThread.getMasterID();
                        for (Integer ID : exitedPlayers) {
                            if (ID == masterID) {
                                clientThread.becomeMaster();
                                break;
                            }
                        }
                        sendersID.clear();
                        sendersID.notifyAll();
                    }
                    break;
                }
            }
        }
    }

    public void addSender(int senderID) {
        synchronized (sendersID) {
            sendersID.add(senderID);
            sendersID.notifyAll();
        }
    }

    public void setStopped() {
        isRunning = false;
    }
}
