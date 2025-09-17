package org.example;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.net.DatagramPacket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.MulticastSocket;

public class DefaultMessageSender implements MessageSender {
    private final MulticastSocket multicastSocket;
    private final InetAddress multicastGroupAddress;
    private final int port;
    private final String scopeId;

    public DefaultMessageSender(MulticastSocket multicastSocket, InetAddress multicastGroupAddress, int port, String scopeId) {
        this.multicastSocket = multicastSocket;
        this.multicastGroupAddress = multicastGroupAddress;
        this.port = port;
        this.scopeId = scopeId;
    }

    @Override
    public void sendMessage(Message message) throws IOException {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        ObjectOutputStream objectOutputStream = new ObjectOutputStream(byteArrayOutputStream);
        objectOutputStream.writeObject(message);
        objectOutputStream.flush();
        byte[] buffer = byteArrayOutputStream.toByteArray();

        InetSocketAddress destination;
        if (multicastGroupAddress instanceof java.net.Inet6Address && scopeId != null) {
            destination = new InetSocketAddress(InetAddress.getByName(multicastGroupAddress.getHostAddress() + "%" + scopeId), port);
        } else {
            destination = new InetSocketAddress(multicastGroupAddress, port);
        }

        DatagramPacket datagramPacket = new DatagramPacket(buffer, buffer.length, destination);
        multicastSocket.send(datagramPacket);
    }
}
