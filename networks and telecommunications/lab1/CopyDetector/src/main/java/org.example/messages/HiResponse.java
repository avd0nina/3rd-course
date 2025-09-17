package org.example.messages;

import org.example.AppCopy;
import org.example.Message;
import org.example.MessageReceiver;
import org.example.MessageSender;

import java.util.List;

public class HiResponse extends Message {
    @Override
    public void handle(List<AppCopy> appCopies, MessageSender sender, MessageReceiver receiver) {
        appCopies.add(new AppCopy(getPid(), getAddress()));
    }
}
