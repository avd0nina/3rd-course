package org.example.model.threads;

import protobuf.SnakesProto;

public interface GameThread {
    void repeatMessage(SnakesProto.GameMessage gameMessage);
}
