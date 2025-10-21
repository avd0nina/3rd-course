package org.example.model.threads.master;

import protobuf.SnakesProto;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

public class AnnouncementThread extends Thread {
    private final AtomicBoolean isRunning = new AtomicBoolean(true);
    private final MasterThread masterThread;
    private SnakesProto.GameAnnouncement gameAnnouncement;
    private final List<SnakesProto.GamePlayer> players;

    public AnnouncementThread(MasterThread thread) {
        masterThread = thread;
        players = new ArrayList<>();
    }

    public void createAnnouncement(String gameName) {
        SnakesProto.GamePlayers.Builder gamePlayers = SnakesProto.GamePlayers.newBuilder();
        for (SnakesProto.GamePlayer player : players) {
            gamePlayers.addPlayers(player);
        }
        gameAnnouncement = SnakesProto.GameAnnouncement
                .newBuilder()
                .setGameName(gameName)
                .setConfig(SnakesProto.GameConfig.getDefaultInstance())
                .setPlayers(gamePlayers).build();
    }

    public void updateAnnouncement(){
        synchronized (players) {
            SnakesProto.GamePlayers.Builder gamePlayers = SnakesProto.GamePlayers.newBuilder();
            for (SnakesProto.GamePlayer player : players) {
                gamePlayers.addPlayers(player);
            }
            gameAnnouncement = SnakesProto.GameAnnouncement
                    .newBuilder()
                    .setGameName(gameAnnouncement.getGameName())
                    .setConfig(gameAnnouncement.getConfig())
                    .setPlayers(gamePlayers).build();
        }
    }

    public void addPlayer(SnakesProto.GamePlayer player) {
        synchronized (players) {
            players.add(player);
        }
    }

    public void deletePlayer(int ID) {
        synchronized (players) {
            for (SnakesProto.GamePlayer player : players) {
                if (player.getId() == ID) {
                    players.remove(player);
                    return;
                }
            }
        }
    }

    @Override
    public void run() {
        while (isRunning.get()) {
            try {
                sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            masterThread.sendAnnounce(gameAnnouncement);
        }
    }

    public void setStopped() {
        isRunning.set(false);
    }
}
