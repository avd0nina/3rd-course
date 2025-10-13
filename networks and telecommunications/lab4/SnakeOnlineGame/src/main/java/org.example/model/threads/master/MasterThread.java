package org.example.model.threads.master;

import org.example.model.*;
import org.example.model.threads.*;
import com.google.protobuf.InvalidProtocolBufferException;
import java.util.logging.Level;
import java.util.logging.LogRecord;
import java.util.logging.Logger;
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

public class MasterThread extends Thread implements GameThread {
    private static final Logger logger = Logger.getLogger(MasterThread.class.getSimpleName());
    private boolean isRunning = true;
    private final DatagramSocket socket;
    private final Model model;
    private final MainThread mainThread;
    private AnnouncementThread announcementThread;
    private final MessagesRepeaterThread repeaterThread;
    private final AFKCheckerThread afkCheckerThread;
    private final FieldInfo fieldInfo;
    private final GameInfo gameInfo;
    private int newPlayerID = 1;
    private final String playerName;
    private final List<SnakesProto.GameMessage> messagesQueue;
    private int ID;
    private final AtomicLong newMSGSeq = new AtomicLong(0);
    private boolean haveDeputy = false;

    public MasterThread(MainThread main, DatagramSocket socket,
                        Model model, GameInfo gameInfo, FieldInfo fieldInfo, String playerName) {
        this.socket = socket;
        this.model = model;
        this.fieldInfo = fieldInfo;
        this.gameInfo = gameInfo;
        this.playerName = playerName;
        this.mainThread = main;
        messagesQueue = new ArrayList<>();
        repeaterThread = new MessagesRepeaterThread(this, messagesQueue,
                gameInfo.getConfig().getStateDelayMs() / 10);
        afkCheckerThread = new AFKCheckerThread(this, (int) (gameInfo.getConfig().getStateDelayMs() * 0.8));
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
            } catch (InvalidProtocolBufferException e) {
                logger.info("{}: Server couldn't parse a msg");
                continue;
            }
            switch (gameMessage.getTypeCase()) {
                case STEER: {
                    fieldInfo.addMove(new Movement(gameMessage.getSteer().getDirection(), gameMessage.getSenderId()));
                    SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                            .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                            .setReceiverId(gameMessage.getSenderId())
                            .setMsgSeq(gameMessage.getMsgSeq())
                            .build();
                    sendMessage(answer, packet.getAddress().getHostAddress(), packet.getPort());
                    fieldInfo.getPlayerByID(gameMessage.getSenderId()).setAlive();
                    break;
                }
                case ROLE_CHANGE: {
                    SnakesProto.GameMessage message = SnakesProto.GameMessage.newBuilder()
                            .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                            .setMsgSeq(gameMessage.getMsgSeq())
                            .setReceiverId(gameMessage.getSenderId())
                            .build();
                    sendMessage(message, packet.getAddress().getHostAddress(), packet.getPort());
                    Player player = fieldInfo.getPlayerByID(gameMessage.getSenderId());
                    if (player == null) {
                        break;
                    }
                    if (gameMessage.getRoleChange().getSenderRole() == SnakesProto.NodeRole.VIEWER) {
                        if (player.getRole() == SnakesProto.NodeRole.DEPUTY) {
                            synchronized (fieldInfo.getPlayers()) {
                                haveDeputy = false;
                                for (Player player1 : fieldInfo.getPlayers()) {
                                    if (player1.getRole() == SnakesProto.NodeRole.NORMAL) {
                                        player1.setRole(SnakesProto.NodeRole.DEPUTY);
                                        sendRoleChange(SnakesProto.NodeRole.DEPUTY,
                                                player1.getAddress(), player1.getPort());
                                        haveDeputy = true;
                                        break;
                                    }
                                }
                                fieldInfo.getPlayers().notifyAll();
                            }
                            setPlayerZombie(player.getID());
                        } else if (player.getRole() == SnakesProto.NodeRole.NORMAL ||
                                player.getRole() == SnakesProto.NodeRole.VIEWER) {
                            setPlayerZombie(player.getID());
                        }
                    }
                    break;
                }
                case JOIN: {
                    receiveJoin(gameMessage, packet.getAddress().getHostAddress(), packet.getPort());
                    break;
                }
                case PING: {
                    afkCheckerThread.addSender(gameMessage.getSenderId());
                    Player player = fieldInfo.getPlayerByID(gameMessage.getSenderId());
                    player.setAddress(packet.getAddress().getHostAddress());
                    player.setPort(packet.getPort());
                    player.setAlive();
                    SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                            .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                            .setSenderId(ID)
                            .setMsgSeq(gameMessage.getMsgSeq()).build();
                    sendMessage(answer, packet.getAddress().getHostAddress(), packet.getPort());
                    break;
                }
                case ACK: {
                    afkCheckerThread.addSender(gameMessage.getSenderId());
                    synchronized (messagesQueue) {
                        messagesQueue.removeIf(message ->
                                message.getReceiverId() == gameMessage.getSenderId() &&
                                        message.getMsgSeq() == gameMessage.getMsgSeq());
                    }
                }
            }
        }
    }

    private void receiveJoin(SnakesProto.GameMessage gameMessage, String senderAddress, int senderPort) {
        SnakesProto.GameMessage.JoinMsg message = gameMessage.getJoin();
        SnakesProto.GamePlayer playerInfo = SnakesProto.GamePlayer
                .newBuilder()
                .setName(message.getPlayerName())
                .setId(newPlayerID)
                .setRole(message.getRequestedRole())
                .setScore(0)
                .setType(message.hasPlayerType() ? message.getPlayerType() : SnakesProto.PlayerType.HUMAN).build();
        Player player = new Player(newPlayerID, message.getPlayerName());
        player.setRole(message.getRequestedRole());
        player.setScore(0);
        if (player.getRole() == SnakesProto.NodeRole.VIEWER) {
            player.setSnake(null);
        }
        if (fieldInfo.addPlayer(player) == 1) {
            SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                    .setError(
                            SnakesProto.GameMessage.ErrorMsg.newBuilder()
                                    .setErrorMessage("Unable to enter the game")
                    )
                    .setMsgSeq(gameMessage.getMsgSeq()).build();
            sendMessage(answer, senderAddress, senderPort);
        } else {
            SnakesProto.GameMessage answer = SnakesProto.GameMessage.newBuilder()
                    .setAck(SnakesProto.GameMessage.AckMsg.getDefaultInstance())
                    .setReceiverId(newPlayerID)
                    .setMsgSeq(gameMessage.getMsgSeq()).build();
            newPlayerID++;
            announcementThread.addPlayer(playerInfo);
            announcementThread.updateAnnouncement();
            player.setAddress(senderAddress);
            player.setPort(senderPort);
            sendMessage(answer, senderAddress, senderPort);
            if (!haveDeputy) {
                player.setRole(SnakesProto.NodeRole.DEPUTY);
                haveDeputy = true;
                sendRoleChange(SnakesProto.NodeRole.DEPUTY, senderAddress, senderPort);
            }
        }
    }

    public void newGame() {
        ID = 0;
        fieldInfo.newGame();
        announcementThread = new AnnouncementThread(this);
        Player player = new Player(0, playerName);
        player.setAddress("127.0.0.1");
        player.setPort(8000);
        player.setRole(SnakesProto.NodeRole.MASTER);
        fieldInfo.addPlayer(player);
        announcementThread.addPlayer(SnakesProto.GamePlayer.newBuilder()
                .setType(SnakesProto.PlayerType.HUMAN)
                .setName(playerName)
                .setId(0)
                .setRole(SnakesProto.NodeRole.MASTER)
                .setScore(0).build());
        announcementThread.createAnnouncement(gameInfo.getGameName());
        announcementThread.start();
        afkCheckerThread.setRole(SnakesProto.NodeRole.MASTER);
        afkCheckerThread.start();
        repeaterThread.start();
        fieldInfo.masterStart();
    }

    public void becomeMaster(int ID) {
        this.ID = ID;
        announcementThread = new AnnouncementThread(this);
        haveDeputy = false;
        synchronized (fieldInfo.getPlayers()) {
            for (Player player : fieldInfo.getPlayers()) {
                newPlayerID = player.getID();
                if (player.getID() == fieldInfo.getMasterID()) {
                    player.setRole(SnakesProto.NodeRole.VIEWER);
                }
                announcementThread.addPlayer(SnakesProto.GamePlayer.newBuilder()
                        .setType(SnakesProto.PlayerType.HUMAN)
                        .setName(player.getNickname())
                        .setId(player.getID())
                        .setRole(player.getRole())
                        .setScore(player.getScore()).build());
                sendRoleChange(player.getRole(), player.getAddress(), player.getPort());
            }
            for (Player player : fieldInfo.getPlayers()) {
                if (player.getRole() == SnakesProto.NodeRole.NORMAL) {
                    player.setRole(SnakesProto.NodeRole.DEPUTY);
                    sendRoleChange(SnakesProto.NodeRole.DEPUTY,
                            player.getAddress(), player.getPort());
                    haveDeputy = true;
                    break;
                }
            }
        }
        fieldInfo.getPlayerByID(ID).setRole(SnakesProto.NodeRole.MASTER);
        newPlayerID++;
        announcementThread.createAnnouncement(gameInfo.getGameName());
        announcementThread.start();
        afkCheckerThread.setRole(SnakesProto.NodeRole.MASTER);
        afkCheckerThread.start();
        repeaterThread.start();
        fieldInfo.masterStart();
    }

    public void sendLose(int playerID) {
        Player player = fieldInfo.getPlayerByID(playerID);
        if (player.getNickname().equals(playerName)) {
            model.showMessage("You lost. Your score: " + player.getScore());
            Player deputy = getDeputy();
            if (deputy != null) {
                sendRoleChange(SnakesProto.NodeRole.MASTER, deputy.getAddress(), deputy.getPort());
                SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage.newBuilder()
                        .setRoleChange(
                                SnakesProto.GameMessage.RoleChangeMsg.newBuilder()
                                        .setReceiverRole(SnakesProto.NodeRole.MASTER)
                                        .setSenderRole(SnakesProto.NodeRole.VIEWER).build()
                        ).setSenderId(ID)
                        .setMsgSeq(newMSGSeq.incrementAndGet())
                        .build();
                synchronized (messagesQueue) {
                    messagesQueue.add(gameMessage);
                    messagesQueue.notifyAll();
                }
                sendMessage(gameMessage, deputy.getAddress(), deputy.getPort());
                mainThread.masterLost(ID);
            }
        } else {
            SnakesProto.GameMessage errorMessage = SnakesProto.GameMessage.newBuilder()
                    .setError(SnakesProto.GameMessage.ErrorMsg.newBuilder()
                            .setErrorMessage("You lost. Your score: " + player.getScore()))
                    .setReceiverId(playerID)
                    .setMsgSeq(newMSGSeq.incrementAndGet())
                    .build();
            sendMessage(errorMessage, player.getAddress(), player.getPort());
            sendRoleChange(SnakesProto.NodeRole.VIEWER, player.getAddress(), player.getPort());
        }
    }

    public void repeatMessage(SnakesProto.GameMessage message) {
        Player player = fieldInfo.getPlayerByID(message.getReceiverId());
        if (player == null) {
            return;
        }
        sendMessage(message, player.getAddress(), player.getPort());
    }

    public void sendAnnounce(SnakesProto.GameAnnouncement gameAnnouncement) {
        SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage
                .newBuilder()
                .setAnnouncement(
                        SnakesProto.GameMessage.AnnouncementMsg
                                .newBuilder().addGames(gameAnnouncement).build()
                )
                .setMsgSeq(0)
                .build();
        sendMessage(gameMessage, "239.192.0.4", 9192);
    }

    private void sendRoleChange(SnakesProto.NodeRole newRole, String address, int port) {
        SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage.newBuilder()
                .setRoleChange(
                        SnakesProto.GameMessage.RoleChangeMsg.newBuilder()
                                .setReceiverRole(newRole)
                                .setSenderRole(SnakesProto.NodeRole.MASTER).build()
                ).setSenderId(ID)
                .setMsgSeq(newMSGSeq.incrementAndGet())
                .build();
        synchronized (messagesQueue) {
            messagesQueue.add(gameMessage);
            messagesQueue.notifyAll();
        }
        sendMessage(gameMessage, address, port);
    }

    public void updateState() {
        SnakesProto.GameMessage message;
        List<SnakesProto.GameMessage> addingMessages = new ArrayList<>();
        synchronized (fieldInfo.getPlayers()) {
            model.drawField(fieldInfo.getPlayers(), fieldInfo.getFoods(), playerName);
            message = SnakesProto.GameMessage.newBuilder()
                    .setState(
                            SnakesProto.GameMessage.StateMsg.newBuilder()
                                    .setState(fieldInfo.getGameState())
                    )
                    .setSenderId(ID)
                    .setMsgSeq(newMSGSeq.incrementAndGet())
                    .build();
            for (Player player : fieldInfo.getPlayers()) {
                if (!player.getNickname().equals(playerName) || !player.isDisconnected()) {
                    message.toBuilder().setReceiverId(player.getID());
                    addingMessages.add(message);
                    sendMessage(message, player.getAddress(), player.getPort());
                }
            }
            fieldInfo.getPlayers().notifyAll();
        }
        synchronized (messagesQueue) {
            messagesQueue.addAll(addingMessages);
            messagesQueue.notifyAll();
        }
    }

    private void sendMessage(SnakesProto.GameMessage message, String address, int port) {
        byte[] data = message.toByteArray();
        DatagramPacket packet = new DatagramPacket(data, data.length);
        try {
            packet.setAddress(InetAddress.getByName(address));
            packet.setPort(port);
            socket.send(packet);
            LogRecord record = new LogRecord(Level.INFO,
                    "send to: {0}, addr = {1}, msg type: {2}");
            record.setParameters(new Object[]{
                    packet.getSocketAddress(),
                    ((InetSocketAddress) packet.getSocketAddress()).getAddress(),
                    message.getTypeCase()
            });
            logger.log(record);
        } catch (IOException ignored) {
        }
    }

    public void makeMove(SnakesProto.Direction direction) {
        fieldInfo.addMove(new Movement(direction, ID));
    }

    public void setPlayerZombie(int playerID) {
        Player player = fieldInfo.getPlayerByID(playerID);
        if (player != null && !player.getNickname().equals(playerName) && player.isAlive()) {
            player.setZombie();
            player.setRole(SnakesProto.NodeRole.VIEWER);
            player.setDisconnected();
            announcementThread.deletePlayer(playerID);
            announcementThread.updateAnnouncement();
        }
    }

    public void disconnect() {
        if (haveDeputy) {
            Player deputy = getDeputy();
            if (deputy == null) {
                return;
            }
            sendRoleChange(SnakesProto.NodeRole.MASTER, deputy.getAddress(), deputy.getPort());
            gameInfo.setGameAddress(deputy.getAddress());
            gameInfo.setGamePort(deputy.getPort());
            SnakesProto.GameMessage gameMessage = SnakesProto.GameMessage.newBuilder()
                    .setRoleChange(
                            SnakesProto.GameMessage.RoleChangeMsg.newBuilder()
                                    .setReceiverRole(SnakesProto.NodeRole.MASTER)
                                    .setSenderRole(SnakesProto.NodeRole.VIEWER).build()
                    ).setSenderId(ID)
                    .setMsgSeq(newMSGSeq.incrementAndGet())
                    .build();

            synchronized (messagesQueue) {
                messagesQueue.add(gameMessage);
                messagesQueue.notifyAll();
            }
            try {
                sleep(1000);
            } catch (InterruptedException ignored) {
            }
            sendMessage(gameMessage, deputy.getAddress(), deputy.getPort());
        }
    }

    private Player getDeputy() {
        if (haveDeputy) {
            Player deputy = null;
            synchronized (fieldInfo.getPlayers()) {
                for (Player player : fieldInfo.getPlayers()) {
                    if (player.getRole() == SnakesProto.NodeRole.DEPUTY) {
                        deputy = player;
                        break;
                    }
                }
                fieldInfo.getPlayers().notifyAll();
            }
            return deputy;
        } else {
            return null;
        }
    }

    public List<Integer> getPlayersID() {
        return fieldInfo.getPlayersID();
    }

    public void setStopped() {
        isRunning = false;
        fieldInfo.masterStop();
        afkCheckerThread.setStopped();
        announcementThread.setStopped();
        repeaterThread.setStopped();
    }
}
