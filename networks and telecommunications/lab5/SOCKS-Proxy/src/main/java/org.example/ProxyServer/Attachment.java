package org.example.ProxyServer;

import lombok.Getter;
import lombok.Setter;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;

@Getter
@Setter
public class Attachment {
    public static final int AUTH = 1;
    public static final int REQUEST = 2;
    public static final int BUFFER_SIZE = 8192;
    private ByteBuffer inputBuffer;
    private ByteBuffer outputBuffer;
    private SelectionKey dstKey;
    private int status;

    public Attachment() {
        this.inputBuffer = ByteBuffer.allocate(BUFFER_SIZE);
        this.outputBuffer = ByteBuffer.allocate(BUFFER_SIZE);
        status = AUTH;
    }
}
