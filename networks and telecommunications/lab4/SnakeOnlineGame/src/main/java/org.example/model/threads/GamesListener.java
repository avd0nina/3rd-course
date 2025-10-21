package org.example.model.threads;

import org.example.model.GameInfo;
import org.example.model.Model;
import com.google.protobuf.InvalidProtocolBufferException;
import protobuf.SnakesProto;
import java.io.IOException;
import java.net.*;
import java.util.Arrays;
import java.util.logging.Logger;

public class GamesListener extends Thread {
    private static final Logger logger = Logger.getLogger(GamesListener.class.getSimpleName());
    private final MulticastSocket server;
    private boolean isRunning = true;
    private final Model model;

    public GamesListener(Model model) throws IOException {
        int MULTICAST_PORT = 9192;
        server = new MulticastSocket(MULTICAST_PORT);
        String MULTICAST_ADDRESS = "239.192.0.4";
        InetAddress multicastAddress = InetAddress.getByName(MULTICAST_ADDRESS);
        NetworkInterface networkInterface = null;
        server.joinGroup(new java.net.InetSocketAddress(multicastAddress, MULTICAST_PORT), networkInterface);
        server.setSoTimeout(1000);
        this.model = model;
    }

    @Override
    public void run() {
        while (isRunning) {
            DatagramPacket packet = new DatagramPacket(new byte[1500], 1500);
            try {
                server.receive(packet);
            } catch (SocketTimeoutException e) {
                continue;
            } catch (IOException e) {
                logger.info("{}: Server couldn't receive a packet");
                continue;
            }
            SnakesProto.GameMessage message;
            try {
                byte[] data = packet.getData();
                message = SnakesProto.GameMessage.parseFrom(Arrays.copyOfRange(data, 0, packet.getLength()));
            } catch (InvalidProtocolBufferException e) {
                logger.info("{}: Server couldn't parse a msg");
                continue;
            }
            if (message.getTypeCase() != SnakesProto.GameMessage.TypeCase.ANNOUNCEMENT) {
                continue;
            }
            var games = message.getAnnouncement().getGamesList();
            for (SnakesProto.GameAnnouncement gameAnnouncement : games) {
                if (gameAnnouncement.hasCanJoin() && !gameAnnouncement.getCanJoin()) {
                    continue;
                }
                GameInfo gameInfo = new GameInfo(gameAnnouncement);
                gameInfo.setGameAddress(packet.getAddress().getHostAddress());
                gameInfo.setGamePort(packet.getPort());
                model.addActiveGame(gameInfo);
            }
        }
    }

    public void setStopped() {
        isRunning = false;
    }
}
