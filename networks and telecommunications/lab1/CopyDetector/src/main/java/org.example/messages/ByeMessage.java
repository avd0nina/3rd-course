package org.example.messages;

import org.example.*;

import java.util.List;

public class ByeMessage extends Message {
    @Override
    public void handle(List<AppCopy> appCopies, MessageSender sender, MessageReceiver receiver) {
        for (final var it : appCopies) {
            if (it.pid() == getPid()) {
                appCopies.remove(it);
                break;
            }
        }
        MessageUtils.printAppCopies(appCopies);
    }
}
