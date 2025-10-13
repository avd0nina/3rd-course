package org.example.view.gamepanel;

import org.example.model.MySnake;
import org.example.model.Player;
import protobuf.SnakesProto;
import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.List;

public class FieldPanel extends JPanel {
    private BufferedImage image;
    private final int width;
    private final int height;
    private double cellSize;
    private Point leftTop;
    private Point leftBottom;
    private Point rightTop;
    private Point rightBottom;
    private SmoothSnakeRenderer snakeRenderer;

    public static class DoublePoint {
        double x, y;

        DoublePoint(double x, double y) {
            this.x = x;
            this.y = y;
        }
    }

    private class SnakeState {
        Color color;
        SnakesProto.Direction direction;
        List<DoublePoint> previousPoints = new ArrayList<>();
        List<DoublePoint> targetPoints = new ArrayList<>();
    }

    private List<SnakeState> snakeStates = new ArrayList<>();
    private List<Point> currentFoods = new ArrayList<>();
    private float progress = 0.0f;
    private final float interpolationSpeed = 0.3f;
    private Timer animationTimer;

    public FieldPanel(int width, int height) {
        this.width = width;
        this.height = height;
        setPreferredSize(new Dimension(800, 800));
        snakeRenderer = new SmoothSnakeRenderer();
        animationTimer = new Timer(10, e -> {
            progress += interpolationSpeed;
            if (progress >= 1.0f) {
                progress = 0.0f;
                animationTimer.stop();
                for (SnakeState state : snakeStates) {
                    state.previousPoints = new ArrayList<>(state.targetPoints);
                }
            }
            repaint();
        });
    }

    public void updateConstants() {
        Dimension d = getPreferredSize();
        leftTop = new Point(0, 0);
        leftBottom = new Point(0, d.height);
        rightBottom = new Point(d.width, d.height);
        rightTop = new Point(d.width, 0);
        cellSize = Math.min((double) (rightTop.x - leftTop.x) / width,
                (double) (rightBottom.y - rightTop.y) / height);
    }

    public void updateField(List<Player> players, List<Point> foods) {
        for (Player player : players) {
            MySnake snake = player.getSnake();
            if (snake != null) {
                boolean found = false;
                for (SnakeState state : snakeStates) {
                    if (state.color.equals(player.getColor())) {
                        state.targetPoints.clear();
                        List<Point> snakePoints = new ArrayList<>(snake.getPoints());
                        for (Point p : snakePoints) {
                            int newX = p.x;
                            int newY = p.y;
                            if (newX < 0) newX = width - 1; 
                            else if (newX >= width) newX = 0; 
                            if (newY < 0) newY = height - 1; 
                            else if (newY >= height) newY = 0; 
                            state.targetPoints.add(new DoublePoint(newX, newY));
                        }
                        state.direction = snake.getDirection();
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    SnakeState newState = new SnakeState();
                    newState.color = player.getColor();
                    newState.direction = snake.getDirection();
                    for (Point p : snake.getPoints()) {
                        int newX = p.x;
                        int newY = p.y;
                        if (newX < 0) newX = width - 1;
                        else if (newX >= width) newX = 0;
                        if (newY < 0) newY = height - 1;
                        else if (newY >= height) newY = 0;
                        newState.targetPoints.add(new DoublePoint(newX, newY));
                        newState.previousPoints.add(new DoublePoint(newX, newY));
                    }
                    snakeStates.add(newState);
                }
            }
        }
        snakeStates.removeIf(state -> players.stream().noneMatch(p -> p.getColor().equals(state.color) && p.getSnake() != null));
        currentFoods = new ArrayList<>(foods);
        progress = 0.0f;
        animationTimer.start();
    }

    private void drawBackgroundAndGrid(Graphics2D g) {
        g.setColor(Color.WHITE);
        g.fillRect(0, 0, getWidth(), getHeight());
        g.setColor(Color.BLACK); 
        for (int x = 0; x <= width; x++) {
            int xPos = (int) (leftTop.x + x * cellSize);
            g.drawLine(xPos, leftTop.y, xPos, (int) (leftTop.y + height * cellSize));
        }
        for (int y = 0; y <= height; y++) {
            int yPos = (int) (leftTop.y + y * cellSize);
            g.drawLine(leftTop.x, yPos, (int) (leftTop.x + width * cellSize), yPos);
        }
        g.setColor(Color.BLACK);
        g.setStroke(new BasicStroke(2));
        g.drawRect(leftTop.x, leftTop.y, (int) (width * cellSize), (int) (height * cellSize));
    }

    private void drawFood(Graphics2D g, Point point) {
        g.setColor(Color.RED);
        double x = leftTop.x + point.x * cellSize;
        double y = leftTop.y + point.y * cellSize;
        g.fillOval((int) x, (int) y, (int) cellSize, (int) cellSize);
    }

    private void drawSnake(Graphics2D g, SnakeState state) {
        List<DoublePoint> interpPoints = new ArrayList<>();
        for (int i = 0; i < state.targetPoints.size(); i++) {
            DoublePoint prev = state.previousPoints.get(i);
            DoublePoint target = state.targetPoints.get(i);
            double ix = prev.x + (target.x - prev.x) * progress;
            double iy = prev.y + (target.y - prev.y) * progress;
            interpPoints.add(new DoublePoint(ix, iy));
        }
        snakeRenderer.drawSnake(g, interpPoints, state.direction, cellSize, leftTop, state.color, width, height);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        image = new BufferedImage(getWidth(), getHeight(), BufferedImage.TYPE_INT_RGB);
        Graphics2D g2d = image.createGraphics();
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        drawBackgroundAndGrid(g2d);
        for (Point food : currentFoods) {
            drawFood(g2d, food);
        }
        for (SnakeState state : snakeStates) {
            drawSnake(g2d, state);
        }
        g2d.dispose();
        g.drawImage(image, 0, 0, this);
    }
}
