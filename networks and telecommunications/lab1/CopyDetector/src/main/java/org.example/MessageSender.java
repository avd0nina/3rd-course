package org.example;

import java.io.IOException;

public interface MessageSender {
    void sendMessage(final Message message) throws IOException;
}
