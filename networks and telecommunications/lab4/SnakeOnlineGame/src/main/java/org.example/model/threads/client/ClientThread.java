package org.example.model.threads.client;

import org.example.model.FieldInfo;
import org.example.model.GameInfo;
import org.example.model.Model;
import org.example.model.Player;
import org.example.model.threads.*;
import com.google.protobuf.InvalidProtocolBufferException;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.LogRecord;
import protobuf.SnakesProto;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;

public class ClientThread extends Thread implements GameThread {
    private static final Logger logger = Logger.getLogger(ClientThread.class.getSimpleName());
    private final DatagramSocket socket;
    private final MainThread mainThread;
    private boolean isRunning = true;
    private final Model model;
    private PingThread pingThread;
    private final MessagesRepeaterThread repeaterThread;
    private final AFKCheckerThread afkCheckerThread;
    private final FieldInfo fieldInfo;
    private final GameInfo gameInfo;
    private final String playerName;
    private int ID;
    private final AtomicLong newMSGSeq = new AtomicLong(0);
    private boolean initialReceiving;
    private final List<SnakesProto.GameMessage> messagesQueue;
    private SnakesProto.NodeRole role;

    public ClientThread(MainThread main, DatagramSocket socket,
                        Model model, GameInfo gameInfo, FieldInfo fieldInfo, String playerName) {
        this.socket = socket;
        this.model = model;
        this.gameInfo = gameInfo;
        this.playerName = playerName;
        this.mainThread = main;
        messagesQueue = new ArrayList<>();
        repeaterThread = new MessagesRepeaterThread(this, messagesQueue,
                gameInfo.getConfig().getStateDelayMs() / 10);
        repeaterThread.start();
        afkCheckerThread = new AFKCheckerThread(this, (int) (gameInfo.getConfig().getStateDelayMs() * 0.8));
        this.fieldInfo = fieldInfo;
    }

    @Override
    public void run() {
        while (isRunning) {
            DatagramPacket packet = new DatagramPacket(new byte[4096], 4096);
            try {
                socket.receive(packet);
            } catch (IOException e) {
                continue;
            }
            SnakesProto.GameMessage gameMessage;
            try {
                gameMessage = SnakesProto.GameMessage
                        .parseFrom(Arrays.copyOfRange(packet.getData(), 0, packet.getLength()));
                LogRecord record = new LogRecord(Level.INFO,
                        "received from: {0}, addr = {1}, msg type: {2}");
                record.setParameters(new Object[]{
                        packet.getSocketAddress(),
                        ((InetSocketAddress) packet.getSocketAddress()).getAddress(),
                        gameMessage.getTypeCase()
                });
                logger.log(record);
            } catch (InvalidProtocolBufferException e) {
                logger.info("{}: Client Thread couldn't parse a msg");
                continue;
            }
            switch (gameMessage.getTypeCase()) {
                case ROLE_CHANGE: {
                    afkCheckerThread.addSender(gameMessage.getSenderId());
                    if (role == SnakesProto.NodeRole.DEPUTY &&
                            gameMessage.getRoleChange().getReceiverRole() == SnakesProto.NodeRole.MASTER) {
                        becomeMaster();
                    }
                    if (gameMessage.getRoleChange().getReceiverRole() == SnakesProto.NodeRole.VIEWER) {
                        role = SnakesProto.NodeRole.VIEWER;
                        afkCheckerThread.setRole(SnakesProto.NodeRole.VIEWER);
                        SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                                .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                                .setSenderId(ID)
                                .setMsgSeq(gameMessage.getMsgSeq()).build();
                        sendMessage(answer, packet.getAddress().getHostAddress(), packet.getPort());
                    } else if (gameMessage.getRoleChange().getReceiverRole() == SnakesProto.NodeRole.DEPUTY) {
                        role = SnakesProto.NodeRole.DEPUTY;
                        afkCheckerThread.setRole(SnakesProto.NodeRole.DEPUTY);
                        SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                                .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                                .setSenderId(ID)
                                .setMsgSeq(gameMessage.getMsgSeq()).build();
                        sendMessage(answer, packet.getAddress().getHostAddress(), packet.getPort());
                    } else if (gameMessage.getRoleChange().getReceiverRole() == SnakesProto.NodeRole.NORMAL) {
                        gameInfo.setGameAddress(packet.getAddress().getHostAddress());
                        gameInfo.setGamePort(packet.getPort());
                        SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                                .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                                .setSenderId(ID)
                                .setMsgSeq(gameMessage.getMsgSeq()).build();
                        sendMessage(answer, packet.getAddress().getHostAddress(), packet.getPort());
                    }
                    LogRecord record = new LogRecord(Level.INFO, "received from: {0}, addr = {1},  msg type: {1}");
                    record.setParameters(new Object[]{packet.getSocketAddress(),
                            ((InetSocketAddress) packet.getSocketAddress()).getAddress(),
                            gameMessage.getTypeCase()});
                    break;
                }
                case STATE: {
                    afkCheckerThread.addSender(gameMessage.getSenderId());
                    SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                            .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                            .setSenderId(ID)
                            .setMsgSeq(gameMessage.getMsgSeq()).build();
                    sendMessage(answer, packet.getAddress().getHostAddress(), packet.getPort());
                    SnakesProto.GameState state = gameMessage.getState().getState();
                    fieldInfo.setField(state);
                    synchronized (fieldInfo.getPlayers()) {
                        model.drawField(fieldInfo.getPlayers(), fieldInfo.getFoods(), playerName);
                        fieldInfo.getPlayers().notifyAll();
                    }
                    break;
                }
                case ACK: {
                    if (initialReceiving) {
                        ID = gameMessage.getReceiverId();
                        pingThread = new PingThread(this, gameInfo.getConfig().getStateDelayMs() / 10);
                        pingThread.start();
                        initialReceiving = false;
                        synchronized (messagesQueue) {
                            messagesQueue.removeIf(message ->
                                    message.getMsgSeq() == gameMessage.getMsgSeq());
                        }
                    } else {
                        afkCheckerThread.addSender(gameMessage.getSenderId());
                        synchronized (messagesQueue) {
                            messagesQueue.removeIf(message ->
                                    message.getMsgSeq() == gameMessage.getMsgSeq());
                        }
                    }
                    break;
                }
                case ERROR: {
                    if (initialReceiving) {
                        model.showMessage("Unable to connect");
                        model.closeGameFrame();
                    } else {
                        model.showMessage(gameMessage.getError().getErrorMessage());
                    }
                    break;
                }
            }
        }
    }

