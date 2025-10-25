package org.example.ProxyServer;

public class SOCKS_Constants {
    static final byte SOCKS_5 = 0x05;
    static final byte NO_AUTH_REQUIRED = 0x00;
    // static final byte USERNAME_PASSWORD = 0x02;
    static final byte IPV4 = 0x01;
    static final byte DOMAIN_NAME = 0x03;
    static final byte IPV6 = 0x04;
    static final byte RSV = 0x00;
    static final byte CONNECT = 0x01;
    // static final byte BIND = 0x02;
    static final byte SUCCESS = 0x00;
    static final byte SERVER_FAIL = 0x01;
    static final byte CONNECTION_NOT_ALLOWED = 0x02;
    // static final byte NETWORK_UNREACHABLE = 0x03;
    static final byte HOST_UNREACHABLE = 0x04;
    // static final byte CONNECTION_REFUSED = 0x05;
    // static final byte TTL_EXPIRED = 0x06;
    static final byte COMMAND_NOT_SUP = 0x07;
    static final byte ADDR_TYPE_NOT_SUP = 0x08;
    static final byte NO_ACCEPT_METHOD = (byte) 0xFF;
    static final int IPV4_LENGTH = 4;
    static final int IPV6_LENGTH = 16;
}
