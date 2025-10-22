package org.example.view.initmenu;

import org.example.view.ViewBase;
import org.example.model.GameInfo;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class AvailableGamesPanel extends JPanel implements ActionListener {
    private final GameInfo gameInfo;
    private final ViewBase viewBase;
    private final JFrame mainWindow;

    public AvailableGamesPanel(GameInfo game, ViewBase viewBase, JFrame parent) {
        setLayout(new GridBagLayout());
        GridBagConstraints constraints = new GridBagConstraints();
        this.viewBase = viewBase;
        this.gameInfo = game;
        mainWindow = parent;
        constraints.insets = new Insets(2, 5, 2, 5);
        JLabel gameNameLabel = new JLabel(game.getGameName());
        gameNameLabel.setFont(new Font("Arial", Font.BOLD, 12));
        gameNameLabel.setHorizontalAlignment(SwingConstants.LEFT);
        constraints.gridy = 0;
        constraints.gridx = 0;
        constraints.gridwidth = 2;
        constraints.weightx = 1.0;
        constraints.anchor = GridBagConstraints.WEST;
        add(gameNameLabel, constraints);
        JLabel playersLabel = new JLabel("Players count: " + game.getPlayerCount());
        playersLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        gameNameLabel.setHorizontalAlignment(SwingConstants.LEFT);
        constraints.gridy = 1;
        constraints.gridx = 0;
        constraints.gridwidth = 1;
        constraints.weightx = 0.7;
        add(playersLabel, constraints);
        JButton button = new JButton("Join");
        button.setActionCommand("joinGame");
        button.addActionListener(this);
        button.setSize(30, 30);
        button.setBackground(Color.WHITE);
        button.setForeground(Color.BLACK);
        constraints.gridx = 3;
        add(button, constraints);
        setPreferredSize(new Dimension(200, 50));
        this.setBorder(BorderFactory.createLineBorder(Color.BLACK));
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        if (e.getActionCommand().equals("joinGame")) {
            String playerName = JOptionPane.showInputDialog(mainWindow, "Enter your name");
            viewBase.enterGame(gameInfo, playerName);
        }
    }
}