    private void sendRoleChange(String address, int port) {
        SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage.newBuilder()
                .setRoleChange(
                        SnakesProto.GameMessage.RoleChangeMsg.newBuilder()
                                .setReceiverRole(SnakesProto.NodeRole.MASTER)
                                .setSenderRole(this.role).build()
                ).setSenderId(ID)
                .setMsgSeq(newMSGSeq.incrementAndGet())
                .build();
        synchronized (messagesQueue) {
            messagesQueue.add(gameMessage);
            messagesQueue.notifyAll();
        }
        sendMessage(gameMessage, address, port);
    }

    public void becomeMaster() {
        if (role != SnakesProto.NodeRole.MASTER) {
            role = SnakesProto.NodeRole.MASTER;
            mainThread.becomeMaster(ID);
        }
    }

    public void connectToGame(SnakesProto.NodeRole requestedRole) {
        SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage.newBuilder()
                .setJoin(
                        SnakesProto.GameMessage.JoinMsg.newBuilder()
                                .setGameName(gameInfo.getGameName())
                                .setRequestedRole(requestedRole)
                                .setPlayerName(playerName)
                )
                .setMsgSeq(newMSGSeq.incrementAndGet())
                .build();
        synchronized (messagesQueue) {
            messagesQueue.add(gameMessage);
            messagesQueue.notifyAll();
        }
        sendMessage(gameMessage, gameInfo.getGameAddress(), gameInfo.getGamePort());
        role = requestedRole;
        initialReceiving = true;
        afkCheckerThread.setRole(role);
        afkCheckerThread.start();
    }

    public void sendPing() {
        SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage.newBuilder()
                .setPing(
                        SnakesProto.GameMessage.PingMsg.getDefaultInstance()
                ).setSenderId(ID)
                .setMsgSeq(newMSGSeq.incrementAndGet())
                .build();
        synchronized (messagesQueue) {
            messagesQueue.add(gameMessage);
            messagesQueue.notifyAll();
        }
        sendMessage(gameMessage, gameInfo.getGameAddress(), gameInfo.getGamePort());
    }

    public void repeatMessage(SnakesProto.GameMessage message) {
        sendMessage(message, gameInfo.getGameAddress(), gameInfo.getGamePort());
    }

    public void makeMove(SnakesProto.Direction direction) {
        if (role == SnakesProto.NodeRole.VIEWER) {
            return;
        }
        SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage.newBuilder()
                .setSteer(
                        SnakesProto.GameMessage.SteerMsg.newBuilder()
                                .setDirection(direction)
                ).setSenderId(ID)
                .setMsgSeq(newMSGSeq.incrementAndGet())
                .build();
        sendMessage(gameMessage, gameInfo.getGameAddress(), gameInfo.getGamePort());
        synchronized (messagesQueue) {
            messagesQueue.add(gameMessage);
            messagesQueue.notifyAll();
        }
    }

    public void disconnect() {
        role = SnakesProto.NodeRole.VIEWER;
        sendRoleChange(gameInfo.getGameAddress(), gameInfo.getGamePort());
    }

    private void sendMessage(SnakesProto.GameMessage message, String address, int port) {
        byte[] data = message.toByteArray();
        DatagramPacket packet = new DatagramPacket(data, data.length);
        try {
            packet.setAddress(InetAddress.getByName(address));
            packet.setPort(port);
            socket.send(packet);
        } catch (IOException ignored) {
        }
    }

    public void changeMaster() {
        int deputyID = fieldInfo.getDeputyID();
        Player player = fieldInfo.getPlayerByID(deputyID);
        if (player == null) {
            model.showMessage("Master left the game and there is no deputy. Game ended");
            return;
        }
        player.setRole(SnakesProto.NodeRole.MASTER);
        gameInfo.setGameAddress(player.getAddress());
        gameInfo.setGamePort(player.getPort());
    }

    public void masterAsClient(int ID) {
        this.ID = ID;
        pingThread = new PingThread(this, gameInfo.getConfig().getStateDelayMs() / 10);
        pingThread.start();
        afkCheckerThread.setRole(SnakesProto.NodeRole.VIEWER);
        afkCheckerThread.start();
    }

    public int getMasterID() {
        return fieldInfo.getMasterID();
    }

    public List<Integer> getPlayersID() {
        return fieldInfo.getPlayersID();
    }

    public void setStopped() {
        isRunning = false;
        if (pingThread != null) {
            pingThread.setStopped();
            pingThread = null;
        }
        afkCheckerThread.setStopped();
        repeaterThread.setStopped();
    }
}
