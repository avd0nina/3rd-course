package org.example.view.gamepanel;

import org.example.view.ViewBase;
import org.example.model.GameInfo;
import org.example.model.Player;
import protobuf.SnakesProto;
import javax.swing.*;
import java.awt.*;
import java.awt.event.KeyEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.Comparator;
import java.util.List;

public class GameFrame {
    private final ViewBase viewBase;
    private final JFrame mainWindow;
    private FieldPanel field;
    private PlayerScorePanel playerArea;

    private class MyDispatcher implements KeyEventDispatcher {
        @Override
        public boolean dispatchKeyEvent(KeyEvent e) {
            if (e.getID() == KeyEvent.KEY_PRESSED || e.getID() == KeyEvent.KEY_TYPED) {
                viewBase.makeMove(e);
            }
            return false;
        }
    }

    public GameFrame(ViewBase viewBase, GameInfo gameInfo, int width, int height) {
        this.viewBase = viewBase;
        mainWindow = new JFrame("MySnake game :[" + gameInfo.getGameName() + "]");
        JPanel mainPanel = getMainPanel(width, height);
        mainWindow.setContentPane(mainPanel);
        mainWindow.setMinimumSize(new Dimension(1000, 850));
        mainWindow.setPreferredSize(new Dimension(1000, 850));
        mainWindow.addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                disconnect();
                super.windowClosing(e);
            }
        });
        mainWindow.setVisible(true);
        mainWindow.setLocationRelativeTo(null);
        KeyboardFocusManager.getCurrentKeyboardFocusManager().addKeyEventDispatcher(new MyDispatcher());
    }

    public void drawField(List<Player> players, List<Point> foods, String playerName) {
        playerArea.removeAll();
        List<Player> updatedScoreList = players.stream().sorted(Comparator.comparing(Player::getScore).reversed()
                .thenComparing(Player::getNickname)).toList();
        for (Player player : updatedScoreList) {
            if (!player.isAlive()) {
                playerArea.addPlayer(player.getColor(), player.getNickname() + " " + player.getRole(), player.getScore());
            } else if (player.getRole() == SnakesProto.NodeRole.VIEWER && player.getSnake() == null) {
            } else if (player.getNickname().equals(playerName)) {
                playerArea.addPlayer(player.getColor(), "you: " + player.getNickname() + " " + player.getRole(), player.getScore());
            } else if (player.getRole() == SnakesProto.NodeRole.MASTER) {
                playerArea.addPlayer(player.getColor(), player.getNickname() + " " + player.getRole(), player.getScore());
            } else {
                playerArea.addPlayer(player.getColor(), player.getNickname() + " " + player.getRole(), player.getScore());
            }
        }
        playerArea.draw();
        field.updateField(updatedScoreList, foods);
    }

    private JPanel getMainPanel(int width, int height) {
        JPanel panel = new JPanel(new BorderLayout());
        field = new FieldPanel(width, height);
        panel.add(field, BorderLayout.WEST);
        field.updateConstants();
        JPanel rightPanel = new JPanel(new BorderLayout());
        rightPanel.setPreferredSize(new Dimension(150, 400));
        playerArea = new PlayerScorePanel();
        rightPanel.add(playerArea, BorderLayout.NORTH);
        JButton backButton = new JButton("Back");
        backButton.setBackground(Color.decode("#390040"));
        backButton.setForeground(Color.WHITE);
        backButton.setActionCommand("back");
        backButton.addActionListener(e -> handleBackButton());
        backButton.setFont(new Font("Comic Sans MS", Font.PLAIN, 16));
        rightPanel.add(backButton, BorderLayout.SOUTH);
        panel.add(rightPanel, BorderLayout.CENTER);
        return panel;
    }

    public void close() {
        mainWindow.dispose();
    }

    private void handleBackButton() {
        disconnect();
    }

    private void disconnect() {
        viewBase.disconnect();
    }

    public void showMessage(String message) {
        SwingUtilities.invokeLater(() -> JOptionPane.showMessageDialog(mainWindow, message, "Error", JOptionPane.ERROR_MESSAGE));
    }
}
