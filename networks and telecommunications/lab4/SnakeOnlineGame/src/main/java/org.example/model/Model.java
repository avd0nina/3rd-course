package org.example.model;

import org.example.view.ViewBase;
import org.example.model.threads.GameDisplayThread;
import org.example.model.threads.GamesListener;
import org.example.model.threads.MainThread;
import java.util.logging.Logger;
import protobuf.SnakesProto;
import java.awt.*;
import java.awt.event.KeyEvent;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class Model {
    private static final Logger logger = Logger.getLogger(Model.class.getSimpleName());
    private final ViewBase viewBase;
    private GamesListener listener;
    private final GameDisplayThread gameShower;
    private MainThread mainThread = null;
    private final List<GameInfo> activeGames;

    public Model() {
        logger.info("init a model");
        viewBase = new ViewBase(this);
        logger.info("model initiated successfully");
        try {
            listener = new GamesListener(this);
            listener.start();
            logger.info("listener starts");
        } catch (IOException e) {
            logger.info("{}: error in starting a listener");
        }
        activeGames = new ArrayList<>();
        gameShower = new GameDisplayThread(this);
        gameShower.start();
        logger.info("game display started");
    }

    public void showActiveGames() {
        synchronized (activeGames) {
            viewBase.showActiveGames(activeGames);
            activeGames.clear();
            activeGames.notifyAll();
        }
    }

    public void addActiveGame(GameInfo gameInfo) {
        synchronized (activeGames) {
            activeGames.add(gameInfo);
            activeGames.notifyAll();
        }
    }

    public GameInfo createGame(String gameName, String playerName) {
        try {
            mainThread = new MainThread(this, new GameInfo(gameName), playerName);
            mainThread.newGame();
            return mainThread.getGameInfo();
        } catch (IOException e) {
            logger.info("{}: createGame(): error in executing a MainThread");
            return null;
        }
    }

    public void connect(GameInfo game, String playerName) {
        try {
            mainThread = new MainThread(this, game, playerName);
            mainThread.connectToGame(SnakesProto.NodeRole.NORMAL);
        } catch (IOException e) {
            logger.info("{}: connect(): error in executing a MainThread");
        }
    }

    public void drawField(List<Player> players, List<Point> foods, String playerName) {
        viewBase.drawField(players, foods, playerName);
    }

    public void makeMove(KeyEvent e) {
        if (mainThread == null) {
            return;
        }
        switch (e.getKeyCode()) {
            case KeyEvent.VK_UP: {
                mainThread.makeMove(SnakesProto.Direction.UP);
                break;
            }
            case KeyEvent.VK_LEFT: {
                mainThread.makeMove(SnakesProto.Direction.LEFT);
                break;
            }
            case KeyEvent.VK_RIGHT: {
                mainThread.makeMove(SnakesProto.Direction.RIGHT);
                break;
            }
            case KeyEvent.VK_DOWN: {
                mainThread.makeMove(SnakesProto.Direction.DOWN);
                break;
            }
        }
    }


    public void showMessage(String message) {
        viewBase.showMessage(message);
    }

    public void closeGameFrame() {
        viewBase.disconnect();
    }

    public void disconnect() {
        mainThread.disconnect();
        mainThread.stop();
        mainThread = null;
    }

    public void stop() {
        listener.setStopped();
        gameShower.setStopped();
        if (mainThread != null) {
            mainThread.stop();
        }
    }
}
