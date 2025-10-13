package org.example.view.initmenu;

import org.example.view.ViewBase;
import org.example.model.GameInfo;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.List;

public class StartMenu implements ActionListener {
    private final ViewBase viewBase;
    private final JFrame mainWindow;
    private ActiveGamesPanel activeGames;

    public StartMenu(ViewBase viewBase) {
        this.viewBase = viewBase;
        mainWindow = new JFrame("MySnake");
        JPanel mainPanel = createStartPanelMenu();
        mainWindow.setContentPane(mainPanel);
        mainWindow.setResizable(false);
        mainWindow.setSize(new Dimension(600, 600));
        mainWindow.setLocationRelativeTo(null);
        mainWindow.addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                exit();
                super.windowClosing(e);
            }
        });
    }

    private JPanel createStartPanelMenu() {
        JPanel panel = new JPanel(new GridBagLayout());
        GridBagConstraints constraints = new GridBagConstraints();
        constraints.insets = new Insets(10, 10, 10, 10);
        JLabel title = new JLabel("MySnake Online");
        title.setFont(new Font("Arial", Font.BOLD, 28));
        title.setForeground(new Color(50, 100, 150));
        constraints.gridx = 0;
        constraints.gridy = 0;
        constraints.gridwidth = 2;
        panel.add(title, constraints);
        JLabel gamesTitle = new JLabel("Available Games");
        gamesTitle.setFont(new Font("Arial", Font.PLAIN, 18));
        gamesTitle.setForeground(new Color(70, 130, 180));
        constraints.gridy = 1;
        constraints.gridwidth = 2;
        panel.add(gamesTitle, constraints);
        activeGames = new ActiveGamesPanel();
        constraints.gridy = 2;
        constraints.gridwidth = 2;
        constraints.fill = GridBagConstraints.BOTH;
        panel.add(activeGames, constraints);
        JButton newGameButton = new JButton("New Game");
        newGameButton.setFont(new Font("Arial", Font.PLAIN, 16));
        newGameButton.setBackground(new Color(200, 220, 240));
        newGameButton.setForeground(Color.BLACK);
        newGameButton.addActionListener(this);
        newGameButton.setActionCommand("createGame");
        constraints.gridy = 3;
        constraints.gridwidth = 1;
        constraints.fill = GridBagConstraints.NONE;
        panel.add(newGameButton, constraints);
        JButton exitButton = new JButton("Exit");
        exitButton.setFont(new Font("Arial", Font.PLAIN, 16));
        exitButton.setBackground(new Color(200, 220, 240));
        exitButton.setForeground(Color.BLACK);
        exitButton.addActionListener(this);
        exitButton.setActionCommand("exitGame");
        constraints.gridx = 1;
        panel.add(exitButton, constraints);
        panel.setBackground(new Color(240, 245, 250));
        return panel;
    }

    public void showDialog(String message) {
        JOptionPane.showMessageDialog(mainWindow, message, "Info", JOptionPane.INFORMATION_MESSAGE);
    }

    public void showGames(List<GameInfo> games) {
        activeGames.removeGames();
        if (games.isEmpty()) {
            activeGames.draw();
        } else {
            for (GameInfo gameInfo : games) {
                activeGames.addGame(gameInfo, viewBase, mainWindow);
            }
            activeGames.draw();
        }
    }

    public void show() {
        mainWindow.setVisible(true);
    }

    public void dispose() {
        mainWindow.setVisible(false);
    }

    public void close() {
        mainWindow.dispose();
    }

    private void exit() {
        viewBase.exit();
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        String command = e.getActionCommand();
        if ("createGame".equals(command)) {
            NewGameWindow gameWindow = new NewGameWindow(viewBase);
            gameWindow.show();
        } else if ("exitGame".equals(command)) {
            int result = JOptionPane.showConfirmDialog(mainWindow,
                    "Are you sure you want to exit?", "Confirm Exit", JOptionPane.YES_NO_OPTION);
            if (result == JOptionPane.YES_OPTION) {
                System.exit(0);
            }
        }
    }
}
