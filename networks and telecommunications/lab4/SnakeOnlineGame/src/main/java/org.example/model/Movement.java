package org.example.model;

import protobuf.SnakesProto;

public record Movement(SnakesProto.Direction direction, int playerID) {
}
