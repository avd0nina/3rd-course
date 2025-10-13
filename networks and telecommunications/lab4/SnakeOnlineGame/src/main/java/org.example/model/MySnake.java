package org.example.model;

import protobuf.SnakesProto;
import java.util.List;
import java.awt.*;

public class MySnake {
    private List<Point> points;
    private SnakesProto.Direction direction;

    public MySnake(List<Point> initialPoints, SnakesProto.Direction direction) {
        points = initialPoints;
        this.direction = direction;
    }

    public void setDirection(SnakesProto.Direction direction) {
        this.direction = direction;
    }

    public List<Point> getPoints() {
        return points;
    }

    public SnakesProto.Direction getDirection() {
        return direction;
    }
}
