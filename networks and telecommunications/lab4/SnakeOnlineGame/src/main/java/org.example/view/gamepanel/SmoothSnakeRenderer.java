package org.example.view.gamepanel;

import protobuf.SnakesProto;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

public class SmoothSnakeRenderer {
    public void drawSnake(Graphics2D g, List<FieldPanel.DoublePoint> points, SnakesProto.Direction direction, double cellSize, Point leftTop, Color color, int fieldWidth, int fieldHeight) {
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(color);
        g.setStroke(new BasicStroke((float) cellSize, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
        List<List<FieldPanel.DoublePoint>> segments = new ArrayList<>();
        List<FieldPanel.DoublePoint> currentSegment = new ArrayList<>();
        for (int i = 0; i < points.size(); i++) {
            FieldPanel.DoublePoint point = points.get(i);
            if (currentSegment.isEmpty()) {
                currentSegment.add(point);
            } else {
                FieldPanel.DoublePoint prev = currentSegment.get(currentSegment.size() - 1);
                if (Math.abs(point.x - prev.x) > fieldWidth / 2 || Math.abs(point.y - prev.y) > fieldHeight / 2) {
                    if (currentSegment.size() > 1) {
                        segments.add(new ArrayList<>(currentSegment));
                    }
                    currentSegment.clear();
                }
                currentSegment.add(point);
            }
        }

        if (!currentSegment.isEmpty() && currentSegment.size() > 1) {
            segments.add(currentSegment);
        }
        for (List<FieldPanel.DoublePoint> segment : segments) {
            for (int i = 0; i < segment.size() - 1; i++) {
                FieldPanel.DoublePoint current = segment.get(i);
                FieldPanel.DoublePoint next = segment.get(i + 1);
                double currentX = adjustCoordinate(current.x, fieldWidth, cellSize);
                double currentY = adjustCoordinate(current.y, fieldHeight, cellSize);
                double nextX = adjustCoordinate(next.x, fieldWidth, cellSize);
                double nextY = adjustCoordinate(next.y, fieldHeight, cellSize);
                int x1 = (int) (leftTop.x + currentX * cellSize + cellSize / 2);
                int y1 = (int) (leftTop.y + currentY * cellSize + cellSize / 2);
                int x2 = (int) (leftTop.x + nextX * cellSize + cellSize / 2);
                int y2 = (int) (leftTop.y + nextY * cellSize + cellSize / 2);
                g.drawLine(x1, y1, x2, y2);
            }
        }
        if (!points.isEmpty()) {
            Color headColor = color.darker();
            g.setColor(headColor);
            FieldPanel.DoublePoint head = points.get(0);
            double headX = adjustCoordinate(head.x, fieldWidth, cellSize);
            double headY = adjustCoordinate(head.y, fieldHeight, cellSize);
            double headScreenX = leftTop.x + headX * cellSize;
            double headScreenY = leftTop.y + headY * cellSize;
            g.fillOval((int) headScreenX, (int) headScreenY, (int) cellSize, (int) cellSize);
        }
    }

    private double adjustCoordinate(double coord, int fieldSize, double cellSize) {
        if (coord < 0) {
            return coord + fieldSize;
        } else if (coord >= fieldSize) {
            return coord - fieldSize;
        }
        return coord;
    }
}
