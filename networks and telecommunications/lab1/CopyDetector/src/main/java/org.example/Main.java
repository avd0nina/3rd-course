package org.example;

import org.example.messages.ByeMessage;
import org.example.messages.HiMessage;

import java.net.InetAddress;
import java.net.MulticastSocket;
import java.util.LinkedList;
import java.util.List;
import java.util.Scanner;

public class Main {
    public static final int ERROR = 1;
    public static final int PORT = 9999;

    public static void main(String[] args) {
        System.out.println("Введите адрес мультикаст-группы (например, 239.0.0.1): ");
        Scanner scanner = new Scanner(System.in);
        final String multicastGroupAddressString = scanner.nextLine().trim();
        if (multicastGroupAddressString.isEmpty()) {
            System.err.println("Адрес мультикаст-группы не может быть пустым.");
            System.exit(ERROR);
        }
        try {
            final InetAddress multicastGroupAddress = InetAddress.getByName(multicastGroupAddressString);
            if (!multicastGroupAddress.isMulticastAddress()) {
                System.err.println("Введённый адрес должен быть мультикаст-адресом (например, 239.0.0.1).");
                System.exit(ERROR);
            }
            System.out.println("Используется адрес: " + multicastGroupAddressString);
            final MulticastSocket multicastSocket = new MulticastSocket(PORT);
            multicastSocket.joinGroup(multicastGroupAddress);
            final MessageSender sender = new DefaultMessageSender(multicastSocket, multicastGroupAddress, PORT);
            final MessageReceiver receiver = new DefaultMessageReceiver(multicastSocket);

            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                final Message byeMessage = new ByeMessage();
                try {
                    System.out.println("Отправка ByeMessage и завершение...");
                    sender.sendMessage(byeMessage);
                    multicastSocket.leaveGroup(multicastGroupAddress);
                    multicastSocket.close();
                } catch (Exception ignored) {
                }
            }));

            final Message hiMessage = new HiMessage();
            System.out.println("Отправка HiMessage...");
            sender.sendMessage(hiMessage);
            final List<AppCopy> liveAppCopies = new LinkedList<>();
            System.out.println("Ожидание сообщений от других копий...");
            while (true) {
                final Message message = receiver.receiveMessage();
                System.out.println("Получено сообщение: " + message.getClass().getSimpleName());
                message.handle(liveAppCopies, sender, receiver);
            }
        } catch (Exception exception) {
            System.err.println("Ошибка: " + exception.getClass().getSimpleName() + ": " + exception.getMessage());
            exception.printStackTrace();
            System.exit(ERROR);
        } finally {
            scanner.close();
        }
    }
}
