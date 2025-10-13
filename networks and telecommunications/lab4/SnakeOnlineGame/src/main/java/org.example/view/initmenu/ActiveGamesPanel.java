package org.example.view.initmenu;

import org.example.view.ViewBase;
import org.example.model.GameInfo;
import javax.swing.*;
import java.awt.*;

public class ActiveGamesPanel extends JPanel {
    private final JScrollPane scrollPane;
    private final JPanel activeGames;

    public ActiveGamesPanel() {
        setPreferredSize(new Dimension(250, 300));
        setMinimumSize(new Dimension(250, 300));
        activeGames = new JPanel();
        activeGames.setLayout(new BoxLayout(activeGames, BoxLayout.Y_AXIS));
        scrollPane = new JScrollPane(activeGames);
        scrollPane.setPreferredSize(new Dimension(250, 275));
        scrollPane.setBorder(BorderFactory.createLineBorder(Color.BLACK));
        add(scrollPane);

    }

    public void removeGames() {
        activeGames.removeAll();
        activeGames.updateUI();
    }

    public void addGame(GameInfo info, ViewBase viewBase, JFrame parent) {
        activeGames.add(new AvailableGamesPanel(info, viewBase, parent));
    }

    public void draw() {
        scrollPane.revalidate();
    }
}
