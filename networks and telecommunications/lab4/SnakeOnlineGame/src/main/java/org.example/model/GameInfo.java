package org.example.model;

import protobuf.SnakesProto;

public class GameInfo {
    private final SnakesProto.GameAnnouncement announcement;
    private String gameAddress;
    private int gamePort;

    public GameInfo(SnakesProto.GameAnnouncement announcement) {
        this.announcement = announcement;
    }

    public GameInfo(String gameName) {
        announcement = SnakesProto.GameAnnouncement
                .newBuilder().setGameName(gameName)
                .setPlayers(
                        SnakesProto.GamePlayers.newBuilder()
                ).setGameName(gameName)
                .setConfig(SnakesProto.GameConfig.getDefaultInstance())
                .build();
    }

    public void setGameAddress(String gameAddress) {
        this.gameAddress = gameAddress;
    }

    public void setGamePort(int gamePort) {
        this.gamePort = gamePort;
    }

    public String getGameAddress() {
        return gameAddress;
    }

    public int getGamePort() {
        return gamePort;
    }

    public int getPlayerCount() {
        return announcement.getPlayers().getPlayersCount();
    }

    public String getGameName() {
        return announcement.getGameName();
    }

    public SnakesProto.GameConfig getConfig() {
        return announcement.getConfig();
    }
}
