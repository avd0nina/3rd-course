package org.example;

import org.example.messages.ByeMessage;
import org.example.messages.HiMessage;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.MulticastSocket;
import java.net.NetworkInterface;
import java.util.Enumeration;
import java.util.LinkedList;
import java.util.List;
import java.util.Scanner;

public class Main {
    public static final int ERROR = 1;
    public static final int PORT = 9999;

    public static void main(String[] args) {
        String multicastGroupAddressString;
        if (args.length > 0) {
            multicastGroupAddressString = args[0].trim();
        } else {
            System.out.println("Введите адрес мультикаст-группы (например, 239.0.0.1 или ff02::1%lo0): ");
            Scanner scanner = new Scanner(System.in);
            multicastGroupAddressString = scanner.nextLine().trim();
            scanner.close();
        }

        if (multicastGroupAddressString.isEmpty()) {
            System.err.println("Адрес мультикаст-группы не может быть пустым.");
            System.exit(ERROR);
        }

        try {
            String scopeId = null;
            if (multicastGroupAddressString.contains("%")) {
                String[] parts = multicastGroupAddressString.split("%");
                multicastGroupAddressString = parts[0];
                scopeId = parts[1];
            }

            final InetAddress multicastGroupAddress = InetAddress.getByName(multicastGroupAddressString);
            if (!multicastGroupAddress.isMulticastAddress()) {
                System.err.println("Введённый адрес должен быть мультикаст-адресом.");
                System.exit(ERROR);
            }

            System.out.println("Подключение к " + (multicastGroupAddress instanceof java.net.Inet6Address ? "IPv6" : "IPv4") + " мультикаст-группе...");
            final MulticastSocket multicastSocket = new MulticastSocket(PORT);
            multicastSocket.setLoopbackMode(false);

            NetworkInterface networkInterface = getNetworkInterface(multicastGroupAddress, scopeId);
            if (networkInterface == null) {
                System.err.println("Не удалось найти подходящий сетевой интерфейс.");
                System.exit(ERROR);
            }

            if (multicastGroupAddress instanceof java.net.Inet6Address) {
                multicastSocket.joinGroup(new InetSocketAddress(multicastGroupAddress, PORT), networkInterface);
            } else {
                multicastSocket.joinGroup(multicastGroupAddress);
            }

            final MessageSender sender = new DefaultMessageSender(multicastSocket, multicastGroupAddress, PORT, scopeId);
            final MessageReceiver receiver = new DefaultMessageReceiver(multicastSocket);

            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                try {
                    sender.sendMessage(new ByeMessage());
                    if (multicastGroupAddress instanceof java.net.Inet6Address) {
                        multicastSocket.leaveGroup(new InetSocketAddress(multicastGroupAddress, PORT), networkInterface);
                    } else {
                        multicastSocket.leaveGroup(multicastGroupAddress);
                    }
                    multicastSocket.close();
                } catch (Exception ignored) {}
            }));

            System.out.println("Отправка HiMessage...");
            sender.sendMessage(new HiMessage());
            final List<AppCopy> liveAppCopies = new LinkedList<>();
            while (true) {
                try {
                    final Message message = receiver.receiveMessage();
                    if (message != null) {
                        message.handle(liveAppCopies, sender, receiver);
                        System.out.println("Текущий список копий:");
                        MessageUtils.printAppCopies(liveAppCopies);
                    }
                } catch (Exception e) {
                    System.err.println("Ошибка: " + e.getMessage());
                }
            }
        } catch (Exception exception) {
            System.err.println("Ошибка: " + exception.getMessage());
            System.exit(ERROR);
        }
    }

    private static NetworkInterface getNetworkInterface(InetAddress multicastAddress, String scopeId) throws Exception {
        NetworkInterface fallback = null;
        Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
        while (interfaces.hasMoreElements()) {
            NetworkInterface ni = interfaces.nextElement();
            if (!ni.isUp() || !ni.supportsMulticast()) continue;
            Enumeration<InetAddress> addresses = ni.getInetAddresses();
            boolean supportsIPv6 = false;
            while (addresses.hasMoreElements()) {
                if (addresses.nextElement() instanceof java.net.Inet6Address) {
                    supportsIPv6 = true;
                }
            }
            if (multicastAddress instanceof java.net.Inet6Address) {
                if (!supportsIPv6 || (scopeId != null && !ni.getName().equals(scopeId))) continue;
                if (ni.getName().equals("lo0") || ni.getName().equals("en0")) return ni;
                if (fallback == null) fallback = ni;
            } else {
                addresses = ni.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    if (addresses.nextElement() instanceof java.net.Inet4Address) return ni;
                }
            }
        }
        return fallback;
    }
}
