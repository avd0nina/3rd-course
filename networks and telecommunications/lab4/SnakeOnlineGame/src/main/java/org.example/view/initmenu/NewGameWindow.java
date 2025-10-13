package org.example.view.initmenu;

import org.example.view.ViewBase;
import javax.swing.*;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class NewGameWindow implements ActionListener {
    private final ViewBase viewBase;
    private final JFrame mainWindow;
    private final JTextArea playerName;

    public NewGameWindow(ViewBase viewBase) {
        this.viewBase = viewBase;
        mainWindow = new JFrame("Create a Game");
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(Color.WHITE);
        GridBagConstraints constraints = new GridBagConstraints();
        constraints.insets = new Insets(10, 10, 10, 10);
        JLabel playerNameTitle = new JLabel("Your Name:");
        playerNameTitle.setFont(new Font("Arial", Font.BOLD, 16));
        playerNameTitle.setForeground(Color.BLACK);
        constraints.gridx = 0;
        constraints.gridy = 0;
        panel.add(playerNameTitle, constraints);
        playerName = new JTextArea(1, 20);
        playerName.setFont(new Font("Arial", Font.PLAIN, 16));
        playerName.setForeground(Color.BLACK);
        playerName.setBackground(Color.WHITE);
        playerName.setCaretColor(Color.BLACK);
        playerName.setBorder(new LineBorder(Color.DARK_GRAY, 1));
        playerName.setLineWrap(true);
        playerName.setWrapStyleWord(true);
        JScrollPane scrollPane = new JScrollPane(playerName);
        scrollPane.setPreferredSize(new Dimension(200, 30));
        scrollPane.setBorder(new LineBorder(Color.DARK_GRAY, 1));
        constraints.gridx = 1;
        panel.add(scrollPane, constraints);
        JButton backButton = new JButton("Back");
        backButton.setFont(new Font("Arial", Font.PLAIN, 14));
        backButton.setBackground(new Color(200, 220, 240));
        backButton.setForeground(Color.BLACK);
        backButton.setActionCommand("back");
        backButton.addActionListener(this);
        constraints.gridx = 0;
        constraints.gridy = 1;
        panel.add(backButton, constraints);
        JButton startButton = new JButton("Start");
        startButton.setFont(new Font("Arial", Font.PLAIN, 14));
        startButton.setBackground(new Color(150, 200, 230));
        startButton.setForeground(Color.BLACK);
        startButton.setActionCommand("create");
        startButton.addActionListener(this);
        constraints.gridx = 1;
        panel.add(startButton, constraints);
        mainWindow.setContentPane(panel);
        mainWindow.setSize(new Dimension(400, 200));
        mainWindow.setLocationRelativeTo(null);
        SwingUtilities.invokeLater(() -> {
            playerName.requestFocusInWindow();
        });
    }

    public void show() {
        mainWindow.setVisible(true);
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        if (e.getActionCommand().equals("create")) {
            String cleanedPlayerName = playerName.getText().trim().replaceAll("\\s+", " ");
            System.out.println("Creating game with player name: '" + cleanedPlayerName + "'");
            if (cleanedPlayerName.isEmpty()) {
                JOptionPane.showMessageDialog(mainWindow,
                        "Please enter a valid player name.",
                        "Error", JOptionPane.ERROR_MESSAGE);
            } else {
                viewBase.createGame("Game_" + System.currentTimeMillis(), cleanedPlayerName);
                mainWindow.dispose();
            }
        } else if (e.getActionCommand().equals("back")) {
            mainWindow.dispose();
        }
    }
}
