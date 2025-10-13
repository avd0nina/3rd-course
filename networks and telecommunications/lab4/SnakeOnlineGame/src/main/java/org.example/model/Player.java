package org.example.model;

import protobuf.SnakesProto;
import java.awt.Color;
import java.util.Random;

public class Player {
    private MySnake mySnake;
    private final Color color;
    private final int ID;
    private final String nickname;
    private int score;
    private String address;
    private int port;
    private boolean isAlive = true;
    private SnakesProto.NodeRole role;
    private boolean disconnected = false;
    private boolean isLost = false;
    private static final Random colorRandom = new Random();

    public Player(int ID, String playerName) {
        this.color = generateDistinctColor();
        this.ID = ID;
        this.nickname = playerName;
        score = 0;
    }

    private Color generateDistinctColor() {
        float hue = colorRandom.nextFloat();
        float saturation = 0.8f + colorRandom.nextFloat() * 0.2f;
        float brightness = 0.7f + colorRandom.nextFloat() * 0.3f;
        return Color.getHSBColor(hue, saturation, brightness);
    }

    public SnakesProto.NodeRole getRole() {
        return role;
    }

    public void setRole(SnakesProto.NodeRole role) {
        this.role = role;
    }

    public int getScore() {
        return score;
    }

    public void setScore(int score) {
        this.score = score;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public int getPort() {
        return port;
    }

    public void setPort(int port) {
        this.port = port;
    }

    public String getNickname() {
        return nickname;
    }

    public int getID() {
        return ID;
    }

    public Color getColor() {
        return color;
    }

    public void setSnake(MySnake mySnake) {
        this.mySnake = mySnake;
    }

    public MySnake getSnake() {
        return mySnake;
    }

    public boolean isAlive() {
        return isAlive;
    }

    public void setAlive() {
        isAlive = true;
    }

    public void setZombie() {
        isAlive = false;
    }

    public void setDisconnected() {
        disconnected = true;
    }

    public boolean isDisconnected() {
        return disconnected;
    }

    public void incrementScore() {
        score++;
    }

    public boolean isLost() {
        return isLost;
    }

    public void setLost() {
        isLost = true;
    }
}
