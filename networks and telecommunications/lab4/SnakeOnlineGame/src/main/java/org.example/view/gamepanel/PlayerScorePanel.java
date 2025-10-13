package org.example.view.gamepanel;

import javax.swing.*;
import java.awt.*;

public class PlayerScorePanel extends JPanel {
    private final JPanel players;
    private final JScrollPane scrollPane;

    public PlayerScorePanel() {
        setLayout(new BorderLayout());
        setPreferredSize(new Dimension(200, 500));
        setMinimumSize(new Dimension(200, 500));
        players = new JPanel();
        players.setLayout(new BoxLayout(players, BoxLayout.Y_AXIS));
        scrollPane = new JScrollPane(players);
        add(scrollPane, BorderLayout.CENTER);
    }

    public void addPlayer(Color color, String nickname, int score) {
        JPanel playerPanel = new JPanel();
        playerPanel.setLayout(new BoxLayout(playerPanel, BoxLayout.X_AXIS));
        playerPanel.setMinimumSize(new Dimension(250, 50));
        JLabel nameLabel = new JLabel(nickname);
        nameLabel.setFont(new Font("Comic Sans MS", Font.PLAIN, 12));
        playerPanel.add(nameLabel);
        JLabel scoreLabel = new JLabel("  " + score + " ");
        scoreLabel.setFont(new Font("Comic Sans MS", Font.PLAIN, 12));
        playerPanel.add(scoreLabel);
        JPanel colorPanel = new JPanel();
        colorPanel.setBackground(color);
        colorPanel.setMaximumSize(new Dimension(30, 30));
        playerPanel.add(colorPanel);
        players.add(playerPanel);
    }

    public void removeAll() {
        players.removeAll();
        players.updateUI();
    }

    public void draw() {
        scrollPane.revalidate();
    }
}
